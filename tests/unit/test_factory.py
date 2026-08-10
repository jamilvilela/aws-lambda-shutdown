"""Tests for service factory and registry."""

from unittest.mock import MagicMock

import pytest

from src.services.factory import ServiceFactory, ServiceClients, UnknownServiceError
from src.services.registry import SERVICE_HANDLERS
from src.services.ec2_handler import EC2Handler
from src.services.rds_handler import RDSHandler
from src.services.ecs_handler import ECSHandler
from src.services.glue_handler import GlueHandler
from src.services.aurora_handler import AuroraHandler
from src.services.batch_handler import BatchHandler
from src.services.dms_handler import DMSHandler
from src.services.dms_serverless_handler import DMSServerlessHandler


def test_factory_creates_all_handlers():
    clients = ServiceClients(
        ec2=MagicMock(), rds=MagicMock(), ecs=MagicMock(),
        glue=MagicMock(), batch=MagicMock(), dms=MagicMock(),
    )
    factory = ServiceFactory(clients)

    assert isinstance(factory.create("ec2"), EC2Handler)
    assert isinstance(factory.create("rds"), RDSHandler)
    assert isinstance(factory.create("ecs"), ECSHandler)
    assert isinstance(factory.create("glue-batch"), GlueHandler)
    assert isinstance(factory.create("glue-stream"), GlueHandler)
    assert isinstance(factory.create("aurora"), AuroraHandler)
    assert isinstance(factory.create("batch"), BatchHandler)
    assert isinstance(factory.create("dms"), DMSHandler)
    assert isinstance(factory.create("dms-serverless"), DMSServerlessHandler)


def test_factory_unknown_service():
    clients = ServiceClients()
    factory = ServiceFactory(clients)
    with pytest.raises(UnknownServiceError):
        factory.create("unknown-service")


def test_registry_contains_all_services():
    expected = {
        "ec2", "rds", "ecs", "glue-batch", "glue-stream",
        "aurora", "batch", "dms", "dms-serverless",
    }
    assert set(SERVICE_HANDLERS.keys()) == expected