"""Cron types."""

from typing import Literal
from pydantic import BaseModel, Field


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    words = string.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


class CronBase(BaseModel):
    """Base class for cron models with camelCase aliases."""
    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
        "extra": "ignore"
    }


class CronSchedule(CronBase):
    """Schedule definition for a cron job."""
    kind: Literal["at", "every", "cron"]
    # For "at": timestamp in ms
    at_ms: int | None = None
    # For "every": interval in ms
    every_ms: int | None = None
    # For "cron": cron expression (e.g. "0 9 * * *")
    expr: str | None = None
    # Timezone for cron expressions
    tz: str | None = None


class CronPayload(CronBase):
    """What to do when the job runs."""
    kind: Literal["system_event", "agent_turn"] = "agent_turn"
    message: str = ""
    # Deliver response to channel
    deliver: bool = False
    channel: str | None = None  # e.g. "whatsapp"
    to: str | None = None  # e.g. phone number


class CronJobState(CronBase):
    """Runtime state of a job."""
    next_run_at_ms: int | None = None
    last_run_at_ms: int | None = None
    last_status: Literal["ok", "error", "skipped"] | None = None
    last_error: str | None = None


class CronJob(CronBase):
    """A scheduled job."""
    id: str
    name: str
    enabled: bool = True
    schedule: CronSchedule = Field(default_factory=lambda: CronSchedule(kind="every"))
    payload: CronPayload = Field(default_factory=CronPayload)
    state: CronJobState = Field(default_factory=CronJobState)
    created_at_ms: int = 0
    updated_at_ms: int = 0
    delete_after_run: bool = False


class CronStore(CronBase):
    """Persistent store for cron jobs."""
    version: int = 1
    jobs: list[CronJob] = Field(default_factory=list)
