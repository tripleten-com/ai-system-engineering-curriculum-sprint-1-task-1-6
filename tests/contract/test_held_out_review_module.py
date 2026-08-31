"""Coldline — Task 1.6.

===================

File:              tests/contract/test_held_out_review_module.py
Component:         Contract — Held-out review dry run
Purpose:           Confirm the held-out check mechanism works, using a fake, non-secret scenario.
Interacts With:    tests.contract.held_out_review, the live API
Sprint/Task:       Sprint 1 — Project 1 / Task 1.6
Concepts:          Held-out evaluation
Tools:             Python 3.12, pytest, httpx
"""

import json

import pytest

from tests.contract.held_out_review import run_held_out_check
from tests.runtime_config import host_port

pytestmark = pytest.mark.runtime


def test_held_out_check_mechanism_with_a_fake_scenario() -> None:
    """Confirm the held-out mechanism reaches the expected state for a fake scenario."""
    fake_scenario = json.dumps(
        {
            "temperature_c": 30.0,
            "allowed_min_c": 0.0,
            "allowed_max_c": 10.0,
            "expected_state": "COMPLETED",
        }
    )
    api_port = host_port("COLDLINE_API_HOST_PORT", 8000)
    base_url = f"http://localhost:{api_port}"
    assert run_held_out_check(fake_scenario, base_url)
