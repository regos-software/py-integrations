"""REGOS API schemas."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from datetime import datetime as _DateTime
from decimal import Decimal as _Decimal
from enum import IntEnum
from typing import Any, TypeAlias

from pydantic import ConfigDict, Field as PydField, RootModel

from schemas.api.common.base import RegosModel


class Language(RegosModel):
    "Модель, описывающая существующие языки в системе"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    id: int | None = PydField(default=None, description="Id языка")
    code: str | None = PydField(default=None, description="Код языка по стандарту ISO 639-3")
    code2: str | None = PydField(default=None)
    name: str | None = PydField(default=None, description="Наименование языка")
    short_name: str | None = PydField(default=None)
    version: str | None = PydField(default=None, description="Версия языка")
    last_update: int | None = PydField(default=None, description="Дата последнего изменения записи в формате unix time в секундах")


class LanguageRegosArrayResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleArrayResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: list[Language] | Error | None = PydField(default=None, description="Массив результата.")


class LanguageTranslationData(RegosModel):
    "Модель языкового пакета"
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    code: str | None = PydField(default=None)
    version: int | None = PydField(default=None)
    data: list[TranslationShort] | None = PydField(default=None)


class LanguageTranslationDataRegosObjectResult(RegosModel):
    "OpenAPI-only typed equivalent of SingleObjectResult."
    model_config = ConfigDict(extra="ignore", populate_by_name=True)
    ok: bool | None = PydField(default=None, description="Признак успешности выполнения запроса.")
    result: LanguageTranslationData | Error | None = PydField(default=None, description="Объект результата.")


# Imports are intentionally placed after model definitions to avoid circular imports.
from schemas.api.common.base import Error
from schemas.api.rbac.translation import TranslationShort


LanguageGetResponse: TypeAlias = LanguageRegosArrayResult


_MODEL_NAMES = ['Language', 'LanguageRegosArrayResult', 'LanguageTranslationData', 'LanguageTranslationDataRegosObjectResult']


__all__ = [
    'Language',
    'LanguageRegosArrayResult',
    'LanguageTranslationData',
    'LanguageTranslationDataRegosObjectResult',
    'LanguageGetResponse'
]
