"""Configuration validation for the shutdown Lambda."""

from __future__ import annotations

import json
import os
from typing import Any, Dict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import jsonschema
from jsonschema import FormatChecker

from .models import Config, General, Notification, Schedule, Service

_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.json")


class ConfigValidationError(Exception):
    """Raised when the configuration is invalid."""


def _load_schema() -> Dict[str, Any]:
    with open(_SCHEMA_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_models(data: Dict[str, Any]) -> Config:
    """Build the typed models from a schema-validated dictionary."""
    general = data["general"]
    schedule = Schedule(**general["schedule"])
    config = Config(
        general=General(
            schedule=schedule,
            notification=Notification(**general["notification"]),
            timezone=general.get("timezone", "UTC"),
        ),
        services=[],
    )
    for service in data["services"]:
        config.services.append(
            Service(
                name=service["name"],
                enabled=service.get("enabled", True),
                schedule=Schedule(**service["schedule"]) if service.get("schedule") else None,
            )
        )
    return config


def validate_config(data: Dict[str, Any]) -> Config:
    """Validate raw JSON data and return a typed :class:`Config` model."""
    try:
        jsonschema.validate(data, _load_schema(), format_checker=FormatChecker())
        timezone = data.get("general", {}).get("timezone", "UTC")
        ZoneInfo(timezone)
    except jsonschema.ValidationError as exc:
        raise ConfigValidationError(str(exc)) from exc
    except ZoneInfoNotFoundError as exc:
        raise ConfigValidationError(f"Invalid timezone: {timezone!r}") from exc
    return _build_models(data)