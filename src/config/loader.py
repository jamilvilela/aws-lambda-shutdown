"""Configuration loader for the shutdown Lambda."""

from __future__ import annotations

import json
import os
from typing import Any, Dict
from urllib.parse import urlparse

import boto3


class ConfigLoadError(Exception):
    """Raised when the configuration file cannot be loaded."""


def _load_from_s3(s3_url: str) -> Dict[str, Any]:
    parsed = urlparse(s3_url)
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    if not bucket or not key:
        raise ConfigLoadError(f"Invalid S3 URL: {s3_url}")
    s3 = boto3.client("s3")
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        return json.loads(response["Body"].read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise ConfigLoadError(f"Failed to load configuration from {s3_url}: {exc}") from exc


def load_config(config_file: str | None = None) -> Dict[str, Any]:
    """Load the raw JSON configuration from a local file or an S3 URL.

    The path comes from ``config_file`` or the ``CONFIG_FILE`` environment
    variable (defaults to ``config.json``).
    """
    path = config_file or os.environ.get("CONFIG_FILE", "config.json")
    try:
        if path.startswith("s3://"):
            return _load_from_s3(path)
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except ConfigLoadError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise ConfigLoadError(f"Failed to load configuration from {path}: {exc}") from exc