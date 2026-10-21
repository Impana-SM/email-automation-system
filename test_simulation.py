"""Simulation script testing contact creation, reminder scheduling, and synchronous task execution."""

import sys
import json
import warnings
from datetime import datetime, timezone

# Suppress datetime deprecation notice in test output
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Ensure standard output supports UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from db.database import engine, SessionLocal, Base
from src.models import Contact, ScheduledReminder, EmailLog
from run_worker import process_pending_tasks


def run_simulation():
    print("=" * 60)
    print("[START] EMAIL AUTOMATION SIMULATION TEST")
    print("=" * 60)

    # Ensure database tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Step 1: Programmatically create a test contact
        test_email = "test@example.com"
        contact = db.query(Contact).filter(Contact.email == test_email).first()
        if not contact:
            contact = Contact(email=test_email, name="Simulation User")
            db.add(contact)
            db.commit()
            db.refresh(contact)
            print(f"[OK] Step 1: Created test contact: {contact.email} (ID: {contact.id})")
        else:
            print(f"[INFO] Step 1: Contact already exists: {contact.email} (ID: {contact.id})")

        # Step 2: Schedule a reminder set to trigger immediately
        now = datetime.utcnow()
        reminder = ScheduledReminder(
            recipient=contact.email,
            subject="Urgent: Simulated Account Reminder",
            body="Hello Simulation User, this is an immediate automated verification reminder.",
            scheduled_time=now,
            status="SCHEDULED",
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        print(f"[OK] Step 2: Scheduled reminder #{reminder.id} for {reminder.recipient} (Time: {reminder.scheduled_time} UTC)")

    finally:
        db.close()

    # Step 3: Invoke the background task processor function synchronously
    print("[RUN] Step 3: Invoking background processor `process_pending_tasks()` synchronously...")
    process_pending_tasks()
    print("[OK] Step 3: `process_pending_tasks()` execution completed.")

    # Step 4: Verify that an email log is successfully created with status SUCCESS
    db = SessionLocal()
    try:
        log = (
            db.query(EmailLog)
            .filter(EmailLog.recipient == test_email)
            .order_by(EmailLog.id.desc())
            .first()
        )

        reminder_updated = (
            db.query(ScheduledReminder)
            .filter(ScheduledReminder.id == reminder.id)
            .first()
        )

        print("\n" + "=" * 60)
        print("[VERIFICATION RESULTS]")
        print("=" * 60)

        if not log:
            print("[FAIL] FAILURE: No EmailLog record was created for", test_email)
            raise AssertionError("Verification failed: No email log created.")

        print(f"• Email Log ID:      #{log.id}")
        print(f"• Recipient:         {log.recipient}")
        print(f"• Subject:           {log.subject}")
        print(f"• Email Log Status:  {log.status}")
        print(f"• Reminder Status:   {reminder_updated.status if reminder_updated else 'N/A'}")
        print(f"• Dispatched At:     {log.sent_at}")

        assert log.status == "SUCCESS", f"Expected log status 'SUCCESS', got '{log.status}'"
        print("\n[SUCCESS] VERIFICATION PASSED: Email log successfully created with status 'SUCCESS'!")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    run_simulation()
