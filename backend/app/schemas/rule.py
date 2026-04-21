from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class RuleOut(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str]
    category: str
    condition_type: str
    condition_params: Any
    risk_points: int
    action: str
    status: str
    priority: int
    version: int
    hit_count: int
    false_positive_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class RuleCreate(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    category: str
    condition_type: str
    condition_params: Any
    risk_points: int = 10
    action: str = "review"
    status: str = "draft"
    priority: int = 5

class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    condition_params: Optional[Any] = None
    risk_points: Optional[int] = None
    action: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
