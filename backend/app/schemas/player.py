from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PlayerOut(BaseModel):
    id: str
    username: str
    email: str
    country: str
    status: str
    kyc_verified: bool
    risk_score: float
    risk_label: str
    pep_flag: bool
    sanctions_flag: bool
    bonus_abuse_flag: bool
    multi_account_flag: bool
    total_deposits: float
    total_withdrawals: float
    chargebacks: int
    last_ip: Optional[str]
    device_fingerprint: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class PlayerUpdate(BaseModel):
    status: Optional[str] = None
    kyc_verified: Optional[bool] = None
    risk_label: Optional[str] = None
    bonus_abuse_flag: Optional[bool] = None
    multi_account_flag: Optional[bool] = None
