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
        for config in self._list_replication_configs():
            if config.get("Status") in RUNNING_STATUSES:
                configs.append(config["ReplicationConfigArn"])
        return configs

    def shutdown_item(self, item_id: str) -> None:
        self._dms.stop_replication(ReplicationConfigArn=item_id)

    def _list_replication_configs(self) -> List[dict]:
        configs: List[dict] = []
        kwargs: dict[str, Any] = {}
        while True:
            page = self._dms.describe_replication_configs(**kwargs)
            configs.extend(page.get("ReplicationConfigs", []))
            if not page.get("Marker"):
                return configs
            kwargs["Marker"] = page["Marker"]
