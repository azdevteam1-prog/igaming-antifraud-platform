from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id = Column(String, ForeignKey("players.id"), nullable=False)
    transaction_id = Column(String, ForeignKey("transactions.id"), nullable=True)
    alert_type = Column(String, nullable=False)
    severity = Column(String, default="Medium")  # Low, Medium, High, Critical
    status = Column(String, default="open")  # open, in_progress, resolved, escalated, false_positive
    rule_code = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    analyst_id = Column(String, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
