"""RDS handler."""

from __future__ import annotations

from typing import Any, List

from .base import ServiceHandler

RUNNING_STATUSES = {"available", "starting", "backing-up", "stopping"}


class RDSHandler(ServiceHandler):
    service_name = "rds"

    def __init__(self, rds: Any) -> None:
        self._rds = rds

    def list_active_items(self) -> List[str]:
        identifiers: List[str] = []
        paginator = self._rds.get_paginator("describe_db_instances")
        for page in paginator.paginate():
            for db in page.get("DBInstances", []):
                if db.get("DBInstanceStatus") in RUNNING_STATUSES:
                    identifiers.append(db["DBInstanceIdentifier"])
        return identifiers

    def shutdown_item(self, item_id: str) -> None:
        self._rds.stop_db_instance(DBInstanceIdentifier=item_id)