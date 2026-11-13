# {{ cookiecutter.project_name }}

{{ cookiecutter.project_description }}

A member of this uv workspace. Run everything from the **workspace root**:

```bash
uv sync --all-packages --all-groups
uv run --package {{ cookiecutter.__project_slug }} pytest projects/{{ cookiecutter.__project_slug }}
```

Add a dependency to this member only:

```bash
uv add --package {{ cookiecutter.__project_slug }} httpx
```
{%- if cookiecutter.project_kind == "application" %}

Run it:

```bash
uv run --package {{ cookiecutter.__project_slug }} {{ cookiecutter.__project_slug }}
```
{%- endif %}

## Layout

```
{{ cookiecutter.__project_slug }}/
├── AGENTS.md              # how to work in this member (CLAUDE.md points to it)
├── docs/
│   ├── PLAN.md            # concerns, decisions log, open questions
│   └── design/package-map.md
├── pyproject.toml         # includes the import contract
├── src/{{ cookiecutter.__module_name }}/
└── tests/
```
