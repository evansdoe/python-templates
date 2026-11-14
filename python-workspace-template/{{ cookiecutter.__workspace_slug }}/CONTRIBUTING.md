# Contributing to {{ cookiecutter.workspace_name }}

## Setup

```bash
uv sync --all-packages --all-groups
{%- if cookiecutter.include_precommit == "yes" %}
uv run pre-commit install
{%- endif %}
```

## Working on one member

```bash
uv run --package <name> pytest projects/<name>
uv add --package <name> httpx        # add a dependency to that member only
```

Shared dev tooling (ruff, pytest, the type checker) lives in the root
`[dependency-groups]`. Member `pyproject.toml` files declare only their own
runtime dependencies.

## How changes are made

People and coding agents follow the same workflow:

- [AGENTS.md](AGENTS.md) is the short entry point; each member's own
  `AGENTS.md` adds what is specific to it.
- `.github/skills/dev-workflow/SKILL.md` describes how a change is made: one
  concern per branch, planned in the member's `docs/PLAN.md`, tests first, the
  gates, one pull request.
- `.github/skills/python-design/SKILL.md` says where code goes. A new module
  or sub-package changes the member's `docs/design/package-map.md`, which the
  project owner approves; the member's `tests/test_architecture.py` enforces
  it.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/), with the member
name as the scope:

```
feat(first-project): add yaml loader
```

## Releasing a member

Members version independently. Tag with the member name as prefix:

```bash
git tag -a first-project-v0.2.0 -m "release: first-project v0.2.0"
git push --follow-tags
```
