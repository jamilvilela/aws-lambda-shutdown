"""Tests for SNS notifier."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.notifier import SNSNotifier
from src.services.base import Failure


def test_notify_failures_publishes():
    sns = MagicMock()
    notifier = SNSNotifier(sns, "arn:aws:sns:us-east-1:123:test-topic")
    failures = [
        Failure(service="ec2", item="i-1", reason="timeout"),
        Failure(service="rds", item="db-1", reason="permission denied"),
    ]
    notifier.notify_failures(failures, datetime(2024, 1, 1, 3, 0))
    sns.publish.assert_called_once()
    args = sns.publish.call_args.kwargs
    assert args["TopicArn"] == "arn:aws:sns:us-east-1:123:test-topic"
    assert "ec2" in args["Message"]
    assert "rds" in args["Message"]
    assert "timeout" in args["Message"]
    assert "permission denied" in args["Message"]
    assert "2024-01-01T03:00:00" in args["Message"]


def test_no_failures_no_publish():
    sns = MagicMock()
    notifier = SNSNotifier(sns, "arn:aws:sns:us-east-1:123:test-topic")
    notifier.notify_failures([])
    sns.publish.assert_not_called()


def test_notify_error_publishes():
    sns = MagicMock()
    notifier = SNSNotifier(sns, "arn:aws:sns:us-east-1:123:test-topic")
    notifier.notify_error("Config file not found", datetime(2024, 1, 1, 3, 0))
    sns.publish.assert_called_once()
    args = sns.publish.call_args.kwargs
    assert args["Subject"] == "[aws-lambda-shutdown] Execution error"
    assert "Config file not found" in args["Message"]
    assert "2024-01-01T03:00:00" in args["Message"]