import asyncio
import json
import re
from typing import Any, Dict, List, Optional, Sequence
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
    Формат входа идентичен другим интеграциям:
    async def send_messages(self, messages: List[Dict]) -> Dict

    Каждый message:
    {
        "campaign_recipient_id": <int|null>,
        "sms_id": <int|null>,
        "recipient": "<email>",
        "message": "<text>"
    }

    Возвращаем как в примере Telegram:
    {
        "sent_batches": <int>,
        "details": [ <result per batch>, ... ]
    }
    """

    INTEGRATION_KEY = "email_sender"

    # Таймауты короче, чтобы не зависать и укладываться в SLA
    CONNECT_TIMEOUT = 5
    COMMAND_TIMEOUT = 5

    # Производительность: параллельные SMTP-сессии на батч
    DEFAULT_POOL_SIZE = 10
    MAX_POOL_SIZE = 20

    # Управление размером батча 
    BATCH_SIZE = 250
    BATCH_JOIN_TIMEOUT = 15  # сек


    SETTINGS_TTL = settings.redis_cache_ttl
    SETTINGS_KEYS = {
        "host": "smtp_host",
        "port": "smtp_port",
        "email": "smtp_email",
        "password": "smtp_password",
        "user": "smtp_user",
        "default_subject": "smtp_default_subject",
        "use_ssl": "smtp_use_ssl",
        "pool_size": "smtp_pool_size",  # опционно
    }

    EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    # -------------------- helpers --------------------

    def _create_error_response(self, code: int, description: str) -> IntegrationErrorResponse:
        return IntegrationErrorResponse(result=IntegrationErrorModel(error=code, description=description))

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}

    async def _fetch_settings(self, cache_key: str) -> dict:
        # 1) Redis
        if settings.redis_enabled and redis_client:
            try:
                cached = await redis_client.get(cache_key)
                if cached:
                    if isinstance(cached, (bytes, bytearray)):
                        cached = cached.decode("utf-8")
                    logger.debug(f"Настройки получены из Redis: {cache_key}")
                    return json.loads(cached)
            except Exception as err:
                logger.warning(f"Ошибка Redis: {err}, загружаем из API")

        # 2) API
        async with RegosAPI(connected_integration_id=self.connected_integration_id) as api:
            settings_response = await api.integrations.connected_integration_setting.get(
                ConnectedIntegrationSettingRequest(integration_key=self.INTEGRATION_KEY)
            )

        settings_map = {item.key.lower(): item.value for item in settings_response}

        # 3) Cache
        if settings.redis_enabled and redis_client:
            try:
                await redis_client.setex(cache_key, self.SETTINGS_TTL, json.dumps(settings_map))
            except Exception as err:
                logger.warning(f"Не удалось сохранить настройки в Redis: {err}")

        return settings_map

    def _is_valid_email(self, addr: str) -> bool:
        return bool(self.EMAIL_RE.match(addr or ""))

    def _build_email_message(self, from_addr: str, to_addr: str, subject: str, body: str, is_html: bool = False) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject or ""
        if is_html:
            msg.add_alternative(body or "", subtype="html")
        else:
            msg.set_content(body or "")
        return msg

    async def _open_smtp(self, host: str, port: int, user: str, password: str, use_ssl: bool) -> aiosmtplib.SMTP:
        smtp = aiosmtplib.SMTP(hostname=host, port=port, timeout=self.COMMAND_TIMEOUT, use_tls=use_ssl)
        await asyncio.wait_for(smtp.connect(), timeout=self.CONNECT_TIMEOUT)
        if not use_ssl:
            try:
                await asyncio.wait_for(smtp.starttls(), timeout=self.COMMAND_TIMEOUT)
            except aiosmtplib.errors.SMTPException as tls_err:
                logger.warning(f"STARTTLS недоступен/ошибка: {tls_err}")
        await asyncio.wait_for(smtp.login(user, password), timeout=self.COMMAND_TIMEOUT)
        return smtp

    # -------------------- public API --------------------

    async def handle_external(self, data: dict) -> Any:
        logger.info(f"handle_external вызван с данными: {data}")
        return IntegrationSuccessResponse(result={"status": "ok"})

    async def send_messages(self, messages: List[Dict]) -> Dict:
        """Отправка email-сообщений батчами (контракт как в других интеграциях)."""
        logger.info(f"Starting message send for ID {self.connected_integration_id}")

        # Небольшая совместимость: если вдруг пришло {"messages": [...]}
        if isinstance(messages, dict) and "messages" in messages:
            messages = messages["messages"]

        if not self.connected_integration_id:
            return self._create_error_response(1000, "No connected_integration_id specified")

        # Validate messages
        for message in messages:
            if "message" not in message or not message["message"]:
                return self._create_error_response(1009, f"Message missing text: {message}")
            if "recipient" not in message or not message["recipient"]:
                return self._create_error_response(1010, f"Message missing recipient: {message}")
            if not self._is_valid_email(str(message["recipient"]).strip()):
                return self._create_error_response(1011, f"Invalid recipient email: {message['recipient']}")

        # Fetch SMTP settings
        cache_key = f"clients:settings:{self.INTEGRATION_KEY}:{self.connected_integration_id}"
        try:
            settings_map = await self._fetch_settings(cache_key)
            host = settings_map.get(self.SETTINGS_KEYS["host"])
            port_raw = settings_map.get(self.SETTINGS_KEYS["port"])
            from_email = settings_map.get(self.SETTINGS_KEYS["email"])
            password = settings_map.get(self.SETTINGS_KEYS["password"])
            use_ssl = self._to_bool(settings_map.get(self.SETTINGS_KEYS["use_ssl"]))
            smtp_user = settings_map.get(self.SETTINGS_KEYS["user"]) or from_email
            default_subject = settings_map.get(self.SETTINGS_KEYS["default_subject"]) or "Уведомление"

            pool_size_raw = settings_map.get(self.SETTINGS_KEYS["pool_size"])
            try:
                pool_size = int(pool_size_raw) if pool_size_raw else self.DEFAULT_POOL_SIZE
            except Exception:
                pool_size = self.DEFAULT_POOL_SIZE
            pool_size = max(1, min(self.MAX_POOL_SIZE, pool_size))

            if not all([host, port_raw, from_email, password]):
                return self._create_error_response(1002, "Missing SMTP settings (host/port/email/password)")
            try:
                port = int(str(port_raw).strip())
            except Exception:
                return self._create_error_response(1003, f"Invalid SMTP port: {port_raw}")

        except Exception as error:
            return self._create_error_response(1001, f"Settings retrieval error: {error}")

        # ---------- отправка батчами (как в примере), внутри батча — параллельные воркеры ----------
        results: List[Dict] = []

        # внутри send_messages -> функция send_batch(batch, batch_index):
        async def send_batch(batch: Sequence[Dict], batch_index: int) -> Dict:
            queue: asyncio.Queue[Dict] = asyncio.Queue()
            for item in batch:
                await queue.put(item)

            local_pool = min(pool_size, max(1, queue.qsize()))
            batch_results: List[Dict] = []

            async def drain_queue_with_error(err_msg: str, worker_label: str = "init") -> int:
                drained = 0
                while True:
                    try:
                        item = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                    batch_results.append({
                        "campaign_recipient_id": item.get("campaign_recipient_id"),
                        "sms_id": item.get("sms_id"),
                        "recipient": item.get("recipient"),
                        "error": err_msg,
                        "worker": worker_label,
                    })
                    queue.task_done()
                    drained += 1
                return drained

            async def worker(wid: int):
                smtp: Optional[aiosmtplib.SMTP] = None
                try:
                    logger.debug(f"[batch {batch_index} w{wid}] opening SMTP {host}:{port} ssl={use_ssl}")
                    # если connect/login упадут — перехватываем ниже
                    smtp = await self._open_smtp(host, port, smtp_user, password, use_ssl)
                    logger.debug(f"[batch {batch_index} w{wid}] SMTP opened")
                    while True:
                        try:
                            item = await asyncio.wait_for(queue.get(), timeout=1.0)
                        except asyncio.TimeoutError:
                            break

                        recipient = str(item["recipient"]).strip()
                        body = item.get("message") or ""
                        raw_subject = item.get("subject")
                        subject = (raw_subject or (body[:70] + "…" if len(body) > 70 else body) or default_subject)

                        email_msg = self._build_email_message(
                            from_addr=from_email, to_addr=recipient, subject=subject, body=body, is_html=False,
                        )

                        try:
                            send_result = await asyncio.wait_for(smtp.send_message(email_msg), timeout=self.COMMAND_TIMEOUT)
                            batch_results.append({
                                "campaign_recipient_id": item.get("campaign_recipient_id"),
                                "sms_id": item.get("sms_id"),
                                "recipient": recipient,
                                "status": "sent",
                                "response": str(send_result),
                                "worker": wid,
                            })
                        except Exception as send_err:
                            logger.error(f"[batch {batch_index} w{wid}] send error to {recipient}: {send_err}")
                            batch_results.append({
                                "campaign_recipient_id": item.get("campaign_recipient_id"),
                                "sms_id": item.get("sms_id"),
                                "recipient": recipient,
                                "error": str(send_err),
                                "worker": wid,
                            })
                        finally:
                            queue.task_done()

                except Exception as open_err:
                    # Критично: воркер не открыл SMTP — дренируем очередь, иначе queue.join() зависнет
                    logger.error(f"[batch {batch_index} w{wid}] SMTP open failed: {open_err}")
                    await drain_queue_with_error(f"SMTP open failed: {open_err}", worker_label=f"w{wid}")
                finally:
                    if smtp:
                        try:
                            await asyncio.wait_for(smtp.quit(), timeout=2)
                        except Exception:
                            pass

            tasks = [asyncio.create_task(worker(i + 1)) for i in range(local_pool)]

            # ждём завершение очереди, но с таймаутом
            try:
                await asyncio.wait_for(queue.join(), timeout=self.BATCH_JOIN_TIMEOUT)
            except asyncio.TimeoutError:
                logger.error(f"[batch {batch_index}] queue.join() timeout after {self.BATCH_JOIN_TIMEOUT}s, cancelling workers")
                for t in tasks:
                    t.cancel()
                # дренируем остатки очереди, чтобы не потерять письма
                await drain_queue_with_error("Batch join timeout; cancelled workers", worker_label="timeout")

            # дожимаем воркеров (не упадём, даже если кто-то уже отменён)
            await asyncio.gather(*tasks, return_exceptions=True)

            sent = sum(1 for r in batch_results if r.get("status") == "sent")
            return {
                "batch_index": batch_index,
                "sent": sent,
                "total": len(batch),
                "pool_used": local_pool,
                "items": batch_results,
            }

