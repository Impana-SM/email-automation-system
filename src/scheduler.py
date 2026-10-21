"""Production-ready asynchronous reminder scheduler utilizing APScheduler."""

import logging
from datetime import datetime
from typing import Callable, Any, Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.job import Job

logger = logging.getLogger("scheduler")


class ReminderScheduler:
    """Async scheduler managing one-time and recurring email reminders."""

    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler()
        self._is_running = False

    def start(self) -> None:
        """Starts the scheduler if not already active."""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("ReminderScheduler started.")

    def shutdown(self, wait: bool = True) -> None:
        """Gracefully terminates scheduled jobs."""
        if self._is_running:
            self.scheduler.shutdown(wait=wait)
            self._is_running = False
            logger.info("ReminderScheduler terminated.")

    def is_running(self) -> bool:
        """Returns True if the scheduler is active."""
        return self._is_running

    def add_reminder_job(
        self,
        job_id: str,
        run_date: datetime,
        func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> Optional[str]:
        """Schedules an async or sync callback at a specific run_date."""
        try:
            self.scheduler.add_job(
                func,
                trigger=DateTrigger(run_date=run_date),
                id=job_id,
                args=args,
                kwargs=kwargs,
                replace_existing=True,
                misfire_grace_time=3600,  # 1 hour grace time for missed jobs
            )
            logger.info("Job %s successfully registered for execution at %s", job_id, run_date)
            return job_id
        except Exception as exc:
            logger.error("Failed to schedule job %s: %s", job_id, str(exc))
            return None

    def cancel_reminder_job(self, job_id: str) -> bool:
        """Removes a registered job by its identifier."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info("Job %s cancelled successfully.", job_id)
            return True
        except Exception as exc:
            logger.warning("Failed to cancel job %s: %s", job_id, str(exc))
            return False

    def reschedule_reminder(self, job_id: str, new_run_date: datetime) -> bool:
        """Updates the trigger time for an existing job."""
        try:
            self.scheduler.reschedule_job(
                job_id,
                trigger=DateTrigger(run_date=new_run_date),
            )
            logger.info("Job %s rescheduled to %s", job_id, new_run_date)
            return True
        except Exception as exc:
            logger.error("Failed to reschedule job %s: %s", job_id, str(exc))
            return False

    def get_scheduled_jobs(self) -> List[Job]:
        """Returns all currently queued jobs."""
        return self.scheduler.get_jobs()
