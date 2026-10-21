"""Background asynchronous worker process executing scheduled email reminders."""

import asyncio
import json
import logging
import signal
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy.orm import Session

load_dotenv()

from db.database import SessionLocal, engine, Base
from src.models import ScheduledReminder, EmailTemplate, EmailLog
from src.mailer import Mailer
from src.template_service import TemplateService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("worker")

mailer = Mailer()
template_service = TemplateService()
is_running = True


def handle_stop_signal(*_):
    """Signals graceful loop termination on SIGINT or SIGTERM."""
    global is_running
    logger.info("Termination signal received. Shutting down worker loop gracefully...")
    is_running = False


async def process_due_reminders():
    """Fetches and executes due reminders from the database."""
    db: Session = SessionLocal()
    try:
        now = datetime.utcnow()
        due_reminders = (
            db.query(ScheduledReminder)
            .filter(
                ScheduledReminder.status == "SCHEDULED",
                ScheduledReminder.scheduled_time <= now,
            )
            .with_for_update(skip_locked=True)
            .all()
            if engine.dialect.name != "sqlite"
            else db.query(ScheduledReminder)
            .filter(
                ScheduledReminder.status == "SCHEDULED",
                ScheduledReminder.scheduled_time <= now,
            )
            .all()
        )

        if not due_reminders:
            return

        logger.info("Found %d due reminders for processing.", len(due_reminders))

        for reminder in due_reminders:
            reminder.status = "PROCESSING"
            db.commit()

            subject = reminder.subject or "Scheduled Reminder"
            body = reminder.body or ""

            # Render template if template_id is specified
            if reminder.template_id:
                tmpl = db.query(EmailTemplate).filter(EmailTemplate.id == reminder.template_id).first()
                if tmpl:
                    context = json.loads(reminder.context_data) if reminder.context_data else {}
                    try:
                        subject, body = template_service.render(
                            tmpl.subject_template,
                            tmpl.body_template,
                            context,
                        )
                    except Exception as render_err:
                        reminder.status = "FAILED"
                        reminder.error_message = f"Render error: {str(render_err)}"
                        db.commit()
                        logger.error("Template rendering failed for reminder #%d: %s", reminder.id, render_err)
                        continue
                else:
                    reminder.status = "FAILED"
                    reminder.error_message = f"Template #{reminder.template_id} does not exist"
                    db.commit()
                    logger.error("Template not found for reminder #%d", reminder.id)
                    continue

            # Dispatch via Mailer
            success, error = await mailer.send_email(
                to_email=reminder.recipient,
                subject=subject,
                body=body,
                is_html=True,
            )

            # Record audit log
            log_entry = EmailLog(
                reminder_id=reminder.id,
                recipient=reminder.recipient,
                subject=subject,
                body=body,
                status="SUCCESS" if success else "FAILED",
                error_message=error,
                sent_at=datetime.utcnow() if success else None,
            )
            db.add(log_entry)

            if success:
                reminder.status = "SUCCESS"
                reminder.error_message = None
                logger.info("Successfully dispatched reminder #%d to %s", reminder.id, reminder.recipient)
            else:
                reminder.retry_count += 1
                if reminder.retry_count >= reminder.max_retries:
                    reminder.status = "FAILED"
                    reminder.error_message = f"Max retries reached: {error}"
                    logger.error("Reminder #%d permanently failed: %s", reminder.id, error)
                else:
                    reminder.status = "SCHEDULED"  # Requeue for retry
                    reminder.error_message = f"Attempt {reminder.retry_count} failed: {error}"
                    logger.warning("Reminder #%d attempt %d failed, requeuing.", reminder.id, reminder.retry_count)

            db.commit()

    except Exception as exc:
        db.rollback()
        logger.error("Unexpected error in reminder processing loop: %s", exc)
    finally:
        db.close()


def process_pending_tasks():
    """Synchronously processes all due pending reminder tasks."""
    try:
        asyncio.run(process_due_reminders())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(process_due_reminders())



async def main():
    """Starts the continuous reminder worker polling loop."""
    logger.info("Starting Email Automation & Reminder Worker...")
    Base.metadata.create_all(bind=engine)

    # Register OS signal handlers if supported
    try:
        signal.signal(signal.SIGINT, handle_stop_signal)
        signal.signal(signal.SIGTERM, handle_stop_signal)
    except (ValueError, AttributeError):
        pass  # Windows environment fallback

    while is_running:
        await process_due_reminders()
        await asyncio.sleep(5)  # 5-second polling interval

    logger.info("Worker loop stopped cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker interrupted by user.")
