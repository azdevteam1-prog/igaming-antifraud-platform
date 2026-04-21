from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Text, JSON
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Rule(Base):
    __tablename__ = "rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)  # velocity, geo, device, behavior, aml
    condition_type = Column(String, nullable=False)  # threshold, match, ratio
    condition_params = Column(JSON, nullable=False)  # {field, operator, value, window_seconds}
    risk_points = Column(Integer, default=10)  # points added to risk score
    action = Column(String, default="review")  # none, review, hold, block, alert
    status = Column(String, default="draft")  # draft, live, archived
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    version = Column(Integer, default=1)
    created_by = Column(String, default="system")
    hit_count = Column(Integer, default=0)
    false_positive_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
