"""EventBridge Scheduler generation from configuration."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from ..config.models import Config

SCHEDULER_PREFIX = "shutdown-"
ENABLED = "ENABLED"
DISABLED = "DISABLED"


class SchedulerGenerator:
    """Creates, updates, and cleans up EventBridge Schedulers."""

    def __init__(self, scheduler: Any, lambda_arn: str = "", scheduler_role_arn: str = "") -> None:
        self._scheduler = scheduler
        self._lambda_arn = lambda_arn
        self._role_arn = scheduler_role_arn

    def remove_all(self) -> Dict[str, List[str]]:
        """Delete every managed ``shutdown-*`` scheduler from the account."""
        removed = []
        for name in self._existing_schedulers():
            self._delete_scheduler(name)
            removed.append(name)
        return {"removed": removed}

    def generate(self, config: Config) -> Dict[str, List[str]]:
        """Sync EventBridge Schedulers to the config.

        Schedulers are enabled when at least one enabled service contributes to
        their time; when only disabled services share a time the scheduler is
        kept but set to DISABLED (re-enabling a service flips it back).
        """
        desired = self._desired_schedulers(config)
        existing = self._existing_schedulers()
        timezone = config.general.timezone
        created = []
        removed = []
        enabled = []
        disabled = []
        for name, (days, time, state) in desired.items():
            if name not in existing:
                self._create_scheduler(name, days, time, state, timezone)
                created.append(name)
                (enabled if state == ENABLED else disabled).append(name)
            elif existing[name] != state:
                self._update_scheduler(name, state)
                (enabled if state == ENABLED else disabled).append(name)
        for name in existing:
            if name not in desired:
                self._delete_scheduler(name)
                removed.append(name)
        return {
            "created": created,
            "removed": removed,
            "enabled": enabled,
            "disabled": disabled,
        }

    def _desired_schedulers(self, config: Config) -> Dict[str, Tuple[Tuple[str, ...], str, str]]:
        """One scheduler per unique time.

        The Lambda shuts down all services whose effective schedule matches the
        invocation time, so a single scheduler per time (instead of one per
        service × time) is sufficient. The days are the union of every service's
        days for that time; the Lambda filters the services again via `matches`.

        A time shared by at least one `enabled` service produces an ENABLED
        scheduler. A time served only by `enabled: false` services is kept
        (so the schedule survives re-enabling) but created/held in DISABLED.
        """
        days_by_time: Dict[str, set] = {}
        enabled_by_time: Dict[str, bool] = {}
        for service in config.services:
            schedule = service.schedule or config.general.schedule
            for time in schedule.times:
                days_by_time.setdefault(time, set()).update(schedule.daysOfWeek)
                enabled_by_time[time] = enabled_by_time.get(time, False) or service.enabled
        desired: Dict[str, Tuple[Tuple[str, ...], str, str]] = {}
        for time, days in sorted(days_by_time.items()):
            name = f"{SCHEDULER_PREFIX}{time.replace(':', '')}"
            state = ENABLED if enabled_by_time[time] else DISABLED
            desired[name] = (tuple(sorted(days)), time, state)
        return desired

    def _existing_schedulers(self) -> Dict[str, str]:
        current = {}
        paginator = self._scheduler.get_paginator("list_schedules")
        for page in paginator.paginate(NamePrefix=SCHEDULER_PREFIX):
            for schedule in page.get("Schedules", []):
                current[schedule["Name"]] = schedule.get("State")
        return current

    def _create_scheduler(self, name: str, days: tuple, time: str, state: str, timezone: str) -> None:
        hour, minute = time.split(":")
        # EventBridge Scheduler uses 6-field cron (minute hour day-of-month
        # month day-of-week year). Exactly one of day-of-month/day-of-week
        # must be '?'; here we use '?' for day-of-month and enforce the days
        # via day-of-week. The cron is evaluated in the configured timezone.
        cron = f"cron({int(minute)} {int(hour)} ? * {','.join(days)} *)"
        self._scheduler.create_schedule(
            Name=name,
            State=state,
            ScheduleExpression=cron,
            ScheduleExpressionTimezone=timezone,
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": self._lambda_arn,
                "RoleArn": self._role_arn,
                # Pass the scheduled time so the Lambda does not depend on
                # wall-clock precision at invocation.
                "Input": json.dumps({"time": time, "days": list(days)}),
            },
        )

    def _update_scheduler(self, name: str, state: str) -> None:
        self._scheduler.update_schedule(Name=name, State=state)

    def _delete_scheduler(self, name: str) -> None:
        self._scheduler.delete_schedule(Name=name)