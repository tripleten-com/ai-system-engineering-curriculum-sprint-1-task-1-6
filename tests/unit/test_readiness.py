"""Coldline.

===================

File:              tests/unit/test_readiness.py
Component:         Unit tests — Test Readiness
Purpose:           Tests for condition-based readiness checks.
Interacts With:    One isolated source responsibility
Sprint/Task:       Sprint 1 — Project 1
Concepts:          Fast feedback, failure paths, state invariants
Tools:             Python 3.12, pytest
"""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest

TASK_ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "coldline_ready", TASK_ROOT / "tests/smoke/readiness.py"
)
assert SPEC is not None and SPEC.loader is not None
READY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(READY)


class TransientClient:
    """Fail one request before returning a healthy response."""

    def __init__(self) -> None:
        """Initialize the call count."""
        self.calls = 0

    def get(self, endpoint: str) -> httpx.Response:
        """Return a response only after one transient transport failure."""
        self.calls += 1
        if self.calls == 1:
            raise httpx.ConnectError("transient reset")
        request = httpx.Request("GET", endpoint)
        return httpx.Response(200, request=request)


def test_readiness_retries_a_transient_transport_failure() -> None:
    """A just-started endpoint may reset once without failing the ready contract."""
    client = TransientClient()

    error = READY._wait_for_endpoint(client, "http://example.test/health", attempts=2, delay=0)

    assert error is None
    assert client.calls == 2


def test_readiness_runs_compose_from_the_task_root() -> None:
    """Keep Compose discovery explicit after the readiness module moves."""
    assert READY.ROOT == TASK_ROOT


def test_worker_readiness_requires_compose_health(monkeypatch: pytest.MonkeyPatch) -> None:
    """The public ready gate must reject a running but unhealthy worker."""
    result = SimpleNamespace(
        returncode=0,
        stdout='{"Service":"worker","State":"running","Health":"unhealthy"}\n',
        stderr="",
    )
    monkeypatch.setattr(READY.subprocess, "run", lambda *args, **kwargs: result)

    assert READY._worker_health_error(attempts=1, delay=0) == (
        "container state=running health=unhealthy"
    )
