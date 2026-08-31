"""Coldline — Task 1.1.

===================

File:              tests/unit/test_bootstrap.py
Component:         Unit tests — Bootstrap
Purpose:           Keep the pinned uv bootstrap re-runnable without network access.
Interacts With:    infra/scripts/bootstrap.py
Sprint/Task:       Sprint 1 — Project 1 / Task 1.1
Concepts:          Reproducibility, idempotency, version parsing
Tools:             Python 3.12, pytest
"""

import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

BOOTSTRAP_PATH = Path(__file__).resolve().parents[2] / "infra/scripts/bootstrap.py"
SPEC = importlib.util.spec_from_file_location("coldline_bootstrap", BOOTSTRAP_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("bootstrap module could not be loaded")
bootstrap = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap)


def test_uv_version_parser_ignores_build_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Recognize the pinned version even when uv prints build metadata."""
    result = SimpleNamespace(stdout="uv 0.11.8 (0e961dd9a 2026-04-27)\n")
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: result)

    assert bootstrap._version(Path("uv")) == bootstrap.UV_VERSION
