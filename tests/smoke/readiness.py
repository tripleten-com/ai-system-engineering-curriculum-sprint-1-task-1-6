"""Coldline.

===================

File:              tests/smoke/readiness.py
Component:         Smoke tests — Readiness
Purpose:           Check the documented ready state for every runtime surface.
Interacts With:    Running Docker Compose services
Sprint/Task:       Sprint 1 — Project 1
Concepts:          Readiness, provisioning, bounded diagnostics
Tools:             Python 3.12, pytest, Prometheus
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Protocol

import httpx

from tests.runtime_config import host_port

ENDPOINTS = {
    "api": f"http://localhost:{host_port('COLDLINE_API_HOST_PORT', 8000)}/health/ready",
    "grafana": f"http://localhost:{host_port('COLDLINE_GRAFANA_HOST_PORT', 3000)}/api/health",
    "prometheus": f"http://localhost:{host_port('COLDLINE_PROMETHEUS_HOST_PORT', 9090)}/-/ready",
    "jaeger": f"http://localhost:{host_port('COLDLINE_JAEGER_HOST_PORT', 16686)}/",
}
ROOT = Path(__file__).resolve().parents[2]


class HttpReader(Protocol):
    """Describe the HTTP operation needed by the readiness loop."""

    def get(self, endpoint: str) -> httpx.Response:
        """Return one HTTP response."""
        ...


def _wait_for_endpoint(
    client: HttpReader,
    endpoint: str,
    *,
    attempts: int = 60,
    delay: float = 0.5,
) -> str | None:
    """Poll one endpoint until it succeeds or the bounded attempts expire."""
    last_error = "endpoint did not answer"
    for attempt in range(attempts):
        try:
            response = client.get(endpoint)
            response.raise_for_status()
            return None
        except httpx.HTTPError as exc:
            last_error = str(exc)
            if attempt + 1 < attempts:
                time.sleep(delay)
    return last_error


def main() -> int:
    """Return success when all documented endpoints answer successfully."""
    failures: list[str] = []
    with httpx.Client(timeout=5.0, follow_redirects=True) as client:
        for component, endpoint in ENDPOINTS.items():
            error = _wait_for_endpoint(client, endpoint)
            if error is not None:
                failures.append(f"{component}: {error}")
    worker_error = _worker_health_error()
    if worker_error is not None:
        failures.append(f"worker: {worker_error}")
    if failures:
        print("Ready-state check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print(
        "Coldline ready: API, worker dependencies, Grafana, Prometheus, and Jaeger are available."
    )
    return 0


def _worker_health_error(*, attempts: int = 60, delay: float = 0.5) -> str | None:
    """Return an error unless Compose reports a dependency-ready worker."""
    last_error = "container is not running"
    for attempt in range(attempts):
        result = subprocess.run(
            ["docker", "compose", "--profile", "observability", "ps", "--format", "json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            last_error = result.stderr.strip() or "Docker Compose status failed"
        else:
            records = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
            worker = next((record for record in records if record.get("Service") == "worker"), None)
            if worker is not None:
                if worker.get("State") == "running" and worker.get("Health") == "healthy":
                    return None
                last_error = f"container state={worker.get('State')} health={worker.get('Health')}"
        if attempt + 1 < attempts:
            time.sleep(delay)
    return last_error


if __name__ == "__main__":
    raise SystemExit(main())
