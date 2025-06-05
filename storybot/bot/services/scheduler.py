"""
storybot.bot.services.scheduler
───────────────────────────────
A single AsyncIOScheduler instance plus helpers to (re)schedule
user-specific background jobs.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------

scheduler: AsyncIOScheduler = AsyncIOScheduler()  # created once


def start_scheduler() -> None:
    """Call this inside Aiogram’s startup hook (after event-loop exists)."""
    if not scheduler.running:
        scheduler.start()
        log.info("APScheduler started")


# ---------------------------------------------------------------------------

def _job_id(user_id: int) -> str:
    """Consistent job id format: user:123456"""
    return f"user:{user_id}"


def schedule_user_job(user_id: int, hours: int, coroutine_callable) -> None:
    """
    Add or replace an interval job for *user_id*.

    Parameters
    ----------
    user_id : int
        Telegram user ID – becomes part of the job id.
    hours : int
        Interval in hours between executions.
    coroutine_callable : Coroutine function
        The async function to execute (e.g. fetch_and_push_stories).
    """
    job_id = _job_id(user_id)
    trigger = IntervalTrigger(hours=hours)

    # replace_existing=True ensures idempotency
    scheduler.add_job(
        coroutine_callable,
        trigger=trigger,
        id=job_id,
        args=[user_id],
        replace_existing=True,
        misfire_grace_time=60,
    )
    log.info("Scheduled auto-check for %s every %sh", user_id, hours)


def remove_user_job(user_id: int) -> None:
    """Delete the interval job for *user_id* if it exists."""
    job_id = _job_id(user_id)
    try:
        scheduler.remove_job(job_id)
        log.info("Removed auto-check for %s", user_id)
    except Exception:  # job not found – silently ignore
        pass
