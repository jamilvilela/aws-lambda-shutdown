"""Test fixtures and configuration."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from src.config.models import Config, General, Notification, Schedule, Service
from src.config.validator import validate_config


@pytest.fixture
def valid_config_dict() -> dict:
    """A minimal valid configuration dictionary."""
    return {
        "general": {
            "schedule": {
                "daysOfWeek": ["MON", "TUE", "WED", "THU", "FRI"],
                "times": ["03:00", "22:00"],
            },
            "notification": {"email": "test@example.com"},
        },
        "services": [
            {"name": "ec2"},
            {"name": "rds"},
        ],
    }


@pytest.fixture
def valid_config(valid_config_dict) -> Config:
    """A validated Config model."""
    return validate_config(valid_config_dict)


@pytest.fixture
def small_config_dict() -> dict:
    """A small config with one service and two times."""
    return {
        "general": {
            "schedule": {
                "daysOfWeek": ["MON", "WED", "FRI"],
                "times": ["03:00", "22:00"],
            },
            "notification": {"email": "test@example.com"},
        },
        "services": [
            {"name": "ec2"},
        ],
    }


@pytest.fixture
def small_config(small_config_dict) -> Config:
    return validate_config(small_config_dict)


@pytest.fixture
def monday_0300() -> datetime:
    """Monday 2024-01-01 03:00 UTC."""
    return datetime(2024, 1, 1, 3, 0)


@pytest.fixture
def monday_2200() -> datetime:
    """Monday 2024-01-01 22:00 UTC."""
    return datetime(2024, 1, 1, 22, 0)


@pytest.fixture
def tuesday_0300() -> datetime:
    """Tuesday 2024-01-02 03:00 UTC."""
    return datetime(2024, 1, 2, 3, 0)


@pytest.fixture
def temp_config_file(tmp_path: Path, valid_config_dict: dict) -> Path:
    """Create a temporary config.json file."""
    path = tmp_path / "config.json"
    path.write_text(json.dumps(valid_config_dict))
    return path