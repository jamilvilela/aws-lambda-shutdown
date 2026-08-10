"""DMS handler (classic replication tasks and instances)."""

from __future__ import annotations

from typing import Any, List

from .base import ServiceHandler

RUNNING_TASK_STATUSES = {"running", "starting", "ready"}
RUNNING_INSTANCE_STATUSES = {"running", "available"}


class DMSHandler(ServiceHandler):
    service_name = "dms"

    def __init__(self, dms: Any) -> None:
        self._dms = dms

    def list_active_items(self) -> List[str]:
        items: List[str] = []
        for task in self._list_replication_tasks():
            if task.get("Status") in RUNNING_TASK_STATUSES:
                items.append(f"task:{task['ReplicationTaskArn']}")
        for instance in self._list_replication_instances():
            if instance.get("ReplicationInstanceStatus") in RUNNING_INSTANCE_STATUSES:
                items.append(f"instance:{instance['ReplicationInstanceArn']}")
        return items

    def shutdown_item(self, item_id: str) -> None:
        kind, arn = item_id.split(":", 1)
        if kind == "task":
            self._dms.stop_replication_task(ReplicationTaskArn=arn)
        elif kind == "instance":
            self._dms.stop_replication_instance(ReplicationInstanceArn=arn)
        else:
            raise ValueError(f"Unknown DMS item kind: {kind}")

    def _list_replication_tasks(self) -> List[dict]:
        tasks: List[dict] = []
        paginator = self._dms.get_paginator("describe_replication_tasks")
        for page in paginator.paginate():
            tasks.extend(page.get("ReplicationTasks", []))
        return tasks

    def _list_replication_instances(self) -> List[dict]:
        instances: List[dict] = []
        paginator = self._dms.get_paginator("describe_replication_instances")
        for page in paginator.paginate():
            instances.extend(page.get("ReplicationInstances", []))
        return instances