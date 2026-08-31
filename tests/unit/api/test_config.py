"""Coldline — Task 1.1.

===================

File:              tests/unit/api/test_config.py
Component:         Unit tests — Test Config
Purpose:           Unit tests for the API configuration boundary.
Interacts With:    One isolated source responsibility
Sprint/Task:       Sprint 1 — Project 1 / Task 1.1
Concepts:          Fast feedback, failure paths, state invariants
Tools:             Python 3.12, pytest, Redis, Pydantic
"""

import pytest
from pydantic import ValidationError

from api.config import ApiSettings


def test_api_settings_require_dependency_addresses(monkeypatch: pytest.MonkeyPatch) -> None:
    """The API must not silently invent working dependency credentials."""
    monkeypatch.delenv("COLDLINE_DATABASE_URL", raising=False)
    monkeypatch.delenv("COLDLINE_REDIS_URL", raising=False)
    monkeypatch.delenv("COLDLINE_OTEL_ENDPOINT", raising=False)

    with pytest.raises(ValidationError):
        ApiSettings(_env_file=None)


def test_api_settings_parse_the_compose_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """The protected config module must validate the supplied Compose values."""
    monkeypatch.setenv("COLDLINE_DATABASE_URL", "postgresql://user:pass@postgres:5432/coldline")
    monkeypatch.setenv("COLDLINE_REDIS_URL", "redis://redis:6379/0")
    monkeypatch.setenv("COLDLINE_OTEL_ENDPOINT", "http://jaeger:4317")

    settings = ApiSettings(_env_file=None)

    assert settings.service_name == "coldline-api"
    assert settings.stream_name == "coldline.exception.jobs"
