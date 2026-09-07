"""Coldline.

===================

File:              tests/contract/test_load_harness.py
Component:         Contract — Load harness
Purpose:           Grade the Task 1.4 latency-injection assignment.
Interacts With:    loadtest/model_provider_latency.py
Sprint/Task:       Sprint 1 — Project 1
Concepts:          Controlled experiments
Tools:             Python 3.12, pytest
"""

import json
import subprocess

import httpx
import pytest

from loadtest.model_provider_latency import (
    BASELINE_LATENCY_MS,
    INJECTED_DELAY_MS,
    injected_latency_ms,
)
from tests.e2e.test_exception_workflow import (
    _load_unique_reading,
    _wait_for_service_evidence,
    _wait_for_terminal,
)
from tests.runtime_config import host_port
from worker.config import WorkerSettings

TRUSTED_BASELINE_LATENCY_MS = WorkerSettings.model_fields["model_latency_ms"].default

# The constant and running-worker checks belong to the runtime verification phase.
# The static authoring gate therefore remains usable on an unsolved checkpoint.
pytestmark = pytest.mark.runtime


def test_injected_latency_adds_exactly_300ms() -> None:
    """The latency-injected run must add exactly +300ms over the measured baseline."""
    assert BASELINE_LATENCY_MS == TRUSTED_BASELINE_LATENCY_MS
    assert INJECTED_DELAY_MS == 300
    assert injected_latency_ms() == TRUSTED_BASELINE_LATENCY_MS + 300


def test_running_worker_has_applied_latency_override() -> None:
    """A changed source constant cannot satisfy an unchanged worker container."""
    result = subprocess.run(
        [
            "docker",
            "compose",
            "--profile",
            "observability",
            "exec",
            "-T",
            "worker",
            "python",
            "-c",
            "from worker.config import WorkerSettings; import json; "
            "print(json.dumps(WorkerSettings().model_latency_ms))",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout) == TRUSTED_BASELINE_LATENCY_MS + 300, (
        "Apply the latency override to the running worker before verification."
    )


def test_running_provider_span_observes_injected_delay() -> None:
    """Check the actual provider call rather than request or queue-wait duration."""
    _, reading = _load_unique_reading()
    port = host_port("COLDLINE_API_HOST_PORT", 8000)
    with httpx.Client(base_url=f"http://localhost:{port}", timeout=5.0) as client:
        response = client.post("/api/v1/readings", json=reading)
        assert response.status_code == 202
        accepted = response.json()
        _wait_for_terminal(client, accepted["status_url"])
    traces = _wait_for_service_evidence("coldline-worker", accepted["exception_id"])
    durations_ms = [
        span["duration"] / 1000
        for item in traces
        for span in item["spans"]
        if span["operationName"] == "model_provider.summarize"
        and any(
            tag["key"] == "coldline.exception_id" and tag["value"] == accepted["exception_id"]
            for tag in span.get("tags", [])
        )
    ]
    assert durations_ms, "The running provider call must be observable in Jaeger."
    # Scheduler noise can add delay; the configuration check rejects other settings.
    assert min(durations_ms) >= TRUSTED_BASELINE_LATENCY_MS + 300 - 10
