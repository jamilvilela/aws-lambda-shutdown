"""Tests for config loader and validator."""

import json
import pytest

from src.config.loader import load_config, ConfigLoadError
from src.config.models import Config
from src.config.validator import validate_config, ConfigValidationError


def test_load_valid_config(temp_config_file):
    data = load_config(str(temp_config_file))
    assert data["general"]["notification"]["email"] == "test@example.com"
    assert len(data["services"]) == 2


def test_load_missing_file():
    with pytest.raises(ConfigLoadError):
        load_config("nonexistent.json")


def test_validate_valid_config(valid_config_dict):
    config = validate_config(valid_config_dict)
    assert isinstance(config, Config)
    assert config.services[0].name == "ec2"
    assert config.general.notification.email == "test@example.com"


def test_validate_missing_general():
    with pytest.raises(ConfigValidationError):
        validate_config({"services": [{"name": "ec2"}]})


def test_validate_missing_services():
    with pytest.raises(ConfigValidationError):
        validate_config({"general": {"schedule": {"daysOfWeek": ["MON"], "times": ["03:00"]}, "notification": {"email": "a@b.c"}}})


def test_validate_invalid_day():
    data = {
        "general": {
            "schedule": {"daysOfWeek": ["XXX"], "times": ["03:00"]},
            "notification": {"email": "a@b.c"},
        },
        "services": [{"name": "ec2"}],
    }
    with pytest.raises(ConfigValidationError):
        validate_config(data)


def test_validate_invalid_time():
    data = {
        "general": {
            "schedule": {"daysOfWeek": ["MON"], "times": ["25:00"]},
            "notification": {"email": "a@b.c"},
        },
        "services": [{"name": "ec2"}],
    }
    with pytest.raises(ConfigValidationError):
        validate_config(data)


def test_validate_invalid_time_format():
    data = {
        "general": {
            "schedule": {"daysOfWeek": ["MON"], "times": ["3:00"]},
            "notification": {"email": "a@b.c"},
        },
        "services": [{"name": "ec2"}],
    }
    with pytest.raises(ConfigValidationError):
        validate_config(data)


def test_validate_service_without_schedule_inherits_general(valid_config_dict):
    config = validate_config(valid_config_dict)
    # rds has no schedule, should inherit general
    rds = next(s for s in config.services if s.name == "rds")
    assert rds.schedule is None


def test_validate_service_with_specific_schedule():
    data = {
        "general": {
            "schedule": {"daysOfWeek": ["MON"], "times": ["03:00"]},
            "notification": {"email": "a@b.c"},
        },
        "services": [
            {"name": "ec2", "schedule": {"daysOfWeek": ["TUE"], "times": ["22:00"]}}
        ],
    }
    config = validate_config(data)
    ec2 = config.services[0]
    assert ec2.schedule is not None
    assert ec2.schedule.daysOfWeek == ["TUE"]
    assert ec2.schedule.times == ["22:00"]