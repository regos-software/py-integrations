from typing import Optional, List
from pydantic import BaseModel, RootModel

class ConnectedIntegrationSetting(BaseModel):
    key: Optional[str]= None
    value: Optional[str]= None
    last_update: Optional[int]= None

class ConnectedIntegrationSettingRequest(BaseModel):
    integration_key: Optional[str] = None
    firm_id: Optional[int] = None

class ConnectedIntegrationSettingEditItem(BaseModel):
    id: Optional[int]= None
    key: Optional[str]= None
    value: Optional[str]= None
    integration_key: Optional[str]= None
    firm_id: Optional[int]= None

class ConnectedIntegrationSettingEditRequest(RootModel[List[ConnectedIntegrationSettingEditItem]]):
    pass
