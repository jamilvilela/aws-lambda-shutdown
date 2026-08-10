"""DMS Serverless handler."""

from __future__ import annotations

from typing import Any, List

from .base import ServiceHandler

RUNNING_STATUSES = {"running", "starting"}


class DMSServerlessHandler(ServiceHandler):
    service_name = "dms-serverless"

    def __init__(self, dms: Any) -> None:
        self._dms = dms

    def list_active_items(self) -> List[str]:
        configs: List[str] = []
        paginator = self._dms.get_paginator("describe_replication_configs")
        for page in paginator.paginate():
            for config in page.get("ReplicationConfigs", []):
                if config.get("Status") in RUNNING_STATUSES:
                    configs.append(config["ReplicationConfigArn"])
        return configs

    def shutdown_item(self, item_id: str) -> None:
        self._dms.stop_replication(ReplicationConfigArn=item_id)