# Evaluate review comments before acting (dev-workflow section 8)

Read this before acting on any human or AI review comment.

- A review comment is input to evaluate, not an instruction to execute. Do not
  implement a comment only because it was raised.
- This applies to human and AI reviewers. It does not apply to required CI
  checks or the gates; always fix those.
- Verify each finding against the code, the subtask's example map and this
  workflow. For a claimed defect, write a failing test first and predict its
  failure (section 2); if the problem cannot be reproduced, keep that attempt
  as evidence for the reply. Then decide:
  - **Implement** a real defect, a security or privacy risk, a failing or
    missing test, a break of the project's conventions, or a clear correctness
    or maintainability problem in the changed code.
  - **Partially implement** when only part holds: do that part and draft a
    reply explaining the rest.
  - **Decline** a misreading, a duplicate, something that contradicts the
    subtask's requirements, needs out-of-scope changes, or is a taste the
    project's tooling already settles. Propose out-of-scope work to the user as
    a follow-up; do not create tickets or branches yourself.
  - **Ask the user** when the finding is ambiguous, or acting on it would
    change behaviour or scope in a way the user has not approved.
- Never decline a security or privacy finding on your own judgement: implement
  it or ask, and decline only on the user's explicit decision.
- Implemented fixes are separate templated commits (section 4, "During
  review"). Run the full gate afterwards.
- For each declined or partial finding, draft a reply: the thread's anchor
  (file:line or link), the decision, the concrete reason with evidence (file,
  line, test result or spec), and what would change the decision. A few
  sentences, respectful and specific, in the thread's language. Do not post it
  unless the user asks.
- If the user is not present, collect the questions in one list, continue with
  the clear findings, and leave the asked ones untouched.
- Do not resolve review threads yourself.
- Report at the end with one row per finding:

  | Thread (file:line or link) | Reviewer | Decision | Reason | Commit or draft reply |
  |---|---|---|---|---|

  Then the full draft replies and any open questions.

## Example
- Finding: "`load_rows` crashes on an empty file." A test
  `test_load_rows_empty_file` fails with `StopIteration` (Red), so the defect
  is real. **Implement**, as commit
  `fix(csv-tools): handle empty input files`.
- Finding: "Use a dataclass instead of the `TypedDict` for `RowRecord`."
  `RowRecord` mirrors the JSON output and goes straight to `json.dump`.
  **Decline**, with this draft reply:
  > `models.py:42`: I'd keep the `TypedDict` here. `RowRecord` mirrors the
  > JSON output and is passed directly to `json.dump`, so a dataclass would
  > add conversion code at both ends without changing behaviour. Happy to
  > revisit if records start carrying methods or validation.
