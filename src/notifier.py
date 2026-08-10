"""SNS notifier."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List

from .services.base import Failure


class SNSNotifier:
    """Publishes failure notifications to an SNS topic."""

    def __init__(self, sns: Any, topic_arn: str) -> None:
        self._sns = sns
        self._topic_arn = topic_arn

    def notify_failures(self, failures: List[Failure], execution_time: datetime | None = None) -> None:
        if not failures:
            return
        execution_time = execution_time or datetime.now()
        subject = f"[aws-lambda-shutdown] Shutdown failure - {len(failures)} item(s)"
        body = self._build_body(failures, execution_time)
        self._sns.publish(TopicArn=self._topic_arn, Subject=subject, Message=body)

    def notify_error(self, message: str, execution_time: datetime | None = None) -> None:
        execution_time = execution_time or datetime.now()
        subject = "[aws-lambda-shutdown] Execution error"
        body = f"Execution time: {execution_time.isoformat()}\nError: {message}"
        self._sns.publish(TopicArn=self._topic_arn, Subject=subject, Message=body)

    @staticmethod
    def _build_body(failures: List[Failure], execution_time: datetime) -> str:
        lines = [f"Execution time: {execution_time.isoformat()}", ""]
        for failure in failures:
            lines.append(f"- Service: {failure.service}")
            lines.append(f"  Item: {failure.item}")
            lines.append(f"  Reason: {failure.reason}")
            lines.append("")
        return "\n".join(lines)