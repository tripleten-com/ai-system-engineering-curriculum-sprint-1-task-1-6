"""Coldline — Task 1.2.

===================

File:              tests/contract/test_authoring_contract.py
Component:         Authoring verifier contract
Purpose:           Runs the same structural gate used before export.
Interacts With:    tests.contract.authoring and the complete Task tree
Sprint/Task:       Sprint 1 — Project 1 / Task 1.2
Concepts:          Dependency direction, configuration ownership, export hygiene
Tools:             Python 3.12, pytest
"""

import re
from pathlib import Path

from tests.contract import authoring
from tests.contract.submission_validation import _changed_paths

TASK_ROOT = Path(__file__).resolve().parents[2]
BANNER_PATTERN = re.compile(r"Coldline — Task \d+\.\d+")
# Task 1.6's own boundary: a submitted PR may touch only the answer sheet and the decision-evidence
# record. Keep this in sync with submission_validation.ALLOWED_PATHS.
SUBMISSION_DIFF_ALLOWLIST = frozenset(
    {"submission.yaml", "docs/student/decision-evidence-record.md"}
)
HEADER_FIELDS = (
    "File:",
    "Component:",
    "Purpose:",
    "Interacts With:",
    "Sprint/Task:",
    "Concepts:",
    "Tools:",
)
COMMENTABLE_CONFIGURATION = (
    ".devcontainer/post-create.sh",
    ".devcontainer/start-stack.sh",
    ".dockerignore",
    ".env.example",
    ".gitattributes",
    ".github/workflows/task.yml",
    ".gitignore",
    "compose.yaml",
    "infra/containers/api.Dockerfile",
    "infra/containers/worker.Dockerfile",
    "infra/observability/grafana/dashboards/provider.yml",
    "infra/observability/grafana/datasources/datasources.yml",
    "infra/observability/prometheus.yml",
    "infra/postgres/001_opening_checkpoint.sql",
    "infra/scripts/bootstrap.ps1",
    "infra/scripts/bootstrap.sh",
    "infra/scripts/preflight.ps1",
    "infra/scripts/preflight.sh",
    "pyproject.toml",
    "submission-sample.yaml",
    "submission.yaml",
)


def test_current_snapshot_satisfies_the_authoring_contract() -> None:
    """Fail when a protected repository invariant drifts."""
    assert authoring.main() == 0


def test_python_files_have_the_student_navigation_banner() -> None:
    """Catch a source file that gives students no ownership or purpose context."""
    failures: list[str] = []
    roots = [TASK_ROOT / "src", TASK_ROOT / "tests", TASK_ROOT / "infra/scripts"]
    for root in roots:
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8")
            header = text[:1200]
            missing = [field for field in HEADER_FIELDS if field not in header]
            if not BANNER_PATTERN.search(header):
                missing.insert(0, "Coldline — Task <sprint>.<task>")
            if missing:
                failures.append(f"{path.relative_to(TASK_ROOT)}: {', '.join(missing)}")

    assert failures == []


def test_submission_change_stays_within_the_permitted_diff() -> None:
    """Catch a submitted change that reaches outside Task 1.6's two-path submission boundary."""
    changed = set(_changed_paths(TASK_ROOT))
    assert changed <= SUBMISSION_DIFF_ALLOWLIST


def test_commentable_configuration_files_explain_their_role() -> None:
    """Catch operational files that provide configuration without context."""
    banner = re.compile(r"Coldline - Task \d+\.\d+")
    missing = []
    for relative in COMMENTABLE_CONFIGURATION:
        text = (TASK_ROOT / relative).read_text(encoding="utf-8")
        if not banner.search(text[:1000]):
            missing.append(relative)

    assert missing == []
