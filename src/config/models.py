"""Configuration data models for the shutdown Lambda."""

from __future__ import annotations

import re
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

VALID_DAYS = {"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"}
TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class Schedule(BaseModel):
    """Days of the week and a list of times (HH:MM, 24h)."""

    daysOfWeek: List[str]
    times: List[str]

    @field_validator("daysOfWeek")
    @classmethod
    def _validate_days(cls, value: List[str]) -> List[str]:
        for day in value:
            if day not in VALID_DAYS:
                raise ValueError(
                    f"Invalid day of week: {day!r}. Valid values: {sorted(VALID_DAYS)}"
                )
        return value

    @field_validator("times")
    @classmethod
    def _validate_times(cls, value: List[str]) -> List[str]:
        for time in value:
            if not TIME_PATTERN.match(time):
                raise ValueError(
                    f"Invalid time: {time!r}. Expected HH:MM in 24h format."
                )
        return value


class Notification(BaseModel):
    """Notification settings (email)."""

    email: str = Field(min_length=3)


class General(BaseModel):
    """General configuration: default schedule and notification."""

    schedule: Schedule
    notification: Notification


class Service(BaseModel):
    """A service to be scanned, with an optional specific schedule.

    ``enabled`` controls whether the service participates in the shutdown;
    when ``false`` it is skipped by the Lambda and shared schedulers at its
    times are kept DISABLED in the console (not deleted).
    """

    name: str = Field(min_length=1)
    enabled: bool = True
    schedule: Optional[Schedule] = None


class Config(BaseModel):
    """Root configuration model."""

    general: General
    services: List[Service] = Field(min_length=1)