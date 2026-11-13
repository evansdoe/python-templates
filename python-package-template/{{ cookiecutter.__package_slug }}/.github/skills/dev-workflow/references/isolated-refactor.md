# Isolated refactor (dev-workflow section 2b)

Read this when the user asks for an isolated refactor, or before proposing
one.

- **Default: inline**, in the main context.
- **Isolated refactor (opt-in):** use it when the user asks for it, and
  propose it for code that will be read and changed often. It needs an agent
  tool that supports subagents; otherwise refactor inline. A fresh context
  reviews the result instead of defending the reasoning that produced it,
  which tends to give smaller, simpler functions. It does not improve
  correctness, and it costs several times the time and tokens.
- Delegate to the `tdd-refactor` agent. It exists in two files with the same
  body and tool-specific frontmatter; a test keeps the bodies identical, so
  edit both together:
  - GitHub Copilot: `.github/agents/tdd-refactor.agent.md` (the subagent tool
    must be enabled).
  - Claude Code: `.claude/agents/tdd-refactor.md`.
  If the agent is not available, refactor inline.
- The subagent does not see the conversation, so the delegation prompt must
  be self-contained: the subtask's example map, the active test's name, the
  changed production files and their tests, the package and its test command
  (from the nearest `AGENTS.md`), and the repository path. Its own file holds
  the refactor contract (no test edits, no new behaviour, one refactoring at a
  time, predictions before every check).
- The subagent never talks to the user and never commits. Afterwards the main
  agent checks that `git diff --name-only` shows no test files changed, that
  the tests and gates are green, and that the report matches the actual diff,
  then posts the Refactor checkpoint itself.
