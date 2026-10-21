"""Core business logic package for Email Automation."""

from src.models import Contact, EmailTemplate, ScheduledReminder, EmailLog, WebhookEvent
from src.mailer import Mailer, EmailService
from src.template_service import TemplateService
from src.scheduler import ReminderScheduler

__all__ = [
    "Contact",
    "EmailTemplate",
    "ScheduledReminder",
    "EmailLog",
    "WebhookEvent",
    "Mailer",
    "EmailService",
    "TemplateService",
    "ReminderScheduler",
]
