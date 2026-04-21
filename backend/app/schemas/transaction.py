from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TransactionOut(BaseModel):
    id: str
    player_id: str
    tx_type: str
    amount: float
    currency: str
    payment_method: str
    status: str
    risk_score: float
    risk_label: str
    ip_address: Optional[str]
    country: Optional[str]
    geo_mismatch_flag: bool
    aml_flag: bool
    velocity_flag: bool
    rule_hits: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
