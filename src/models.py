"""SQLAlchemy ORM models for templates, scheduled reminders, logs, and webhook events."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base


class Contact(Base):
    """Registered contact/recipient model."""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class EmailTemplate(Base):
    """Stores reusable dynamic Jinja2 email templates."""
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    subject_template = Column(String(255), nullable=False)
    body_template = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    reminders = relationship("ScheduledReminder", back_populates="template", cascade="all, delete-orphan")


class ScheduledReminder(Base):
    """Stores pending, processing, and executed email reminder jobs."""
    __tablename__ = "scheduled_reminders"

    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String(255), index=True, nullable=False)
    template_id = Column(Integer, ForeignKey("email_templates.id", ondelete="SET NULL"), nullable=True)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    context_data = Column(Text, nullable=True)  # JSON-encoded dictionary
    scheduled_time = Column(DateTime, index=True, nullable=False)
    status = Column(String(50), default="SCHEDULED", index=True, nullable=False)  # SCHEDULED, PROCESSING, SENT, FAILED, CANCELLED
    job_id = Column(String(100), unique=True, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    template = relationship("EmailTemplate", back_populates="reminders")
    logs = relationship("EmailLog", back_populates="reminder")


class EmailLog(Base):
    """Audit log recording every dispatched email attempt and its outcome."""
    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("scheduled_reminders.id", ondelete="SET NULL"), nullable=True)
    recipient = Column(String(255), index=True, nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(50), default="PENDING", index=True, nullable=False)  # SENT, FAILED, PENDING
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    reminder = relationship("ScheduledReminder", back_populates="logs")


class WebhookEvent(Base):
    """Tracks inbound delivery and interaction webhooks (opens, clicks, bounces)."""
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), default="generic", nullable=False)
    event_type = Column(String(50), index=True, nullable=False)  # delivered, opened, clicked, bounced, spam
    recipient = Column(String(255), index=True, nullable=True)
    payload = Column(Text, nullable=False)  # Raw JSON payload
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
