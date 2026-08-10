"""Integration-style tests for the main handler flow."""

import datetime as _dt
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

import pytest

from src.config.loader import ConfigLoadError
from src.handler import _resolve_now, lambda_handler


VALID_CONFIG = {
    "general": {
        "schedule": {"daysOfWeek": ["MON", "TUE", "WED", "THU", "FRI"], "times": ["03:00", "22:00"]},
        "notification": {"email": "test@example.com"},
    },
    "services": [
        {"name": "ec2"},
        {"name": "rds"},
    ],
}

# Config where services only run on Monday (so Tuesday should skip)
MONDAY_ONLY_CONFIG = {
    "general": {
        "schedule": {"daysOfWeek": ["MON"], "times": ["03:00"]},
        "notification": {"email": "test@example.com"},
    },
    "services": [
        {"name": "ec2"},
        {"name": "rds"},
    ],
}


@patch("src.handler._build_clients")
@patch("src.handler._build_notifier")
@patch("src.handler.load_config", return_value=VALID_CONFIG)
def test_lambda_handler_processes_services_on_schedule(mock_load, mock_notifier, mock_clients, monday_0300):
    """Handler runs services when schedule matches."""
    mock_notifier.return_value = MagicMock()
    mock_clients.return_value = MagicMock()

    with patch("src.handler.ServiceFactory") as mock_factory_cls:
        mock_factory = MagicMock()
        mock_factory_cls.return_value = mock_factory
        mock_handler = MagicMock()
        mock_handler.run.return_value = []
        mock_factory.create.return_value = mock_handler

        event = {}
        context = MagicMock()
        result = lambda_handler(event, context, now=monday_0300)

        assert result["status"] == "ok"
        assert result["services_processed"] == 2
        assert result["failures"] == 0
        assert mock_factory.create.call_count == 2


@patch("src.handler._build_clients")
@patch("src.handler._build_notifier")
@patch("src.handler.load_config", return_value=MONDAY_ONLY_CONFIG)
def test_lambda_handler_skips_services_not_on_schedule(mock_load, mock_notifier, mock_clients, tuesday_0300):
    """Handler skips services when schedule doesn't match."""
    mock_notifier.return_value = MagicMock()
    mock_clients.return_value = MagicMock()

    with patch("src.handler.ServiceFactory") as mock_factory_cls:
        mock_factory = MagicMock()
        mock_factory_cls.return_value = mock_factory
        mock_handler = MagicMock()
        mock_handler.run.return_value = []
        mock_factory.create.return_value = mock_handler

        event = {}
        context = MagicMock()
        result = lambda_handler(event, context, now=tuesday_0300)

        assert result["services_processed"] == 0
        assert result["failures"] == 0
        mock_factory.create.assert_not_called()


@patch("src.handler._build_clients")
@patch("src.handler._build_notifier")
def test_lambda_handler_skips_disabled_services(mock_notifier, mock_clients, monday_0300):
    """Handler skips services with `enabled: false` even when the schedule matches."""
    mock_notifier.return_value = MagicMock()
    mock_clients.return_value = MagicMock()

    disabled_config = {
        "general": {
            "schedule": {"daysOfWeek": ["MON"], "times": ["03:00"]},
            "notification": {"email": "test@example.com"},
        },
        "services": [
            {"name": "ec2", "enabled": False},
            {"name": "rds", "enabled": True},
        ],
    }

    with patch("src.handler.load_config", return_value=disabled_config) as mock_load:
        with patch("src.handler.ServiceFactory") as mock_factory_cls:
            mock_factory = MagicMock()
            mock_factory_cls.return_value = mock_factory
            mock_handler = MagicMock()
            mock_handler.run.return_value = []
            mock_factory.create.return_value = mock_handler

            event = {}
            context = MagicMock()
            result = lambda_handler(event, context, now=monday_0300)

            # Only rds (enabled) was processed; ec2 was skipped
            assert result["services_processed"] == 1
            assert result["failures"] == 0
            assert mock_factory.create.call_count == 1
            mock_factory.create.assert_called_once_with("rds")


@patch("src.handler._build_clients")
@patch("src.handler._build_notifier")
@patch("src.handler.load_config", return_value=VALID_CONFIG)
def test_lambda_handler_sends_notification_on_failure(mock_load, mock_notifier, mock_clients, monday_0300):
    """Handler sends SNS notification when a service fails."""
    mock_notifier.return_value = MagicMock()
    mock_clients.return_value = MagicMock()

    with patch("src.handler.ServiceFactory") as mock_factory_cls:
        mock_factory = MagicMock()
        mock_factory_cls.return_value = mock_factory
        failing_handler = MagicMock()
        failing_handler.run.return_value = [
            MagicMock(service="ec2", item="i-1", reason="timeout")
        ]
        ok_handler = MagicMock()
        ok_handler.run.return_value = []
        mock_factory.create.side_effect = [failing_handler, ok_handler]

        event = {}
        context = MagicMock()
        result = lambda_handler(event, context, now=monday_0300)

        assert result["failures"] == 1
        mock_notifier.return_value.notify_failures.assert_called_once()


@patch("src.handler._build_clients")
@patch("src.handler._build_notifier")
def test_lambda_handler_config_error_sends_fallback(mock_notifier, mock_clients, monday_0300):
    """Handler sends fallback notification on config error."""
    mock_notifier.return_value = MagicMock()
    mock_clients.return_value = MagicMock()

    with patch("src.handler.load_config", side_effect=ConfigLoadError("File not found")):
        event = {}
        context = MagicMock()
        with pytest.raises(ConfigLoadError):
            lambda_handler(event, context, now=monday_0300)
        mock_notifier.return_value.notify_error.assert_called_once()


@patch("src.handler._build_clients")
@patch("src.handler._build_notifier")
@patch("src.handler.load_config", return_value=VALID_CONFIG)
def test_lambda_handler_uses_scheduled_time_from_event(mock_load, mock_notifier, mock_clients, monday_0300):
    """Handler uses the time passed by the Scheduler event instead of wall clock."""
    mock_notifier.return_value = MagicMock()
    mock_clients.return_value = MagicMock()

    with patch("src.handler.ServiceFactory") as mock_factory_cls:
        mock_factory = MagicMock()
        mock_factory_cls.return_value = mock_factory
        mock_handler = MagicMock()
        mock_handler.run.return_value = []
        mock_factory.create.return_value = mock_handler

        # Event carries the scheduled time; no `now` injected
        event = {"time": "22:00"}
        context = MagicMock()

        with patch("src.handler.datetime", wraps=_dt.datetime) as mock_datetime:
            mock_datetime.now.return_value = monday_0300
            result = lambda_handler(event, context)

        assert result["services_processed"] == 2
        assert mock_factory.create.call_count == 2


def test_resolve_now_uses_local_day_from_configured_timezone():
    """`_resolve_now` with a tz uses the day in that timezone and the event time."""
    aware_now = _dt.datetime(2024, 1, 1, 23, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
    with patch("src.handler.datetime", wraps=_dt.datetime) as mock_datetime:
        mock_datetime.now.return_value = aware_now
        resolved = _resolve_now({"time": "23:00"}, ZoneInfo("America/Sao_Paulo"))
    assert resolved is not None
    assert resolved.weekday() == 0  # Monday
    assert resolved.strftime("%H:%M") == "23:00"