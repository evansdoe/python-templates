# Pace (dev-workflow section 2a)

Read this when proposing a pace for a subtask, when the user changes it, or
when the user is not present.

## Choosing a pace
The pace decides where the agent stops and waits. Propose one per subtask in
its example map and let the user confirm it with the plan. The user can change
it at any time; follow the latest instruction, and return to the next
subtask's confirmed pace unless told otherwise. The newer and riskier the
work, the closer the stops:

| Kind of subtask | Proposed pace |
|---|---|
| New module, security control or concurrency | `every-step` for the first 2 cycles, then `per-cycle` |
| Pure logic in a pattern already set | `per-cycle` |
| Review fix | `every-step` (usually 1 to 2 cycles) |
| Configuration or documentation only | no TDD stops; plan and end-of-subtask checkpoints only |

| Pace | Stops after |
|---|---|
| `every-step` | test list, Red, Green, Refactor, and any prediction mismatch |
| `full-hitl` | test list, Red, Refactor, and any prediction mismatch |
| `per-cycle` (default) | each completed cycle, and any prediction mismatch |
| `every-n N` | every N completed cycles, and any prediction mismatch |
| `autonomous` | nothing; mismatches are reported, not waited on |

## When the user is not present
- The user is not present when the session was started by a schedule or runs
  headless, or when they said they are away. Otherwise assume they are present
  and wait at checkpoints.
- Do not block. Work at `autonomous` pace and record every skipped stop.
  Record open questions as explicit assumptions, put the plan at the top of
  the work, create the branches, and keep making local WIP commits, because
  these are cheap to undo.
- A design change that needs the owner's approval is proposed, not made:
  record the proposal in the report and continue only with work that does not
  depend on it.
- When the work cannot go on without it (a new module the import contract
  must list), make the change provisionally: add the package-map row, an empty module
  with its docstring so the import contract can pass, and the contract entry,
  all in one commit; write "Proposed, not approved: <names>" under
  Open in `docs/PLAN.md`, and list it first in the report. The owner approves
  or reverts it before anything is pushed.
- Do not squash, push, force-push, or open or update a pull request.
- Finish with a report: the plan and assumptions, the checkpoints in commit
  order, every prediction mismatch, every deviation from the step plan with
  its reason, the gate results, and the decisions waiting for the user.
