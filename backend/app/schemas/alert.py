from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AlertOut(BaseModel):
    id: str
    player_id: str
    transaction_id: Optional[str]
    alert_type: str
    severity: str
    status: str
    rule_code: Optional[str]
    description: Optional[str]
    analyst_id: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class AlertUpdate(BaseModel):
    status: Optional[str] = None
    analyst_id: Optional[str] = None
    resolution_notes: Optional[str] = None
