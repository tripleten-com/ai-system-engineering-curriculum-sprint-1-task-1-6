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

import pytest

from loadtest.model_provider_latency import BASELINE_LATENCY_MS, injected_latency_ms

# Not a Docker-dependent check, but graded only as part of `poe verify`'s runtime phase
# (mirrors tests/contract/test_telemetry_repair.py's use of this marker to keep the
# static `poe author-verify` gate green on an unsolved checkpoint).
pytestmark = pytest.mark.runtime


def test_injected_latency_adds_exactly_300ms() -> None:
    """The latency-injected run must add exactly +300ms over the measured baseline."""
    assert injected_latency_ms() == BASELINE_LATENCY_MS + 300
