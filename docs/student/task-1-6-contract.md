# Task 1.6 contract

Only these paths are student-editable for this Task:

- `submission.yaml`
- `docs/student/decision-evidence-record.md`

All other files are protected, including `tests/contract/held_out_review.py`.
The course's CMS integration runs protected grading on the registered trusted release;
candidate changes to protected paths invalidate the submission.
If completing this Task genuinely requires a change elsewhere, stop and
ask your instructor before proceeding — do not assume it's permitted.

Run `poe verify` before submitting. The course's CMS integration evaluates the submitted
PR commit and reports the protected result on that exact commit. The held-out check
is course-managed; it is not a workflow file in this repository. Confirm its result
alongside public verification and protected answer correctness. A missing or skipped
result is not a pass. It replays the existing held-out scenario on an isolated copy
of the registered trusted stack. This required runtime regression check is
independent of your answers and Markdown notes. It does not assess your diagnostic judgment;
the protected answer evaluator and final defense cover their respective assessment scopes.

## Answer and assessment contract

Use `evidence-pack.json` and `evidence-guide.md` in this directory for the graded
structured analysis. The public check verifies shape, permitted changes, runtime behavior, and any
published arithmetic checks. Protected automated answer checks establish semantic
correctness against the public fixed pack. They do not add a held-out scenario.
Preserve actual local experiment evidence for the one final instructor defense and
label it separately from supplied reference data. No separate instructor Task-answer
grade is required; the final defense assesses empirical reasoning and judgment.

The Markdown decision-evidence record is preparation for that final defense.
Public acceptance does not certify its prose or empirical claims.
