# {{ cookiecutter.workspace_name }}

{{ cookiecutter.workspace_description }}

## Members

`uv sync --all-packages --all-groups` installs every project under `projects/`
editable into this workspace's single `.venv`, so a member's modules are
importable here without listing per-member paths in `mkdocs.yml`. Document a
member's public API with a mkdocstrings directive naming its top-level
module, e.g.:

    ::: geo_core

Add a nav entry per member as you write its page — `nav:` in `mkdocs.yml` is
the one place this template doesn't auto-discover, since a table of contents
is an editorial choice, not a build input.
