"""Service handler registry."""

from __future__ import annotations

from typing import Dict, Type

from .aurora_handler import AuroraHandler
from .batch_handler import BatchHandler
from .base import ServiceHandler
from .dms_handler import DMSHandler
from .dms_serverless_handler import DMSServerlessHandler
from .ec2_handler import EC2Handler
from .ecs_handler import ECSHandler
from .glue_handler import GlueHandler
from .rds_handler import RDSHandler

SERVICE_HANDLERS: Dict[str, Type[ServiceHandler]] = {
    "ec2": EC2Handler,
    "rds": RDSHandler,
    "ecs": ECSHandler,
    "glue-batch": GlueHandler,
    "glue-stream": GlueHandler,
    "aurora": AuroraHandler,
    "batch": BatchHandler,
    "dms": DMSHandler,
    "dms-serverless": DMSServerlessHandler,
}