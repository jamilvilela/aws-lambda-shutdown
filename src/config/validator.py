"""Configuration validation for the shutdown Lambda."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import ValidationError

from .models import Config


class ConfigValidationError(Exception):
    """Raised when the configuration is invalid."""


def validate_config(data: Dict[str, Any]) -> Config:
    """Validate raw JSON data and return a typed :class:`Config` model."""
    try:
        return Config.model_validate(data)
    except ValidationError as exc:
        raise ConfigValidationError(str(exc)) from exc