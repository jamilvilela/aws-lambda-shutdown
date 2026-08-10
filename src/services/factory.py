"""Service handler factory with dependency injection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Type

from .base import ServiceHandler
from .registry import SERVICE_HANDLERS


class UnknownServiceError(Exception):
    """Raised when a service is not registered."""


@dataclass
class ServiceClients:
    """Container of AWS clients injected into handlers."""

    ec2: Any = None
    rds: Any = None
    ecs: Any = None
    glue: Any = None
    batch: Any = None
    dms: Any = None


_HANDLER_CLIENT = {
    "ec2": "ec2",
    "rds": "rds",
    "ecs": "ecs",
    "aurora": "rds",
    "batch": "batch",
    "dms": "dms",
    "dms-serverless": "dms",
}


class ServiceFactory:
    """Creates service handlers based on the service name."""

    def __init__(
        self, clients: ServiceClients, registry: Dict[str, Type[ServiceHandler]] | None = None
    ) -> None:
        self._clients = clients
        self._registry = registry or SERVICE_HANDLERS

    def create(self, service_name: str) -> ServiceHandler:
        handler_cls = self._registry.get(service_name)
        if handler_cls is None:
            raise UnknownServiceError(f"Unknown service: {service_name}")
        if handler_cls.__name__ == "GlueHandler":
            return handler_cls(glue=self._clients.glue, service_name=service_name)
        attr = _HANDLER_CLIENT.get(service_name)
        if attr is None:
            raise UnknownServiceError(f"No client mapping for service: {service_name}")
        return handler_cls(**{attr: getattr(self._clients, attr)})