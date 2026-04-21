from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from app.core.database import Base
import uuid

class DeviceSession(Base):
    __tablename__ = "device_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id = Column(String, ForeignKey("players.id"), nullable=False)
    fingerprint = Column(String, nullable=False)
    ip_address = Column(String, nullable=False)
    country = Column(String(2), nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EntityLink(Base):
    __tablename__ = "entity_links"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    player_id_a = Column(String, ForeignKey("players.id"), nullable=False)
    player_id_b = Column(String, ForeignKey("players.id"), nullable=False)
    link_type = Column(String, nullable=False)  # ip, device, email, phone, payment_token
    link_value = Column(String, nullable=False)  # the shared attribute value
    strength = Column(Integer, default=1)  # number of shared attributes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
