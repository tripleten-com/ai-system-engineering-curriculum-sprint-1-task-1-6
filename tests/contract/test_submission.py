"""Coldline.

===================

File:              tests/contract/test_submission.py
Component:         Contract tests — Test Submission
Purpose:           Tests for the public answer and path checks for this Task's submission.
Interacts With:    Published interfaces and repository boundaries
Sprint/Task:       Sprint 1 — Project 1
Concepts:          Compatibility, ownership, export safety
Tools:             Python 3.12, pytest
"""

from pathlib import Path

import pytest
import yaml

from tests.contract.submission_validation import (
    SubmissionError,
    _load_one_document,
    main,
    validate_baseline,
    validate_changed_paths,
    validate_submission,
)

ROOT = Path(__file__).parents[2]


def valid_answers() -> dict[str, object]:
    """Return a complete fictional answer sheet unrelated to Coldline outcomes."""
    return {
        "answers": {
            "decision_evidence_mappings": (
                "Fictional Recommendation: scale the fictional exception worker pool from 2 to 6 "
                "fictional processes. Fictional Mapping 1: fictional Task 1.1 baseline confirmed "
                "the fictional Redis Streams queue adapter as the only fictional asynchronous "
                "hop. Fictional Mapping 2: fictional Task 1.3 telemetry repair restored fictional "
                "end-to-end trace continuity for the fictional Task 1.4 load test. Fictional "
                "Mapping 3: fictional Task 1.4's fictional latency-injection experiment ruled out "
                "the fictional model provider as the bottleneck. Fictional Mapping 4: fictional "
                "Task 1.5 capacity math produced a fictional required concurrency of 3.3, rounded "
                "up with a fictional 30 percent safety margin to 6 fictional worker processes."
            ),
            "self_review_checklist": (
                "Fictional self-review complete: fictional evidence record checked against Tasks "
                "1.1-1.5, fictional submission scanned for secrets, and fictional presentation "
                "timed under 10 minutes."
            ),
            "limitations_statement": (
                "Fictional local Docker Compose tests cannot prove fictional multi-region "
                "latency, fictional production cost, or fictional long-term reliability; only "
                "fictional staging and production telemetry can confirm the fictional "
                "recommendation holds at real 10x traffic."
            ),
        }
    }


def test_complete_answer_shape_passes_public_validation(tmp_path: Path) -> None:
    """A complete direct-answer mapping must pass syntax and schema validation."""
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(valid_answers()), encoding="utf-8")

    validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_blank_template_fails_with_field_address(tmp_path: Path) -> None:
    """An untouched answer sheet must identify an incomplete field."""
    submission = tmp_path / "submission.yaml"
    submission.write_text((ROOT / "submission.yaml").read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.raises(SubmissionError, match="answers.decision_evidence_mappings"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_malformed_yaml_is_rejected(tmp_path: Path) -> None:
    """A syntactically invalid answer sheet must fail safely."""
    submission = tmp_path / "submission.yaml"
    submission.write_text("answers: [unterminated", encoding="utf-8")

    with pytest.raises(SubmissionError, match="restricted YAML"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_unexpected_answer_field_is_rejected(tmp_path: Path) -> None:
    """Fields outside the published direct-answer schema must fail validation."""
    answers = valid_answers()
    answer_mapping = answers["answers"]
    assert isinstance(answer_mapping, dict)
    answer_mapping["repair_hint"] = "not part of this Task's schema"
    submission = tmp_path / "submission.yaml"
    submission.write_text(yaml.safe_dump(answers), encoding="utf-8")

    with pytest.raises(SubmissionError, match="Additional properties"):
        validate_submission(submission, ROOT / "docs/contracts/submission.schema.json")


def test_exact_sample_copy_is_rejected(tmp_path: Path) -> None:
    """The fictional sample must not be accepted as a student submission."""
    submission = tmp_path / "submission.yaml"
    submission.write_text(
        (ROOT / "submission-sample.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(SubmissionError, match="fictional sample"):
        validate_submission(
            submission,
            ROOT / "docs/contracts/submission.schema.json",
            sample_path=ROOT / "submission-sample.yaml",
        )


def test_only_student_editable_paths_are_permitted() -> None:
    """The advisory path gate must accept this Task's editable paths and reject others."""
    validate_changed_paths(["submission.yaml"])
    validate_changed_paths(["docs/student/decision-evidence-record.md"])
    validate_changed_paths(["submission.yaml", "docs/student/decision-evidence-record.md"])

    with pytest.raises(SubmissionError, match="src/api"):
        validate_changed_paths(["src/api/routes.py"])

    with pytest.raises(SubmissionError, match="loadtest"):
        validate_changed_paths(["loadtest/model_provider_latency.py"])


def test_baseline_template_is_rejected_and_edited_copy_passes(tmp_path: Path) -> None:
    """The evidence-record baseline gate must reject the template and accept a real edit."""
    baseline = tmp_path / "decision-evidence-record.md"
    baseline.write_text(
        (ROOT / "docs/student/decision-evidence-record.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    with pytest.raises(SubmissionError, match="template markers"):
        validate_baseline(baseline)

    baseline.write_text(
        "# Decision-Evidence Record\n\n"
        "| Claim | Source | What it proves | Limitation |\n"
        "|---|---|---|---|\n"
        "| Fictional worker concurrency drives the bottleneck | Fictional Task 1.4 load test | "
        "Fictional queue backlog grew while CPU stayed low | Fictional local-only evidence |\n",
        encoding="utf-8",
    )
    validate_baseline(baseline)


def test_public_entrypoint_reports_an_incomplete_answer_sheet(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Catch a verifier entrypoint that skips the real submission contract."""
    (tmp_path / "docs/contracts").mkdir(parents=True)
    (tmp_path / "submission.yaml").write_text(
        (ROOT / "submission.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "submission-sample.yaml").write_text(
        (ROOT / "submission-sample.yaml").read_text(encoding="utf-8"), encoding="utf-8"
    )
    (tmp_path / "docs/contracts/submission.schema.json").write_text(
        (ROOT / "docs/contracts/submission.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    assert main(tmp_path, changed_paths=[]) == 1
    assert "answers.decision_evidence_mappings is incomplete" in capsys.readouterr().err


@pytest.mark.parametrize(
    "unsafe_text",
    [
        "answers: {value: first, value: second}\n",
        "answers: &answer {value: fictional}\n",
        "answers: *missing\n",
        "answers: {<<: {value: fictional}}\n",
        "answers: {value: 2026-09-04}\n",
        "answers: {value: 2026-09-04T12:30:00Z}\n",
        "answers: {value: !custom fictional}\n",
        "answers: {value: !!set {fictional: null}}\n",
        "answers: {1: fictional}\n",
    ],
    ids=[
        "duplicate-key",
        "anchor",
        "alias",
        "merge-key",
        "date",
        "timestamp",
        "custom-tag",
        "set",
        "non-string-key",
    ],
)
def test_non_json_yaml_constructs_are_rejected(tmp_path: Path, unsafe_text: str) -> None:
    """Reject restricted syntax before schema validation can mask a parser defect."""
    submission = tmp_path / "submission.yaml"
    submission.write_text(unsafe_text, encoding="utf-8")

    with pytest.raises(SubmissionError, match="restricted YAML"):
        _load_one_document(submission)


def test_multiple_yaml_documents_are_rejected(tmp_path: Path) -> None:
    """A second document cannot supply or replace the answer mapping."""
    submission = tmp_path / "submission.yaml"
    submission.write_text("answers: {}\n---\nanswers: {}\n", encoding="utf-8")

    with pytest.raises(SubmissionError, match="exactly one YAML mapping"):
        _load_one_document(submission)


def test_plain_yaml_values_and_block_strings_are_preserved(tmp_path: Path) -> None:
    """The restrictions preserve ordinary answer data and quoted date strings."""
    submission = tmp_path / "submission.yaml"
    submission.write_text(
        'answers:\n  date: "2026-09-04"\n  values: [true, false, null, 12, 2.5]\n'
        "  explanation: |\n    Fictional observation.\n    Second line.\n",
        encoding="utf-8",
    )

    assert _load_one_document(submission) == {
        "answers": {
            "date": "2026-09-04",
            "values": [True, False, None, 12, 2.5],
            "explanation": "Fictional observation.\nSecond line.\n",
        }
    }
