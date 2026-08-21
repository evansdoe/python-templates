# {{ cookiecutter.package_name }}

{{ cookiecutter.package_description }}

{% if cookiecutter.ci_platform in ["github", "both"] -%}
[![CI]({{ cookiecutter.__github_url }}/actions/workflows/ci.yml/badge.svg)]({{ cookiecutter.__github_url }}/actions/workflows/ci.yml)
{% endif -%}
{% if cookiecutter.ci_platform in ["gitlab", "both"] -%}
[![pipeline status]({{ cookiecutter.__gitlab_url }}/badges/main/pipeline.svg)]({{ cookiecutter.__gitlab_url }}/-/pipelines)
{% endif -%}
[![Python](https://img.shields.io/badge/python-{{ cookiecutter.min_python_version }}%2B-blue)](https://www.python.org)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## Install

```bash
uv add {{ cookiecutter.__package_slug }}
```

## Usage

```python
import {{ cookiecutter.__module_name }}

print({{ cookiecutter.__module_name }}.__version__)
```

## Development

```bash
git clone {{ cookiecutter.__repo_url }}.git
cd {{ cookiecutter.__package_slug }}
uv sync --all-groups
{%- if cookiecutter.include_precommit == "yes" %}
uv run pre-commit install
{%- endif %}
uv run poe all
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full task list.
{%- if cookiecutter.include_danger == "yes" %}

### Danger.js (one-time setup)

```bash
cd scripts/danger && pnpm install   # commit the generated pnpm-lock.yaml
```
{%- if cookiecutter.ci_platform in ["gitlab", "both"] %}

For GitLab, add a project access token (`api` scope, Reporter role) as the masked CI/CD
variable `DANGER_GITLAB_API_TOKEN`. GitHub Actions uses the built-in `GITHUB_TOKEN`.
{%- endif %}
{%- endif %}

## License

{% if cookiecutter.license == "Proprietary" %}Proprietary. All rights reserved.{% else %}{{ cookiecutter.license }} — see [LICENSE](LICENSE).{% endif %}
