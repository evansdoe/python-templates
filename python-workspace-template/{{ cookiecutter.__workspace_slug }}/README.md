# {{ cookiecutter.workspace_name }}

{{ cookiecutter.workspace_description }}

{% if cookiecutter.ci_platform in ["github", "both"] -%}
[![CI]({{ cookiecutter.__github_url }}/actions/workflows/ci.yml/badge.svg)]({{ cookiecutter.__github_url }}/actions/workflows/ci.yml)
{% endif -%}
{% if cookiecutter.ci_platform in ["gitlab", "both"] -%}
[![pipeline status]({{ cookiecutter.__gitlab_url }}/badges/main/pipeline.svg)]({{ cookiecutter.__gitlab_url }}/-/pipelines)
{% endif %}
This is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/):
a monorepo hosting several Python projects that share one lockfile and one dev
toolchain. Each member lives under `projects/<name>/` with its own
`pyproject.toml` and its own dependencies.

```
{{ cookiecutter.__workspace_slug }}/
├── pyproject.toml          # workspace root: members = ["projects/*"]
├── uv.lock                 # one lockfile for every member
├── ruff.toml               # shared lint config
├── scripts/ci/             # project discovery used by CI
└── projects/
    ├── first-project/
    └── second-project/
```

## Setup

```bash
uv sync --all-packages --all-groups
{%- if cookiecutter.include_precommit == "yes" %}
uv run pre-commit install
{%- endif %}
```

## Adding a project

Generate one with the member template — the glob in `[tool.uv.workspace]` picks
it up automatically, and CI discovers it with no pipeline edits:

```bash
cruft create git@github.com:{{ cookiecutter.vcs_username }}/python-workspace-member.git --output-dir projects/
uv sync --all-packages --all-groups
```

## Everyday commands

| Task | Command |
| --- | --- |
| Format | `uv run poe fmt` |
| Lint (autofix) | `uv run poe lint` |
{%- if cookiecutter.type_checker != "none" %}
| Type check | `uv run poe types` |
{%- endif %}
| Test everything | `uv run poe test` |
| Test one member | `uv run --package <name> pytest projects/<name>` |
| List members | `uv run poe projects` |
| Everything | `uv run poe all` |

Run a member's own entry point with `uv run --package <name> <command>`.

## How CI works

Lint, type checks and the license audit run **once** at the root over all
members. Tests run **per member**, and only for members affected by the change:

{% if cookiecutter.ci_platform in ["github", "both"] -%}
- **GitHub Actions** — the `discover` job emits a JSON matrix from
  `scripts/ci/discover_projects.py`, and `test` fans out over it.
{% endif -%}
{% if cookiecutter.ci_platform in ["gitlab", "both"] -%}
- **GitLab CI** — `generate-child-pipeline` writes `child-pipelines.yml` from the
  same script and the `projects` job triggers it. A member with its own
  `.gitlab-ci.yml` gets triggered instead of the default test job.
{% endif %}
A change to `pyproject.toml`, `uv.lock`, `ruff.toml`, `scripts/` or the CI
config counts as affecting every member.

## License

{% if cookiecutter.license == "Proprietary" %}Proprietary. All rights reserved.{% else %}{{ cookiecutter.license }} — see [LICENSE](LICENSE).{% endif %}
