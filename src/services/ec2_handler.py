"""EC2 service handler."""

from __future__ import annotations

from typing import Any, List

from .base import ServiceHandler

RUNNING_STATES = {"running", "pending", "stopping"}


class EC2Handler(ServiceHandler):
    service_name = "ec2"

    def __init__(self, ec2: Any) -> None:
        self._ec2 = ec2

    def list_active_items(self) -> List[str]:
        instances: List[str] = []
        paginator = self._ec2.get_paginator("describe_instances")
        for page in paginator.paginate(
            Filters=[{"Name": "instance-state-name", "Values": sorted(RUNNING_STATES)}]
        ):
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instances.append(instance["InstanceId"])
        return instances

    def shutdown_item(self, item_id: str) -> None:
        self._ec2.stop_instances(InstanceIds=[item_id], Force=True)