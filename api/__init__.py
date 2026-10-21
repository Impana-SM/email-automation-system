"""API package for REST routes, schemas, and dependencies."""

from api.schemas import (
    EmailSendRequest,
    EmailSendResponse,
    TemplateCreate,
    TemplateResponse,
    ReminderCreate,
    ReminderResponse,
)

__all__ = [
    "EmailSendRequest",
    "EmailSendResponse",
    "TemplateCreate",
    "TemplateResponse",
    "ReminderCreate",
    "ReminderResponse",
]
