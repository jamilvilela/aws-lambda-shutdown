"""Aurora handler."""

from __future__ import annotations

from typing import Any, List

from .base import ServiceHandler

RUNNING_STATUSES = {"available", "starting", "backing-up", "stopping"}


class AuroraHandler(ServiceHandler):
    service_name = "aurora"

    def __init__(self, rds: Any) -> None:
        self._rds = rds

    def list_active_items(self) -> List[str]:
        identifiers: List[str] = []
        paginator = self._rds.get_paginator("describe_db_clusters")
        for page in paginator.paginate():
            for cluster in page.get("DBClusters", []):
                if cluster.get("Status") in RUNNING_STATUSES:
                    identifiers.append(cluster["DBClusterIdentifier"])
        return identifiers

    def shutdown_item(self, item_id: str) -> None:
        self._rds.stop_db_cluster(DBClusterIdentifier=item_id)