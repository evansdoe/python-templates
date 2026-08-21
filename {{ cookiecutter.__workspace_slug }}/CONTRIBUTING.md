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
