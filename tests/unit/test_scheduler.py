"""Tests for scheduler generator."""

from unittest.mock import MagicMock

import pytest

from src.config.validator import validate_config
from src.scheduler.generator import SchedulerGenerator


SMALL_CONFIG = {
    "general": {
        "schedule": {"daysOfWeek": ["MON", "WED", "FRI"], "times": ["03:00", "22:00"]},
        "notification": {"email": "test@example.com"},
    },
    "services": [
        {"name": "ec2"},
        {"name": "rds"},
    ],
}

# Service with a per-service override: ec2 runs on MON only at 22:00
OVERRIDE_CONFIG = {
    "general": {
        "schedule": {"daysOfWeek": ["MON", "WED", "FRI"], "times": ["03:00"]},
        "notification": {"email": "test@example.com"},
    },
    "services": [
        {"name": "ec2", "schedule": {"daysOfWeek": ["MON"], "times": ["22:00"]}},
        {"name": "rds"},
    ],
}


def test_generate_creates_one_scheduler_per_time():
    scheduler = MagicMock()
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": []}]
    config = validate_config(SMALL_CONFIG)
    gen = SchedulerGenerator(scheduler, "arn:aws:lambda:us-east-1:123:function:test", "arn:aws:iam::123:role/scheduler")
    result = gen.generate(config)
    # 2 unique times → 2 schedulers (not one per service × time)
    assert len(result["created"]) == 2
    assert "shutdown-0300" in result["created"]
    assert "shutdown-2200" in result["created"]
    assert scheduler.create_schedule.call_count == 2
    # Check cron expression for 03:00 on MON,WED,FRI
    call = scheduler.create_schedule.call_args_list[0].kwargs
    assert call["ScheduleExpression"] == "cron(0 3 ? * FRI,MON,WED *)"
    assert call["ScheduleExpressionTimezone"] == "UTC"
    assert call["FlexibleTimeWindow"] == {"Mode": "OFF"}
    assert call["Target"]["Arn"] == "arn:aws:lambda:us-east-1:123:function:test"
    assert call["Target"]["RoleArn"] == "arn:aws:iam::123:role/scheduler"
    # The scheduled time is passed to the Lambda via the target input
    assert call["Target"]["Input"] == '{"time": "03:00", "days": ["FRI", "MON", "WED"]}'
    # Schedulers are created ENABLED by default
    assert call["State"] == "ENABLED"


def _disabled_config(*service_flags: bool) -> dict:
    """SMALL_CONFIG with ec2/rds enabled flags set."""
    cfg = dict(SMALL_CONFIG)
    cfg["services"] = [
        {"name": "ec2", "enabled": service_flags[0]},
        {"name": "rds", "enabled": service_flags[1]},
    ]
    return cfg


def test_generate_disabled_shared_time_is_disabled():
    """All services disabled -> schedulers kept in DISABLED (not deleted)."""
    scheduler = MagicMock()
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": []}]
    config = validate_config(_disabled_config(False, False))
    gen = SchedulerGenerator(scheduler, "arn:lambda", "arn:role")
    result = gen.generate(config)
    assert set(result["created"]) == {"shutdown-0300", "shutdown-2200"}
    assert set(result["disabled"]) == {"shutdown-0300", "shutdown-2200"}
    assert result["enabled"] == []
    assert result["removed"] == []
    for call in scheduler.create_schedule.call_args_list:
        assert call.kwargs["State"] == "DISABLED"
    scheduler.update_schedule.assert_not_called()


def test_generate_disabled_exclusive_time_is_disabled():
    """A time served only by a disabled service is kept but DISABLED."""
    scheduler = MagicMock()
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": []}]
    cfg = {
        "general": {
            "schedule": {"daysOfWeek": ["MON"], "times": ["03:00"]},
            "notification": {"email": "test@example.com"},
        },
        "services": [
            {"name": "ec2", "enabled": False, "schedule": {"daysOfWeek": ["MON"], "times": ["22:00"]}},
            {"name": "rds"},  # enabled → 03:00
        ],
    }
    config = validate_config(cfg)
    gen = SchedulerGenerator(scheduler, "arn:lambda", "arn:role")
    result = gen.generate(config)
    by_name = {c.kwargs["Name"]: c.kwargs for c in scheduler.create_schedule.call_args_list}
    assert by_name["shutdown-0300"]["State"] == "ENABLED"
    assert by_name["shutdown-2200"]["State"] == "DISABLED"
    assert result["enabled"] == ["shutdown-0300"]
    assert result["disabled"] == ["shutdown-2200"]


def test_generate_disables_existing_scheduler_on_reenable_change():
    """An existing ENABLED scheduler becomes DISABLED when its services are disabled."""
    scheduler = MagicMock()
    existing = [
        {"Name": "shutdown-0300", "State": "ENABLED"},
        {"Name": "shutdown-2200", "State": "DISABLED"},
    ]
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": existing}]
    config = validate_config(_disabled_config(False, False))
    gen = SchedulerGenerator(scheduler, "arn:lambda", "arn:role")
    result = gen.generate(config)
    assert result["created"] == []
    assert result["removed"] == []
    assert result["disabled"] == ["shutdown-0300"]
    assert result["enabled"] == []
    scheduler.update_schedule.assert_called_once_with(Name="shutdown-0300", State="DISABLED")


def test_generate_enables_existing_scheduler_when_services_enabled():
    """An existing DISABLED scheduler is re-enabled when a service comes back."""
    scheduler = MagicMock()
    existing = [
        {"Name": "shutdown-0300", "State": "DISABLED"},
        {"Name": "shutdown-2200", "State": "DISABLED"},
    ]
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": existing}]
    config = validate_config(SMALL_CONFIG)
    gen = SchedulerGenerator(scheduler, "arn:lambda", "arn:role")
    result = gen.generate(config)
    assert result["created"] == []
    assert result["removed"] == []
    assert set(result["enabled"]) == {"shutdown-0300", "shutdown-2200"}
    assert result["disabled"] == []
    assert scheduler.update_schedule.call_count == 2
    for call in scheduler.update_schedule.call_args_list:
        assert call.kwargs["State"] == "ENABLED"


def test_generate_unions_days_across_services_per_time():
    scheduler = MagicMock()
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": []}]
    config = validate_config(OVERRIDE_CONFIG)
    gen = SchedulerGenerator(scheduler, "arn:lambda", "arn:role")
    result = gen.generate(config)
    # Times: 03:00 (general) + 22:00 (ec2 override) → 2 schedulers
    assert set(result["created"]) == {"shutdown-0300", "shutdown-2200"}
    by_name = {c.kwargs["Name"]: c.kwargs for c in scheduler.create_schedule.call_args_list}
    # shutdown-0300: ec2 and rds both fire → union of their days
    assert by_name["shutdown-0300"]["ScheduleExpression"] == "cron(0 3 ? * FRI,MON,WED *)"
    # shutdown-2200: only ec2 (override) fires → MON only
    assert by_name["shutdown-2200"]["ScheduleExpression"] == "cron(0 22 ? * MON *)"


def test_generate_idempotent():
    scheduler = MagicMock()
    # First run: no existing
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": []}]
    config = validate_config(SMALL_CONFIG)
    gen = SchedulerGenerator(scheduler, "arn:lambda", "arn:role")
    r1 = gen.generate(config)
    assert len(r1["created"]) == 2
    # Second run: existing schedulers in the correct state
    existing = [{"Name": name, "State": "ENABLED"} for name in r1["created"]]
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": existing}]
    r2 = gen.generate(config)
    assert r2["created"] == []
    assert r2["removed"] == []
    assert r2["enabled"] == []
    assert r2["disabled"] == []
    scheduler.update_schedule.assert_not_called()


def test_generate_uses_configured_timezone():
    scheduler = MagicMock()
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": []}]
    cfg = dict(SMALL_CONFIG)
    cfg["general"] = {**cfg["general"], "timezone": "America/Sao_Paulo"}
    config = validate_config(cfg)
    gen = SchedulerGenerator(scheduler, "arn:lambda", "arn:role")
    gen.generate(config)
    for call in scheduler.create_schedule.call_args_list:
        assert call.kwargs["ScheduleExpressionTimezone"] == "America/Sao_Paulo"


def test_remove_all_deletes_every_managed_scheduler():
    scheduler = MagicMock()
    existing = [{"Name": "shutdown-0300"}, {"Name": "shutdown-2200"}]
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": existing}]
    gen = SchedulerGenerator(scheduler)
    result = gen.remove_all()
    assert set(result["removed"]) == {"shutdown-0300", "shutdown-2200"}
    assert scheduler.delete_schedule.call_count == 2
    scheduler.delete_schedule.assert_any_call(Name="shutdown-0300")
    scheduler.delete_schedule.assert_any_call(Name="shutdown-2200")


def test_remove_all_with_no_schedulers():
    scheduler = MagicMock()
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": []}]
    gen = SchedulerGenerator(scheduler)
    result = gen.remove_all()
    assert result["removed"] == []
    scheduler.delete_schedule.assert_not_called()


def test_generate_cleanup_removed():
    scheduler = MagicMock()
    # Existing schedulers include one not in desired
    existing = [
        {"Name": "shutdown-0300"},
        {"Name": "shutdown-2200"},
        {"Name": "shutdown-old-service-0300"},  # should be removed
    ]
    scheduler.get_paginator.return_value.paginate.return_value = [{"Schedules": existing}]
    config = validate_config(SMALL_CONFIG)
    gen = SchedulerGenerator(scheduler, "arn:lambda", "arn:role")
    result = gen.generate(config)
    assert "shutdown-old-service-0300" in result["removed"]
    scheduler.delete_schedule.assert_called_once_with(Name="shutdown-old-service-0300")