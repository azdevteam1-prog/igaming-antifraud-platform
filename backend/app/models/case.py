import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Enum as SAEnum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class CaseStatus(str, enum.Enum):
    open = "open"
    investigating = "investigating"
    escalated = "escalated"
    resolved = "resolved"
    closed = "closed"
    false_positive = "false_positive"


class CasePriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class CaseType(str, enum.Enum):
    fraud = "fraud"
    money_laundering = "money_laundering"
    account_takeover = "account_takeover"
    multi_accounting = "multi_accounting"
    bonus_abuse = "bonus_abuse"
    payment_fraud = "payment_fraud"
    identity_theft = "identity_theft"
    other = "other"


class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_number = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    case_type = Column(SAEnum(CaseType), nullable=False)
    status = Column(SAEnum(CaseStatus), default=CaseStatus.open, nullable=False)
    priority = Column(SAEnum(CasePriority), default=CasePriority.medium, nullable=False)
    player_id = Column(String(100), nullable=True, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    evidence = Column(JSON, default=list)
    tags = Column(JSON, default=list)
    risk_score = Column(String(10), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignee = relationship("User", foreign_keys=[assigned_to], backref="assigned_cases")
    creator = relationship("User", foreign_keys=[created_by], backref="created_cases")
    comments = relationship("CaseComment", back_populates="case", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Case {self.case_number} [{self.status}]>"


class CaseComment(Base):
    __tablename__ = "case_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(String(5), default="true")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    case = relationship("Case", back_populates="comments")
    author = relationship("User", backref="case_comments")
