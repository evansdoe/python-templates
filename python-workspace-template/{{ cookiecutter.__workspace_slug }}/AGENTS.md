# AGENTS.md: {{ cookiecutter.__workspace_slug }}

{{ cookiecutter.workspace_description }}

A uv workspace. Each project is a member under `projects/` with its own
`pyproject.toml`; shared tooling (ruff{% if cookiecutter.type_checker != "none" %}, {{ cookiecutter.type_checker }}{% endif %}, poe) is configured here at
the root. Run every command from this folder.

## Commands

```bash
uv sync --all-packages --all-groups                # install everything
uv run poe check                                   # format check, lint{% if cookiecutter.type_checker != "none" %}, types{% endif %}
uv run poe test                                    # all tests
uv run --package <member> pytest projects/<member> # one member's tests
uv run poe fmt && uv run poe lint                  # apply formatting and lint fixes
```

`uv run poe check` and `uv run poe test` must pass before every commit.

## Working in a member

- Read `projects/<member>/AGENTS.md` first. For that member it overrides this
  file.
- Its `docs/PLAN.md` holds the concerns, the decisions log and the open
  questions; its `docs/design/package-map.md` holds the approved sub-packages.
- Its `tests/test_architecture.py` enforces the package map. When it fails,
  move the code; do not loosen the contract.
- Before adding a module, class or sub-package, read
  `.github/skills/python-design/SKILL.md`.
- Design decisions belong to the project owner. Propose, wait for approval,
  then record the decision in the member's `docs/PLAN.md`.

## Adding a member

```bash
cruft create <python-workspace-member template> --output-dir projects/
uv sync --all-packages --all-groups
```

The `members = ["projects/*"]` glob picks it up. Do not add a `[tool.ruff]`
section to a member; it would replace the root configuration.

## Rules

- Every code change follows `.github/skills/dev-workflow/SKILL.md`: plan,
  test first, gates, one pull request.
- One concern per branch; keep changes small enough to review in one sitting.
- No drive-by changes: mention what you noticed, do not fix it unasked.
- No secrets, credentials or personal data in code, tests, fixtures or docs.
