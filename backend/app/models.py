from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, Integer, String, Text

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    item_type = Column(String(10), nullable=False)
    category = Column(String(30), nullable=False)
    probability = Column(Integer, nullable=False)
    impact = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    priority = Column(String(10), nullable=False)
    owner = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="Open")
    due_date = Column(Date, nullable=False)
    mitigation = Column(Text, default="")
    review_notes = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, index=True, nullable=False)
    action = Column(String(30), nullable=False)
    changed_by = Column(String(50), nullable=False)
    details = Column(Text, default="")
    timestamp = Column(DateTime, default=utcnow)