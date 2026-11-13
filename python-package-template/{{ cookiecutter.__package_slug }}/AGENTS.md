# AGENTS.md: {{ cookiecutter.__package_slug }}

{{ cookiecutter.package_description }}

## Where things are

- `docs/PLAN.md`: the concerns (one branch each), the decisions log and the
  open questions. Read it before starting work; update it when a concern
  changes status or a decision is made.
- `docs/design/package-map.md`: every sub-package, its role, what belongs in
  it and what it may import. The project owner approves changes to it.
- `[tool.importlinter]` in `pyproject.toml`: the package map as an enforced
  contract.
- `tests/test_architecture.py`: runs the contract and checks that
  `tests/unit/` mirrors the package.

## Commands

```bash
uv sync --all-groups      # install everything
uv run pytest             # all tests, including the architecture test
uv run poe fmt            # apply formatting
uv run poe check          # format check, lint{% if cookiecutter.type_checker != "none" %}, types{% endif %}
```

`uv run poe check` and `uv run pytest` must pass before every commit.

## Rules

- Every code change follows `.github/skills/dev-workflow/SKILL.md`: plan,
  test first, gates, one pull request.
- Before adding a module, class or sub-package, read
  `.github/skills/python-design/SKILL.md`.
- A new top-level module or sub-package is a design decision. Propose its row
  for the package map, wait for approval, then add it to the map and to
  `layers` in `pyproject.toml` in the same change.
- Start with one module per role. Split a module only when it passes about
  150 lines or has two reasons to change. A helper used by one module stays
  in that module.
- When the architecture test fails, move the code to where it belongs. Do not
  loosen the contract, rename a module to dodge it, or skip the test.
- Unit tests go in `tests/unit/<same path as in src>`. Test files do not
  import each other; share helpers through fixtures in `tests/conftest.py`.
- Record a decision in `docs/PLAN.md` on the day it is made, one line, dated.
- No secrets, credentials or personal data in code, tests, fixtures or docs.
