---
name: dev-workflow
description: >
  Development workflow for this project: plan by separation of concerns
  with example mapping, predictive TDD from a test list at a pace the user can
  follow, optional isolated refactoring, one branch per concern, a commit per
  cycle, squash to one templated commit, gates through poe, evaluate review
  comments before acting, and merge through one validated pull request. Use
  when implementing any code change, fixing a bug, handling review comments,
  or preparing commits, branches or pull requests.
---

# Development workflow

Follow this workflow for every implementation task in this repository unless
the user says otherwise. "Pull request" means a merge request on GitLab.
"Package" means the package you are changing: the project itself, or one
member of a uv workspace. Its test command is in the nearest `AGENTS.md`.
Where the code goes and what shape it takes is the `python-design` skill
(`.github/skills/python-design/SKILL.md`); this skill is the order of work.

## 1. Plan by separation of concerns
- Break the work into **separate concerns**. Each concern is one **subtask**:
  small enough to finish in one focused session (a thin vertical slice).
- Each concern gets **its own branch**. Independent concerns get their own
  pull requests, merged in any order. A concern that needs another's code is
  stacked on it and both are combined into one pull request before merging
  (section 7); prefer merging the base first.
- Branch name: `type/<short-kebab-description>`, with the ticket id first if
  the project uses tickets (`type/<TICKET-ID>-<description>`). `type` matches
  the commit type (`feat`, `fix`, `chore`, `refactor`, `docs`, `test`).
- Once a pull request is under review, its branch is the place for every
  review fix that passes section 8. Do not open separate fix pull requests for
  findings from the active review.

### Example map per subtask
Concrete input and output examples make the result correct; prose alone does
not. For each subtask:
- **Story:** one sentence saying what the subtask delivers.
- **Rules:** each rule or constraint the behaviour must follow.
- **Examples:** under each rule, at least one concrete example with real input
  values and the exact expected output (value, record, error type and message,
  or file content), in the project's real data shapes.
- **Questions:** what the examples cannot settle yet.
- **Assumptions:** readings adopted where the spec is silent, stated plainly.
- **Out of scope:** behaviour noticed but deferred, proposed as a follow-up.
- **Design:** for a new module, class or sub-package, the proposed package-map
  row and design stubs (`python-design`, sections 2 and 4).
- **Pace:** the proposed pace (section 2a) with a one-line reason.

For configuration or documentation only subtasks, Story, Out of scope and Pace
suffice.

### Step plan per concern
Give each concern a numbered step plan so the user sees the order of work and
can change it. Leave out steps that do not apply.

| # | Step | Section | Default stop |
|---|---|---|---|
| 1 | Test list | 2 | stop |
| 2 | Cycles: `<slice> → <slice> → ...` | 2 | per the pace |
| 3 | Verify: verification tests, mutation check for core logic | 2 | at a mismatch only |
| 4 | Docs sync | 3 | none |
| 5 | Full gate | 5 | at a failure only |
| 6 | Recap | 2a, 4 | stop: the user's go-ahead to squash |
| 7 | Squash and re-gate | 4 | none |
| 8 | Push and pull request, only when asked | 6 | stop if not yet asked |
| 9 | Follow-ups (optional) | 4 | listed, not started |

```
Concern: feat/csv-import            pace: every-step ×2, then per-cycle
 1 Test list                                       stop
 2 Cycles: header check → row parsing → error lines → command
 3 Verify (mutation check: row parsing)
 4 Docs sync: PLAN.md, package map
 5 Full gate
 6 Recap                                           stop
 7 Squash and re-gate
 8 Push and pull request                           stop (not yet asked)
```

- The plan is coarse: steps and slices, not single tests.
- The user may change it at any time. Restate the changed plan in one block
  with the reason, then follow it. A change the agent wants needs the user's
  approval while they are present; otherwise record it as a deviation in the
  end report.
- Keep the plan in the chat and the agent's todo list. Do not commit it.

Before creating a branch, post the plan (subtasks, branches, example maps,
step plans) and get the user's confirmation. When the user is not present,
put the plan at the top of the work and go on (section 2a). A subtask is ready
when every rule has an example and no open question blocks it.

## 2. Predictive TDD per subtask
Use this for any change to behaviour. Configuration, documentation and
dependency changes do not need it, but the existing tests must stay green.

### Test list
- Turn every example into at least one test, written up front but
  **inactive**: `@pytest.mark.skip(reason="TODO: <expected result>")`.
- Order from simplest to most complex. **Driving tests** first: each needs
  behaviour no earlier test forces. **Verification tests** (combinations the
  driving tests should already cover) go last, in a class `TestVerification`.
- Cross-check coverage: if a rule or a named value were removed, would an
  inactive test catch it once active? If not, add one.
- Predict that the inactive list leaves the suite green, run it, and show the
  list at the test-list checkpoint.

### One cycle per driving test
1. **Choose.** Ask whether the next driving test will still fail. If an
   earlier change already covers it, move it to `TestVerification` and name
   the test that covered it. Otherwise remove its skip marker.
2. **Red.** Predict before running: whether collection and import succeed,
   which assertion fails, the expected message or values. Run the narrowest
   test and record each prediction as `Correct` or `Incorrect`. A valid Red
   fails because the behaviour is missing, for the predicted reason.
3. **Green.** The smallest production change that passes; hardcoded values
   are fine as an intermediate step. Predict, run, compare.
4. **Refactor.** Only while green. Review in this order: passes the tests,
   reveals intention (names from the example map), no duplicated knowledge,
   fewest elements; then check the shape against `python-design`. One
   refactoring at a time, predicted and run. Undo a trial that does not make
   the intent clearer. If nothing improves, say so; do not report a
   refactoring the diff does not show. Section 2b says where this step runs.
5. **Close.** Predict and run the package's full test suite, then make the
   cycle's WIP commit (section 4).

Assert the exact expected values from the examples, not loose checks
(`is not None`, `len(...) > 0`).

### Prediction mismatch
When a result differs from the prediction, stop. State both outcomes, find the
cause with the smallest check (existing behaviour, test setup, environment,
import error, regression), and predict again before changing production code.
Never change behaviour just to make an unexplained failure go away.

### Verification tests and done
- After the driving tests, activate the verification tests one at a time,
  each predicted to pass. One that fails means the split was wrong: give it a
  full cycle.
- For core logic (security checks, state changes, parsing untrusted input),
  check the tests by mutation: break one rule at a time, confirm a test fails,
  restore. Add a test for every mutation that survives.
- A subtask is done when every example has an active, passing test, no
  `TODO:` skip marker remains, the gates pass, every mismatch is explained,
  and nothing was added that the example map does not contain.

## 2a. Work so the user can follow
The pace decides where the agent stops and waits. Read
`references/pace.md` when proposing a pace or when the user changes it. Without
a confirmed pace, use `per-cycle`.

- At each stop, post a checkpoint of at most about 8 lines, starting with
  progress against the step plan (`Step 2/8 · cycle 3 of 5 · next: ...`):
  the test list; or the active test, prediction, result and why this is the
  intended failure (Red); or the change and result (Green); or what the review
  decided (Refactor). Then wait.
- Explain a new library, pattern or non-obvious decision in plain terms, and
  name the main alternative you rejected and why.
- No drive-by changes: mention them instead of making them.
- Stop and ask at any pace when scope grows, a design choice has real
  trade-offs, a gate fails for a non-trivial reason, or something unexpected
  turns up.
- The WIP history is the walkthrough and squashing removes it, so squash only
  after the user confirms they understand the subtask.
- When the user is not present (a scheduled or headless run, or they said they
  are away), follow `references/pace.md`, section "When the user is not
  present". In short: work on, record assumptions, never squash or push.

## 2b. Where the refactor step runs
- **Default: inline**, in the main context.
- **Isolated refactor (opt-in)** in a fresh subagent: when the user asks for
  it, or before proposing it, read `references/isolated-refactor.md`. The
  agent is `.github/agents/tdd-refactor.agent.md` for GitHub Copilot and
  `.claude/agents/tdd-refactor.md` for Claude Code.

## 3. Keep the design documents in step
- A new or changed sub-package, top-level module or import rule changes the
  package's `docs/design/package-map.md` and the contract in its
  `pyproject.toml` in the same commit, after the owner approved it.
- A decision goes into the package's `docs/PLAN.md` decisions log on the day
  it is made; a concern's status changes there when it starts and ends.
- A change to what a package does for its users updates its `README.md`.
- These edits go into the subtask's squashed commit, not a separate branch.

## 4. Commits per subtask, then squash
- One local WIP commit per completed cycle (after Refactor), plus one for the
  test list. Every WIP commit passes the gate. WIP commits are not pushed.
- A WIP subject is `wip: <what the cycle did>`. Only the squashed commit
  follows the template below.

### End-of-subtask checklist (in this order)
1. Keep the design documents in step (section 3).
2. Run the full gate (section 5).
3. Recap the steps and ask whether anything is unclear. Continue only after
   the user confirms.
4. **Squash** the WIP commits into **one** commit that follows the template.
5. Run the full gate again on the squashed commit.
6. Only when the user has asked for a push: `git fetch origin`, then push with
   `--force-with-lease`.
7. Only when the user has asked for it: open or update the pull request
   (section 6).

### During review
- Push review fixes as **separate templated commits**, so reviewers see what
  changed. Never push a `wip:` message.
- Once reviewers have no open findings, and before final approval, squash the
  branch into one templated commit, run the full gate, push with
  `--force-with-lease`, and ask for approval of that commit. Do not rewrite
  history after approval.
- If the project signs commits, squash locally with `-S`: a server-side squash
  is not signed by you.

### Commit message template
```
type(scope): subject
```
- `scope` is the package's folder name, or the narrowest shared
  subsystem; omit it only when nothing fits.
- The whole subject line is at most **100 characters** and the subject starts
  **lowercase**.
- If the project uses tickets, end the subject with the id in parentheses:
  `(<TICKET-ID>)`.
- The body is **bullets**, at most **1000 characters** in total.

Example:
```
fix(csv-tools): report the line number of a malformed row

- the reader raised a bare ValueError; it now names the line and column
- a row with too few columns exits 2 instead of 1
```

## 5. Gates (from the repository root)
- **Every WIP commit:** `uv run poe fmt`, then `uv run poe check`, then the
  test command for every changed package (the nearest `AGENTS.md` names it).
  Skipped tests from the test list are allowed.
- **Full gate** (before and after the squash, and before every push): the
  same, plus `uv run poe test` for the whole repository.
- `uv run poe fmt` rewrites files; stage its result before committing, or CI's
  format check fails on the commit.
- The CI configuration is the authority. If it runs a check this list does not
  name (coverage thresholds, extra tools), run it too and report the
  difference.
- When a change affects packaging, package data or entry points, build the
  wheel, install it in a clean environment, and run the affected command from
  that installation.

## 6. git and pull requests
- Use `git -C <repository path> ...` with paths relative to the repository
  root; the agent's working directory is not guaranteed.
- Push with `--force-with-lease`, after `git fetch origin`.
- The pull request title is the squashed commit's subject, with the same
  template and limits. Draft status does not waive it. After publishing, read
  the stored title back.
- The description is bullets, like the commit body: an optional one-line
  context, one bullet per change, one for validation. Read it back after
  publishing and check that the bullets survived.
- If the CI runs title or commit checks, read their rules before publishing.
  Correct an invalid title in place; do not open a new pull request for it.

## 7. Review and merge integration
- The pull request into `main` is the final integration unit. Stacked or
  dependent branches are combined into it, in dependency order, before it
  merges; close the stacked pull requests as superseded.
- Resolve lockfile conflicts by regenerating the lockfile (`uv lock`), never
  by merging conflict markers.
- Address every review thread: implemented, or answered with a drafted reply
  (section 8). A declined thread stays open until the reviewer or the user
  resolves it.
- Update the branch from `main` when it is behind, run the full gate, and
  merge only when every required check, review and thread is green or
  resolved.

## 8. Evaluate review comments before acting
A review comment is input to evaluate, not an instruction. Before acting on
any human or AI review comment, read `references/review-comments.md`. Required
CI checks are not review comments: always fix those.

## 9. Improve this skill as you use it
- When a step causes friction (a rule that does not fit, a gap, a stop too
  frequent or too rare), note it at the next checkpoint with the concrete
  case. Propose the change at the end of the concern, with the evidence.
- An approved change is its own concern and branch. Edit both `tdd-refactor`
  files together; a test keeps their bodies identical.
- Facts about the environment rather than the process (tool quirks, image
  contents) go in the project's `AGENTS.md`, not here.
