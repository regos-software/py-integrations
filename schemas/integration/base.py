from pydantic import BaseModel, Field
from typing import Any, Dict

class IntegrationRequest(BaseModel):
    action: str = Field(..., description="Наименование вызываемого метода")
    connected_integration_id: str = Field(..., description="ID подключённой интеграции (токен)")
    data: Any = Field(..., description="Произвольный объект данных, передаваемый в метод")

class IntegrationSuccessResponse(BaseModel):
    ok: bool = Field(True, description="Признак успешного выполнения запроса")
    result: Any = Field(..., description="Результат выполнения метода")

class IntegrationErrorModel(BaseModel):
    error: int = Field(..., description="Код логической ошибки")
    description: Any = Field(..., description="Описание ошибки")

class IntegrationErrorResponse(BaseModel):
    ok: bool = Field(False, description="Признак логической ошибки (false)")
    result: IntegrationErrorModel = Field(..., description="Информация об ошибке")
