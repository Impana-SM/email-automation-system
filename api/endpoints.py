"""REST API endpoints for sending emails, managing templates, and scheduling reminders."""

import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_db_session, get_mailer, get_template_service
from api.schemas import (
    EmailSendRequest,
    EmailSendResponse,
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    ReminderCreate,
    ReminderResponse,
    EmailLogResponse,
    DashboardStats,
)
from src.models import EmailTemplate, ScheduledReminder, EmailLog
from src.mailer import Mailer
from src.template_service import TemplateService

router = APIRouter(prefix="/api/v1", tags=["Email Operations"])


# =====================================================================
# 1. Direct Email Dispatch
# =====================================================================
@router.post("/emails/send", response_model=EmailSendResponse, status_code=status.HTTP_200_OK)
async def send_email_endpoint(
    payload: EmailSendRequest,
    db: Session = Depends(get_db_session),
    mailer: Mailer = Depends(get_mailer),
    template_service: TemplateService = Depends(get_template_service),
):
    """Dispatches an email immediately (supports raw text or template rendering)."""
    subject = payload.subject or "Notification"
    body = payload.body or ""

    # If template_id provided, render dynamic template
    if payload.template_id:
        tmpl = db.query(EmailTemplate).filter(EmailTemplate.id == payload.template_id).first()
        if not tmpl:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        try:
            subject, body = template_service.render(
                tmpl.subject_template,
                tmpl.body_template,
                payload.context_data or {},
            )
        except Exception as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    if not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email body cannot be empty")

    log_entry = EmailLog(
        recipient=payload.to_email,
        subject=subject,
        body=body,
        status="PENDING",
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    success, error = await mailer.send_email(
        to_email=payload.to_email,
        subject=subject,
        body=body,
        is_html=payload.is_html,
    )

    log_entry.status = "SENT" if success else "FAILED"
    log_entry.error_message = error
    log_entry.sent_at = datetime.utcnow() if success else None
    db.commit()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email dispatch failed: {error}",
        )

    return EmailSendResponse(
        success=True,
        message="Email successfully dispatched.",
        log_id=log_entry.id,
    )


# =====================================================================
# 2. Template Management
# =====================================================================
@router.post("/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreate,
    db: Session = Depends(get_db_session),
    template_service: TemplateService = Depends(get_template_service),
):
    """Registers a new Jinja2 email template with validation."""
    is_valid, msg = template_service.validate_template_syntax(payload.body_template)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid template syntax: {msg}")

    existing = db.query(EmailTemplate).filter(EmailTemplate.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Template name already exists")

    template = EmailTemplate(
        name=payload.name,
        description=payload.description,
        subject_template=payload.subject_template,
        body_template=payload.body_template,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


@router.get("/templates", response_model=List[TemplateResponse])
def list_templates(db: Session = Depends(get_db_session)):
    """Retrieves all registered email templates."""
    return db.query(EmailTemplate).order_by(EmailTemplate.created_at.desc()).all()


@router.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template(template_id: int, db: Session = Depends(get_db_session)):
    """Fetches a specific template by ID."""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int, db: Session = Depends(get_db_session)):
    """Deletes an existing email template."""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    db.delete(template)
    db.commit()
    return None


# =====================================================================
# 3. Scheduled Reminders
# =====================================================================
@router.post("/reminders", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def schedule_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db_session),
):
    """Schedules a new reminder for automated dispatch."""
    if payload.template_id:
        template = db.query(EmailTemplate).filter(EmailTemplate.id == payload.template_id).first()
        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced template not found")

    job_id = f"reminder_{int(datetime.utcnow().timestamp())}_{payload.recipient[:6]}"
    reminder = ScheduledReminder(
        recipient=payload.recipient,
        template_id=payload.template_id,
        subject=payload.subject,
        body=payload.body,
        context_data=json.dumps(payload.context_data or {}),
        scheduled_time=payload.scheduled_time,
        status="SCHEDULED",
        job_id=job_id,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/reminders", response_model=List[ReminderResponse])
def list_reminders(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db_session),
):
    """Retrieves all scheduled reminders, optionally filtered by status."""
    query = db.query(ScheduledReminder)
    if status_filter:
        query = query.filter(ScheduledReminder.status == status_filter.upper())
    return query.order_by(ScheduledReminder.scheduled_time.desc()).all()


@router.delete("/reminders/{reminder_id}", status_code=status.HTTP_200_OK)
def cancel_reminder(reminder_id: int, db: Session = Depends(get_db_session)):
    """Cancels a scheduled reminder before execution."""
    reminder = db.query(ScheduledReminder).filter(ScheduledReminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    if reminder.status in ("SENT", "COMPLETED"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel already sent reminder")

    reminder.status = "CANCELLED"
    db.commit()
    return {"success": True, "message": f"Reminder #{reminder_id} cancelled"}


# =====================================================================
# 4. Audit Logs & Dashboard Stats
# =====================================================================
@router.get("/logs", response_model=List[EmailLogResponse])
def list_logs(
    limit: int = Query(50, ge=1, le=200),
    recipient: Optional[str] = None,
    db: Session = Depends(get_db_session),
):
    """Lists audit logs of email dispatches."""
    query = db.query(EmailLog)
    if recipient:
        query = query.filter(EmailLog.recipient.ilike(f"%{recipient}%"))
    return query.order_by(EmailLog.created_at.desc()).limit(limit).all()


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db_session)):
    """Returns aggregated metrics for the dashboard view."""
    total_sent = db.query(EmailLog).filter(EmailLog.status == "SENT").count()
    total_failed = db.query(EmailLog).filter(EmailLog.status.in_(["FAILED", "BOUNCED"])).count()
    pending_reminders = db.query(ScheduledReminder).filter(ScheduledReminder.status == "SCHEDULED").count()
    active_templates = db.query(EmailTemplate).count()
    recent_logs = db.query(EmailLog).order_by(EmailLog.created_at.desc()).limit(10).all()

    return DashboardStats(
        total_sent=total_sent,
        total_failed=total_failed,
        pending_reminders=pending_reminders,
        active_templates=active_templates,
        recent_logs=recent_logs,
    )
