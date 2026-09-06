"""Coldline.

===================

File:              tests/contract/test_ports.py
Component:         Contract tests — Test Ports
Purpose:           Contract tests for the five accepted application ports.
Interacts With:    Published interfaces and repository boundaries
Sprint/Task:       Sprint 1 — Project 1
Concepts:          Compatibility, ownership, export safety
Tools:             Python 3.12, pytest, Redis
"""

import inspect
from typing import Any, cast

import ports
from adapters.model import DeterministicModelProvider
from adapters.queue import RedisJobQueue


def test_exactly_five_application_ports_are_defined_once() -> None:
    """The core package must expose exactly the five accepted provider boundaries."""
    protocol_names = {
        name
        for name, value in inspect.getmembers(ports, inspect.isclass)
        if not name.startswith("_") and getattr(value, "_is_protocol", False)
    }
    assert protocol_names == {
        "JobQueue",
        "ModelProvider",
        "ObjectStore",
        "Retriever",
        "SecretProvider",
    }


def test_active_adapters_satisfy_their_provider_neutral_port_shapes() -> None:
    """Active implementations must expose every operation owned by their core ports."""
    redis_queue = RedisJobQueue(
        cast(Any, object()),
        stream="contract-stream",
        group="contract-group",
        consumer="contract-consumer",
    )

    assert isinstance(DeterministicModelProvider(latency_ms=0), ports.ModelProvider)
    assert isinstance(redis_queue, ports.JobQueue)
