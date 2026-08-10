"""Configuration data models for the shutdown Lambda."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

VALID_DAYS = {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}


@dataclass
class Schedule:
    """Days of the week and a list of times (HH:MM, 24h)."""

    daysOfWeek: List[str]
    times: List[str]


@dataclass
class Notification:
    """Notification settings (email)."""

    email: str


@dataclass
class General:
    """General configuration: schedule, timezone and notification."""

    schedule: Schedule
    notification: Notification
    timezone: str = "UTC"


@dataclass
class Service:
    """A service to be scanned, with an optional specific schedule.

    ``enabled`` controls whether the service participates in the shutdown;
    when ``false`` it is skipped by the Lambda and shared schedulers at its
    times are kept DISABLED in the console (not deleted).
    """

    name: str
    enabled: bool = True
    schedule: Optional[Schedule] = None


@dataclass
class Config:
    """Root configuration model."""

    general: General
    services: List[Service] = field(default_factory=list)