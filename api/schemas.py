"""Pydantic schemas for request validation, responses, and webhook payloads."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field


# --- Direct Email Sending Schemas ---
class EmailSendRequest(BaseModel):
    to_email: EmailStr
    subject: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = None
    is_html: bool = True
    template_id: Optional[int] = None
    context_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class EmailSendResponse(BaseModel):
    success: bool
    message: str
    log_id: Optional[int] = None


# --- Template Schemas ---
class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    subject_template: str = Field(..., min_length=1, max_length=255)
    body_template: str = Field(..., min_length=1)


class TemplateUpdate(BaseModel):
    description: Optional[str] = Field(None, max_length=255)
    subject_template: Optional[str] = Field(None, max_length=255)
    body_template: Optional[str] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    subject_template: str
    body_template: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Reminder Schemas ---
class ReminderCreate(BaseModel):
    recipient: EmailStr
    scheduled_time: datetime
    template_id: Optional[int] = None
    context_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    subject: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = None


class ReminderResponse(BaseModel):
    id: int
    recipient: str
    template_id: Optional[int] = None
    subject: Optional[str] = None
    scheduled_time: datetime
    status: str
    job_id: Optional[str] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Email Log Schemas ---
class EmailLogResponse(BaseModel):
    id: int
    reminder_id: Optional[int] = None
    recipient: str
    subject: str
    status: str
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Webhook Schemas ---
class WebhookPayload(BaseModel):
    provider: str = "generic"
    event_type: str = Field(..., description="delivered, opened, clicked, bounced, or spam")
    recipient: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class WebhookResponse(BaseModel):
    success: bool
    message: str
    event_id: Optional[int] = None


# --- Dashboard Stats Schema ---
class DashboardStats(BaseModel):
    total_sent: int
    total_failed: int
    pending_reminders: int
    active_templates: int
    recent_logs: List[EmailLogResponse] = []
