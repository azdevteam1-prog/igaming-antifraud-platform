"""
Player Session Model for iGaming Anti-Fraud Platform
Tracks login sessions with device fingerprint, IP geolocation,
and session metadata for fraud and multi-account detection.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, DateTime, Float,
    ForeignKey, Text, Integer, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class PlayerSession(Base):
    __tablename__ = "player_sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to player
    player_id = Column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session lifecycle
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Network / IP data
    ip_address = Column(String(45), nullable=True)  # supports IPv6
    country_code = Column(String(2), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    asn = Column(String(20), nullable=True)     # Autonomous System Number
    is_vpn = Column(Boolean, default=False)
    is_tor = Column(Boolean, default=False)
    is_proxy = Column(Boolean, default=False)
    is_datacenter = Column(Boolean, default=False)

    # Device fingerprint
    device_id = Column(
        UUID(as_uuid=True),
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_agent = Column(Text, nullable=True)
    browser = Column(String(100), nullable=True)
    os = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile / desktop / tablet
    screen_resolution = Column(String(20), nullable=True)
    timezone = Column(String(60), nullable=True)
    language = Column(String(20), nullable=True)
    canvas_hash = Column(String(64), nullable=True)   # Canvas fingerprint
    webgl_hash = Column(String(64), nullable=True)    # WebGL fingerprint

    # Risk signals computed at session start
    geo_risk_score = Column(Float, default=0.0)
    ip_risk_score = Column(Float, default=0.0)
    impossible_travel = Column(Boolean, default=False)
    travel_distance_km = Column(Float, nullable=True)

    # Session activity counters
    transaction_count = Column(Integer, default=0)
    failed_login_count = Column(Integer, default=0)
    page_views = Column(Integer, default=0)

    # Audit timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player = relationship("Player", back_populates="sessions", lazy="selectin")
    device = relationship("Device", lazy="selectin")

    # Indexes for common query patterns
    __table_args__ = (
        Index("ix_player_sessions_player_started", "player_id", "started_at"),
        Index("ix_player_sessions_ip", "ip_address"),
        Index("ix_player_sessions_country", "country_code"),
        Index("ix_player_sessions_active", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"<PlayerSession id={self.id} player={self.player_id} "
            f"ip={self.ip_address} active={self.is_active}>"
        )

    @property
    def duration_seconds(self) -> float | None:
        """Return session duration in seconds, or None if still active."""
        if self.ended_at and self.started_at:
            return (self.ended_at - self.started_at).total_seconds()
        return None

    @property
    def is_anonymous(self) -> bool:
        """True if the session uses any anonymisation technology."""
        return self.is_vpn or self.is_tor or self.is_proxy or self.is_datacenter
