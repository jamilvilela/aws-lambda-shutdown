"""ECS handler."""

from __future__ import annotations

from typing import Any, List

from .base import ServiceHandler


class ECSHandler(ServiceHandler):
    service_name = "ecs"

    def __init__(self, ecs: Any) -> None:
        self._ecs = ecs

    def list_active_items(self) -> List[str]:
        items: List[str] = []
        clusters = self._list_clusters()
        for cluster in clusters:
            services = self._list_services(cluster)
            if not services:
                continue
            descriptions = self._ecs.describe_services(cluster=cluster, services=services)
            for svc in descriptions.get("services", []):
                if svc.get("runningCount", 0) > 0:
                    items.append(f"{cluster}|{svc['serviceName']}")
        return items

    def shutdown_item(self, item_id: str) -> None:
        cluster, service = item_id.split("|", 1)
        self._ecs.update_service(cluster=cluster, service=service, desiredCount=0)

    def _list_clusters(self) -> List[str]:
        clusters: List[str] = []
        paginator = self._ecs.get_paginator("list_clusters")
        for page in paginator.paginate():
            clusters.extend(page.get("clusterArns", []))
        return clusters

    def _list_services(self, cluster: str) -> List[str]:
        services: List[str] = []
        paginator = self._ecs.get_paginator("list_services")
        for page in paginator.paginate(cluster=cluster):
            services.extend(page.get("serviceArns", []))
        return services