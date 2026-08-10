"""Base classes for service handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class Failure:
    """A single shutdown failure."""

    service: str
    item: str
    reason: str


class ServiceHandler(ABC):
    """Interface for a service shutdown handler."""

    service_name: str = ""

    @abstractmethod
    def list_active_items(self) -> List[str]:
        """Return identifiers of all active items."""

    @abstractmethod
    def shutdown_item(self, item_id: str) -> None:
        """Forcibly shut down a single item. Raises on failure."""

    def run(self) -> List[Failure]:
        """Shut down all active items and collect failures."""
        failures: List[Failure] = []
        for item in self.list_active_items():
            try:
                self.shutdown_item(item)
            except Exception as exc:  # noqa: BLE001
                failures.append(Failure(service=self.service_name, item=item, reason=str(exc)))
        return failures