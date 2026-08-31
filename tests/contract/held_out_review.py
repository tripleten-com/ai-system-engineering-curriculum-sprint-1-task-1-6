"""Coldline — Task 1.6.

===================

File:              tests/contract/held_out_review.py
Component:         Contract — Held-out review
Purpose:           Replay a held-out scenario and grade the result without exposing expected values.
Interacts With:    The live API, a runtime-supplied held-out scenario definition
Sprint/Task:       Sprint 1 — Project 1 / Task 1.6
Concepts:          Held-out evaluation
Tools:             Python 3.12, httpx
"""

import json
import os
import sys
import time
import uuid
from datetime import UTC, datetime

import httpx


def run_held_out_check(scenario_json: str, api_base_url: str) -> bool:
    """Submit the held-out reading and confirm the system reaches the expected state.

    Returns True/False only — never logs or returns the scenario's expected values,
    so a student reading CI output cannot recover the held-out answer key.
    """
    scenario = json.loads(scenario_json)
    reading_id = f"held-out-{uuid.uuid4().hex}"
    with httpx.Client(base_url=api_base_url, timeout=10.0) as client:
        response = client.post(
            "/api/v1/readings",
            json={
                "reading_id": reading_id,
                "shipment_id": f"held-out-shipment-{uuid.uuid4().hex}",
                "temperature_c": scenario["temperature_c"],
                "allowed_min_c": scenario["allowed_min_c"],
                "allowed_max_c": scenario["allowed_max_c"],
                "recorded_at": datetime.now(UTC).isoformat(),
            },
        )
        if response.status_code != 202:
            return False
        exception_id = response.json().get("exception_id")
        for _ in range(20):
            status_response = client.get(f"/api/v1/exceptions/{exception_id}")
            if status_response.status_code == 200:
                state = status_response.json().get("state")
                if state == scenario["expected_state"]:
                    return True
                if state == "FAILED":
                    return False
            time.sleep(0.5)
    return False


if __name__ == "__main__":
    # The scenario arrives through the environment, never as an argument: a command-line argument is
    # readable from /proc/<pid>/cmdline by any other process for as long as this one lives.
    scenario_env = os.environ.get("HELD_OUT_SCENARIO", "")
    api_base_url_env = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    passed = run_held_out_check(scenario_env, api_base_url_env)
    print("HELD_OUT_CHECK_PASSED" if passed else "HELD_OUT_CHECK_FAILED")
    sys.exit(0 if passed else 1)
