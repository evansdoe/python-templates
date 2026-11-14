# Contributing to {{ cookiecutter.package_name }}

## Setup

```bash
uv sync --all-groups
{%- if cookiecutter.include_precommit == "yes" %}
uv run pre-commit install
{%- endif %}
```

## Everyday commands

| Task | Command |
| --- | --- |
| Format | `uv run poe fmt` |
| Lint (autofix) | `uv run poe lint` |
{%- if cookiecutter.type_checker != "none" %}
| Type check | `uv run poe types` |
{%- endif %}
| Tests | `uv run poe test` |
| Coverage | `uv run poe cov` |
| Everything | `uv run poe all` |

## How changes are made

People and coding agents follow the same workflow:

- [AGENTS.md](AGENTS.md) is the short entry point: where things are, the
  commands, the rules.
- `.github/skills/dev-workflow/SKILL.md` describes how a change is made: one
  concern per branch, planned in `docs/PLAN.md`, tests first, the gates above,
  one pull request.
- `.github/skills/python-design/SKILL.md` says where code goes. A new module
  or sub-package changes `docs/design/package-map.md`, which the project owner
  approves; `tests/test_architecture.py` enforces it.

## Commits

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject in lowercase, imperative>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

## Releasing

1. Update `version` in `pyproject.toml` and add a `CHANGELOG.md` entry.
2. Tag: `git tag -a v0.1.0 -m "release: v0.1.0" && git push --follow-tags`.
