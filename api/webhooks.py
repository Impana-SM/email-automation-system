"""Webhook receivers for tracking email delivery, opens, clicks, and bounces."""

import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session

from db.database import get_db
from src.models import WebhookEvent, EmailLog
from api.schemas import WebhookPayload, WebhookResponse

logger = logging.getLogger("webhooks")
router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


@router.post("/events", response_model=WebhookResponse, status_code=status.HTTP_200_OK)
async def receive_webhook_event(
    payload: WebhookPayload,
    db: Session = Depends(get_db),
):
    """
    Ingests email tracking webhook events (delivered, opened, clicked, bounced).
    Records event telemetry and updates audit log states when applicable.
    """
    try:
        raw_json = json.dumps(payload.data)
        event = WebhookEvent(
            provider=payload.provider,
            event_type=payload.event_type.lower(),
            recipient=payload.recipient,
            payload=raw_json,
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        logger.info(
            "Webhook received [%s] for recipient: %s from provider: %s",
            payload.event_type,
            payload.recipient,
            payload.provider,
        )

        # Update latest EmailLog entry if recipient matches
        if payload.recipient:
            log_entry = (
                db.query(EmailLog)
                .filter(EmailLog.recipient == payload.recipient)
                .order_by(EmailLog.created_at.desc())
                .first()
            )
            if log_entry and payload.event_type.lower() == "bounced":
                log_entry.status = "BOUNCED"
                log_entry.error_message = f"Bounced via {payload.provider} webhook: {raw_json[:200]}"
                db.commit()

        return WebhookResponse(
            success=True,
            message="Webhook event recorded successfully",
            event_id=event.id,
        )
    except Exception as exc:
        db.rollback()
        logger.error("Failed to process webhook event: %s", exc)
        return WebhookResponse(success=False, message=str(exc))


@router.post("/generic", status_code=status.HTTP_200_OK)
async def receive_raw_generic_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """Accepts arbitrary JSON webhook payloads from third-party SMTP providers."""
    try:
        body = await request.json()
    except Exception:
        body = {"raw_text": (await request.body()).decode("utf-8", errors="ignore")}

    event = WebhookEvent(
        provider="custom_raw",
        event_type="raw_callback",
        payload=json.dumps(body),
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    return {"status": "ok", "event_id": event.id}
