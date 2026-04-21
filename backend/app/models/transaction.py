from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id = Column(String, ForeignKey("players.id"), nullable=False)
    tx_type = Column(String, nullable=False)  # deposit, withdrawal
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="EUR")
    payment_method = Column(String, nullable=False)  # card, crypto, bank, ewallet
    payment_token = Column(String, nullable=True)  # hashed card/wallet id
    status = Column(String, default="pending")  # pending, approved, declined, flagged, hold, reversed
    risk_score = Column(Float, default=0.0)
    risk_label = Column(String, default="Low")
    ip_address = Column(String, nullable=True)
    country = Column(String(2), nullable=True)
    device_fingerprint = Column(String, nullable=True)
    fraud_type = Column(String, nullable=True)
    aml_flag = Column(Boolean, default=False)
    velocity_flag = Column(Boolean, default=False)
    geo_mismatch_flag = Column(Boolean, default=False)
    rule_hits = Column(Text, nullable=True)  # JSON list of rule codes
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
