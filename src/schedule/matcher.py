"""Schedule matching logic."""

from __future__ import annotations

from datetime import datetime

from ..config.models import Schedule

DAY_INDEX = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


def matches(schedule: Schedule, now: datetime | None = None) -> bool:
    """Return True if the given schedule matches the current time/day."""
    now = now or datetime.now()
    if now.weekday() not in [DAY_INDEX[d] for d in schedule.daysOfWeek]:
        return False
    return now.strftime("%H:%M") in schedule.times