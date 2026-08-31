"""Coldline — Task 1.6.

===================

File:              tests/contract/submission_validation.py
Component:         Contract tests — Submission Validation
Purpose:           Validate this Task's submission answers and advisory change paths.
Interacts With:    Published interfaces and repository boundaries
Sprint/Task:       Sprint 1 — Project 1 / Task 1.6
Concepts:          Compatibility, ownership, export safety
Tools:             Python 3.12, pytest
"""

import json
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from jsonschema import Draft202012Validator

# Future tasks: update this set to match your own README's student-editable paths.
ALLOWED_PATHS = frozenset(
    {
        "submission.yaml",
        "docs/student/decision-evidence-record.md",
    }
)
# Set to a relative path if this Task also has a second student-editable evidence file.
BASELINE_PATH: str | None = "docs/student/decision-evidence-record.md"
# If BASELINE_PATH is set, update these to match that file's own template placeholder text.
BASELINE_MARKERS = frozenset(
    {
        '| e.g. "Worker concurrency is the primary bottleneck"',
    }
)


class SubmissionError(ValueError):
    """Report one actionable public-verification failure."""


def main(root: Path | None = None, *, changed_paths: list[str] | None = None) -> int:
    """Validate the current answer sheet and protected-path boundary.

    The optional arguments keep this entrypoint testable without changing the
    process working directory or creating a temporary Git repository.
    """
    task_root = Path.cwd() if root is None else root
    try:
        validate_submission(
            task_root / "submission.yaml",
            task_root / "docs/contracts/submission.schema.json",
            sample_path=task_root / "submission-sample.yaml",
        )
        if BASELINE_PATH is not None:
            validate_baseline(task_root / BASELINE_PATH)
        validate_changed_paths(
            _changed_paths(task_root) if changed_paths is None else changed_paths
        )
    except (SubmissionError, RuntimeError) as exc:
        print(f"verification failed: {exc}", file=sys.stderr)
        return 1
    print("Submission verification passed.")
    return 0


def validate_submission(
    submission_path: Path,
    schema_path: Path,
    *,
    sample_path: Path | None = None,
) -> None:
    """Validate YAML shape, placeholders, schema, and sample-copy behavior."""
    submission = _load_one_document(submission_path)
    answers = submission.get("answers") if isinstance(submission, dict) else None
    if not isinstance(answers, dict):
        raise SubmissionError("answers must be one mapping")

    for field, value in answers.items():
        if isinstance(value, str) and (not value.strip() or "Replace this line" in value):
            raise SubmissionError(f"answers.{field} is incomplete")

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(submission), key=lambda error: list(error.path)
    )
    if errors:
        error = errors[0]
        location = ".".join(str(part) for part in error.absolute_path) or "submission"
        raise SubmissionError(f"{location}: {error.message}")

    if sample_path is not None and submission == _load_one_document(sample_path):
        raise SubmissionError("submission must not copy the fictional sample answers")


def validate_baseline(baseline_path: Path) -> None:
    """Reject the untouched evidence template without grading its prose."""
    text = baseline_path.read_text(encoding="utf-8")
    remaining = sorted(marker for marker in BASELINE_MARKERS if marker in text)
    if remaining:
        raise SubmissionError(f"{baseline_path.name} still contains template markers")


def validate_changed_paths(paths: list[str]) -> None:
    """Reject changed paths outside this Task's student-editable surfaces."""
    normalized = {PurePosixPath(path.replace("\\", "/")).as_posix() for path in paths}
    protected = sorted(normalized - ALLOWED_PATHS)
    if protected:
        raise SubmissionError(f"protected path changed: {', '.join(protected)}")


def _changed_paths(root: Path) -> list[str]:
    """Return changes since this checkout's published baseline commit."""
    try:
        repository_root = Path(
            subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        ).resolve()
        if root.resolve() != repository_root:
            # The authoring snapshot is nested. Only a generated repository's
            # own history defines student changes.
            return []
        baseline = _baseline_commit(repository_root)
        result = subprocess.run(
            ["git", "diff", "--name-only", baseline],
            cwd=repository_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("Git history is unavailable for protected-path validation") from exc
    return [line for line in result.stdout.splitlines() if line]


def _baseline_commit(repository_root: Path) -> str:
    """Return the commit a student's changes are measured against.

    Student work happens ahead of the repository's published `main` - on a
    branch, or as uncommitted edits - and later export refreshes legitimately
    keep advancing `main` after a student has already forked from it. The
    protected boundary is therefore the commit a student actually started
    from (their merge-base with `main`), not the repository's very first
    commit, which an export refresh may since have moved past.
    """
    for candidate in ("origin/main", "main"):
        probe = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", candidate],
            cwd=repository_root,
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", candidate],
                cwd=repository_root,
                check=True,
                capture_output=True,
                text=True,
            )
            return merge_base.stdout.strip()
    # No published `main` is reachable (e.g. an unpublished staging export) -
    # fall back to the repository's single root commit.
    roots = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if len(roots) != 1:
        raise RuntimeError("repository must have exactly one protected root commit")
    return roots[0]


def _load_one_document(path: Path) -> dict[str, Any]:
    """Load exactly one safe YAML mapping."""
    try:
        documents = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
    except yaml.YAMLError as exc:
        raise SubmissionError(f"{path.name} must contain valid YAML") from exc
    if len(documents) != 1 or not isinstance(documents[0], dict):
        raise SubmissionError(f"{path.name} must contain exactly one YAML mapping")
    return documents[0]


if __name__ == "__main__":
    raise SystemExit(main())
