# Task 1.6 contract

Only these paths are student-editable for this Task:

- `submission.yaml`
- `docs/student/decision-evidence-record.md`

All other files are protected. `.github/workflows/protected-review.yml` and
`tests/contract/held_out_review.py` are explicitly protected — editing either voids the held-out
check's integrity, since the protected workflow depends on both running unmodified against a
scenario you have not seen. If completing this Task genuinely requires a change elsewhere, stop and
ask your instructor before proceeding — do not assume it's permitted.

Run `poe verify` before submitting. Opening your pull request also triggers a separate protected
workflow (`.github/workflows/protected-review.yml`) that replays a held-out scenario against your
running stack; its result appears as a second, independent PR check alongside the public one.
