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
├── pyproject.toml
├── src/{{ cookiecutter.__module_name }}/
└── tests/
```
