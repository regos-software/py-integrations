import asyncio
import json
import os
import re
from typing import Any, Optional
from email.message import EmailMessage

import aiosmtplib

from core.api.regos_api import RegosAPI
from schemas.api.integrations.connected_integration_setting import ConnectedIntegrationSettingRequest

from schemas.integration.base import (
    IntegrationSuccessResponse,
    IntegrationErrorResponse,
    IntegrationErrorModel,
)
from schemas.integration.email_integration_base import IntegrationEmailBase
from clients.base import ClientBase

from core.logger import setup_logger
from config.settings import settings
from core.redis import redis_client

logger = setup_logger("email_sender")


class EmailSenderIntegration(IntegrationEmailBase, ClientBase):
    """
    Интеграция отправки EMAIL через SMTP.

    ЕДИНЫЙ входной формат:
    messages = [
        {
            "campaign_recipient_id": 88,    # опционально
            "sms_id": null,                 # опционально
            "recipient": "user@example.com",
            "message": "Текст письма"
        },
        ...
    ]
    """

    INTEGRATION_KEY = "email_sender"
    CONNECT_TIMEOUT = 5
    COMMAND_TIMEOUT = 5
    SETTINGS_TTL = settings.redis_cache_ttl

    # Пул параллельных SMTP-соединений (можно переопределить через настройку)
    DEFAULT_POOL_SIZE = 10
    MAX_POOL_SIZE = 20

    # Ожидаемые ключи в ConnectedIntegrationSetting (кейсы не важны)
    # Вы перечислили: SMTP_HOST, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD,
    # SMTP_USER, SMTP_DEFAULT_SUBJECT, SMTP_USE_SSL
    SETTINGS_KEYS = {
        "host": "smtp_host",
        "port": "smtp_port",
        "email": "smtp_email",
        "password": "smtp_password",
        "user": "smtp_user",  # если логин отличается от email
        "default_subject": "smtp_default_subject",
        "use_ssl": "smtp_use_ssl",
        # необязательное: размер пула
        "pool_size": "smtp_pool_size",
    }

    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False

    # ----------------------- служебные -----------------------

    def _error_response(self, code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(
            result=IntegrationErrorModel(error=code, description=description)
        )

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}

    async def _get_settings(self, cache_key: str) -> dict:
        """Настройки SMTP из Redis или API."""
        # 1) Redis
        if settings.redis_enabled and redis_client:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Настройки получены из Redis: {cache_key}")
                    if isinstance(cached, (bytes, bytearray)):
                        cached = cached.decode("utf-8")
                    return json.loads(cached)
            except Exception as err:
                logger.warning(f"Ошибка Redis: {err}, загружаем из API")

        # 2) API
        logger.debug("Настройки не найдены в кеше, загружаем из API")
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            settings_response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(integration_key=self.INTEGRATION_KEY)
            )

        settings_map = {item.key.lower(): item.value for item in settings_response}

        # 3) Кешируем
        if settings.redis_enabled and redis_client:
            try:
                await redis_client.setex(cache_key, self.SETTINGS_TTL, json.dumps(settings_map))
            except Exception as err:
                logger.warning(f"Не удалось сохранить настройки в Redis: {err}")

        return settings_map

    def _is_valid_email(self, addr: str) -> bool:
        return bool(self.EMAIL_RE.match(addr or ""))

    def _build_email_message(
        self, from_addr: str, to_addr: str, subject: str, body: str, is_html: bool = False
    ) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject or ""
        if is_html:
            msg.add_alternative(body or "", subtype="html")
        else:
            msg.set_content(body or "")
        return msg

    async def _open_smtp(
        self, host: str, port: int, user: str, password: str, use_ssl: bool
    ) -> aiosmtplib.SMTP:
        smtp = aiosmtplib.SMTP(
            hostname=host,
            port=port,
            timeout=self.COMMAND_TIMEOUT,
            source_address=None,
            use_tls=use_ssl,  # SMTPS при True
        )
        await smtp.connect(timeout=self.CONNECT_TIMEOUT)
        # При не-SSL поднимаем TLS, если доступно
        if not use_ssl:
            try:
                await smtp.starttls()
            except aiosmtplib.errors.SMTPException as tls_err:
                logger.warning(f"STARTTLS недоступен или не удался: {tls_err}")
        await smtp.login(user, password)
        return smtp

    # ----------------------- публичные -----------------------

    async def handle_external(self, data: dict) -> Any:
        logger.info(f"handle_external вызван с данными: {data}")
        return IntegrationSuccessResponse(result={"status": "ok"})

    async def send_messages(self, messages: list[dict]) -> Any:
        """
        Единый формат (как в SMS), но recipient — это EMAIL.
        Требования по скорости покрываем пулом параллельных SMTP-соединений.
        """
        logger.info("Начата отправка email через EmailSenderIntegration (пул соединений)")

        if not self.connected_integration_id:
            return self._error_response(1000, "connected_integration_id не указан")

        cache_key = f"clients:settings:{self.INTEGRATION_KEY}:{self.connected_integration_id}"

        # --- настройки SMTP ---
        try:
            settings_map = await self._get_settings(cache_key)
            host = settings_map.get(self.SETTINGS_KEYS["host"])
            port_raw = settings_map.get(self.SETTINGS_KEYS["port"])
            from_email = settings_map.get(self.SETTINGS_KEYS["email"])
            password = settings_map.get(self.SETTINGS_KEYS["password"])
            use_ssl = self._to_bool(settings_map.get(self.SETTINGS_KEYS["use_ssl"]))
            smtp_user = settings_map.get(self.SETTINGS_KEYS["user"]) or from_email
            default_subject = settings_map.get(self.SETTINGS_KEYS["default_subject"]) or "Уведомление"

            # Размер пула: из настроек или дефолт
            pool_size_raw = settings_map.get(self.SETTINGS_KEYS["pool_size"])
            try:
                pool_size = int(pool_size_raw) if pool_size_raw else self.DEFAULT_POOL_SIZE
            except Exception:
                pool_size = self.DEFAULT_POOL_SIZE
            pool_size = max(1, min(self.MAX_POOL_SIZE, pool_size))
            pool_size = min(pool_size, max(1, len(messages)))  # не больше числа писем

            if not all([host, port_raw, from_email, password]):
                return self._error_response(
                    1002,
                    "Настройки интеграции не содержат один из обязательных параметров: "
                    "SMTP_HOST, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD",
                )

            try:
                port = int(str(port_raw).strip())
            except Exception:
                return self._error_response(1003, f"Некорректный порт SMTP: {port_raw}")

        except Exception as e:
            return self._error_response(1001, f"Ошибка при получении настроек: {e}")

        # --- предвалидация и подготовка очереди ---
        queue: asyncio.Queue[dict] = asyncio.Queue()
        invalid_results: list[dict] = []
        for item in messages:
            recipient = (item.get("recipient") or "").strip()
            if not self._is_valid_email(recipient):
                invalid_results.append({
                    "campaign_recipient_id": item.get("campaign_recipient_id"),
                    "sms_id": item.get("sms_id"),
                    "recipient": recipient,
                    "error": "Некорректный email в поле recipient",
                })
                continue
            await queue.put(item)

        # Если все письма неверные — возвращаем сразу
        if queue.empty():
            return {
                "sent_messages": 0,
                "total_messages": len(messages),
                "details": invalid_results,
            }

        # --- воркер отправки через своё SMTP-соединение ---
        async def worker(worker_id: int, results: list[dict]):
            smtp: Optional[aiosmtplib.SMTP] = None
            try:
                smtp = await self._open_smtp(host, port, smtp_user, password, use_ssl)
                while True:
                    try:
                        item = await asyncio.wait_for(queue.get(), timeout=1.0)
                    except asyncio.TimeoutError:
                        # очередь пуста для этого воркера
                        break

                    recipient = (item.get("recipient") or "").strip()
                    body = item.get("message") or ""
                    raw_subject = item.get("subject")
                    # генерируем тему при отсутствии:
                    subject = (raw_subject or (body[:70] + "…" if len(body) > 70 else body) or default_subject)

                    email_msg = self._build_email_message(
                        from_addr=from_email,
                        to_addr=recipient,
                        subject=subject,
                        body=body,
                        is_html=False,  # при необходимости переключите
                    )

                    try:
                        send_result = await smtp.send_message(email_msg)
                        results.append({
                            "campaign_recipient_id": item.get("campaign_recipient_id"),
                            "sms_id": item.get("sms_id"),
                            "recipient": recipient,
                            "status": "sent",
                            "response": str(send_result),
                            "worker": worker_id,
                        })
                    except Exception as send_err:
                        logger.error(f"[worker {worker_id}] Ошибка отправки на {recipient}: {send_err}")
                        results.append({
                            "campaign_recipient_id": item.get("campaign_recipient_id"),
                            "sms_id": item.get("sms_id"),
                            "recipient": recipient,
                            "error": str(send_err),
                            "worker": worker_id,
                        })
                    finally:
                        queue.task_done()
            finally:
                if smtp:
                    try:
                        await smtp.quit()
                    except Exception as quit_err:
                        logger.warning(f"[worker {worker_id}] Ошибка при закрытии SMTP-сессии: {quit_err}")

        # --- запускаем пул воркеров ---
        results: list[dict] = []
        worker_tasks = [asyncio.create_task(worker(i + 1, results)) for i in range(pool_size)]

        # дожидаемся обработки очереди и завершения воркеров
        await queue.join()
        for t in worker_tasks:
            # если воркер ушёл в ожидание пустой очереди — он завершится сам по таймауту
            try:
                await t
            except Exception as e:
                logger.error(f"Воркер упал: {e}")

        # добавляем ошибки валидации
        results.extend(invalid_results)

        sent_total = sum(1 for r in results if r.get("status") == "sent")
        logger.info(f"Email-рассылка завершена. Отправлено: {sent_total} / {len(messages)} "
                    f"(пул={pool_size})")

        return {
            "sent_messages": sent_total,
            "total_messages": len(messages),
            "details": results,
        }
