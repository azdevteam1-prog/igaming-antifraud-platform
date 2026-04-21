from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, Text
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Player(Base):
    __tablename__ = "players"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone = Column(String, nullable=True)
    country = Column(String(2), nullable=False)
    currency = Column(String(3), default="EUR")
    status = Column(String, default="active")  # active, suspended, banned, review
    kyc_verified = Column(Boolean, default=False)
    kyc_level = Column(Integer, default=0)  # 0=none, 1=basic, 2=enhanced
    risk_score = Column(Float, default=0.0)
    risk_label = Column(String, default="Low")  # Low, Medium, High, Critical
    pep_flag = Column(Boolean, default=False)
    sanctions_flag = Column(Boolean, default=False)
    bonus_abuse_flag = Column(Boolean, default=False)
    multi_account_flag = Column(Boolean, default=False)
    total_deposits = Column(Float, default=0.0)
    total_withdrawals = Column(Float, default=0.0)
    chargebacks = Column(Integer, default=0)
    registration_ip = Column(String, nullable=True)
    last_ip = Column(String, nullable=True)
    device_fingerprint = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
