"""Main Lambda handler."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict
from zoneinfo import ZoneInfo

import boto3

from .config.loader import ConfigLoadError, load_config
from .config.validator import ConfigValidationError, validate_config
from .notifier import SNSNotifier
from .schedule.matcher import matches
from .scheduler.generator import SchedulerGenerator
from .services.factory import ServiceClients, ServiceFactory

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _build_clients() -> ServiceClients:
    return ServiceClients(
        ec2=boto3.client("ec2"),
        rds=boto3.client("rds"),
        ecs=boto3.client("ecs"),
        glue=boto3.client("glue"),
        batch=boto3.client("batch"),
        dms=boto3.client("dms"),
    )


def _build_notifier() -> SNSNotifier:
    return SNSNotifier(
        sns=boto3.client("sns"),
        topic_arn=os.environ["SNS_TOPIC_ARN"],
    )


def _resolve_now(event: Dict[str, Any], tz: ZoneInfo | None = None) -> datetime | None:
    """Extract the scheduled time ("HH:MM") from the Scheduler event, if present.

    When ``tz`` is given, the resulting datetime is interpreted in that
    timezone (the weekday/date come from the current time there); otherwise a
    naive UTC-style datetime is returned.
    """
    trigger = (event or {}).get("time")
    if not trigger:
        return None
    try:
        time = datetime.strptime(trigger, "%H:%M").time()
    except ValueError:
        return None
    if tz is not None:
        return datetime.combine(datetime.now(tz).date(), time, tzinfo=tz)
    return datetime.combine(datetime.now().date(), time)


def lambda_handler(event: Dict[str, Any], context: Any, now: datetime | None = None) -> Dict[str, Any]:
    """Entry point invoked by EventBridge Scheduler."""
    try:
        config = validate_config(load_config())
    except (ConfigLoadError, ConfigValidationError) as exc:
        logger.error("Configuration error: %s", exc)
        notifier = _build_notifier()
        notifier.notify_error(str(exc), now or _resolve_now(event) or datetime.now())
        raise

    if now is None:
        tz = ZoneInfo(config.general.timezone)
        now = _resolve_now(event, tz) or datetime.now(tz)

    factory = ServiceFactory(_build_clients())
    failures = []
    services_processed = 0
    for service in config.services:
        if not service.enabled:
            logger.info("Service %s disabled — skipping", service.name)
            continue
        schedule = service.schedule or config.general.schedule
        if not matches(schedule, now):
            continue
        services_processed += 1
        handler = factory.create(service.name)
        failures.extend(handler.run())

    if failures:
        notifier = _build_notifier()
        notifier.notify_failures(failures, now)

    return {"status": "ok", "services_processed": services_processed, "failures": len(failures)}


def generate_schedulers_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Entry point for scheduler generation (can be invoked manually or via a separate schedule)."""
    config = validate_config(load_config())
    generator = SchedulerGenerator(
        scheduler=boto3.client("scheduler"),
        lambda_arn=os.environ["LAMBDA_ARN"],
        scheduler_role_arn=os.environ["SCHEDULER_ROLE_ARN"],
    )
    result = generator.generate(config)
    return {"status": "ok", **result}