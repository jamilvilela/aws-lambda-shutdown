"""EventBridge Scheduler generation from configuration."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from ..config.models import Config

SCHEDULER_PREFIX = "shutdown-"


class SchedulerGenerator:
    """Creates, updates, and cleans up EventBridge Schedulers."""

    def __init__(self, scheduler: Any, lambda_arn: str, scheduler_role_arn: str) -> None:
        self._scheduler = scheduler
        self._lambda_arn = lambda_arn
        self._role_arn = scheduler_role_arn

    def generate(self, config: Config) -> Dict[str, List[str]]:
        desired = self._desired_schedulers(config)
        existing = self._existing_schedulers()
        created = []
        for name, (days, time) in desired.items():
            if name not in existing:
                self._create_scheduler(name, days, time)
                created.append(name)
        removed = []
        for name in existing:
            if name not in desired:
                self._delete_scheduler(name)
                removed.append(name)
        return {"created": created, "removed": removed}

    def _desired_schedulers(self, config: Config) -> Dict[str, Tuple[Tuple[str, ...], str]]:
        """One scheduler per unique time.

        The Lambda shuts down all services whose effective schedule matches the
        invocation time, so a single scheduler per time (instead of one per
        service × time) is sufficient. The days are the union of every service's
        days for that time; the Lambda filters the services again via `matches`.

        Schedulers are tied to a day/time, not to a service, so the per-service
        `enabled` flag does NOT affect them: every service's schedule contributes
        and all schedulers are always created ENABLED. The Lambda skips services
        with `enabled: false` at runtime.
        """
        days_by_time: Dict[str, set] = {}
        for service in config.services:
            schedule = service.schedule or config.general.schedule
            for time in schedule.times:
                days_by_time.setdefault(time, set()).update(schedule.daysOfWeek)
        desired: Dict[str, Tuple[Tuple[str, ...], str]] = {}
        for time, days in sorted(days_by_time.items()):
            name = f"{SCHEDULER_PREFIX}{time.replace(':', '')}"
            desired[name] = (tuple(sorted(days)), time)
        return desired

    def _existing_schedulers(self) -> set:
        names = set()
        paginator = self._scheduler.get_paginator("list_schedules")
        for page in paginator.paginate(NamePrefix=SCHEDULER_PREFIX):
            for schedule in page.get("Schedules", []):
                names.add(schedule["Name"])
        return names

    def _create_scheduler(self, name: str, days: tuple, time: str) -> None:
        hour, minute = time.split(":")
        # EventBridge Scheduler uses 6-field cron (minute hour day-of-month
        # month day-of-week year). Exactly one of day-of-month/day-of-week
        # must be '?'; here we use '?' for day-of-month and enforce the days
        # via day-of-week.
        cron = f"cron({int(minute)} {int(hour)} ? * {','.join(days)} *)"
        self._scheduler.create_schedule(
            Name=name,
            State="ENABLED",
            ScheduleExpression=cron,
            ScheduleExpressionTimezone="UTC",
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": self._lambda_arn,
                "RoleArn": self._role_arn,
                # Pass the scheduled time so the Lambda does not depend on
                # wall-clock precision at invocation.
                "Input": json.dumps({"time": time, "days": list(days)}),
            },
        )

    def _delete_scheduler(self, name: str) -> None:
        self._scheduler.delete_schedule(Name=name)