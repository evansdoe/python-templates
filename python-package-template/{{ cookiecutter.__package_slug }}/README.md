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

How the code is organised:

- [docs/design/package-map.md](docs/design/package-map.md): the agreed
  sub-packages, enforced by `[tool.importlinter]` in `pyproject.toml` and
  checked by `tests/test_architecture.py`.
- [docs/PLAN.md](docs/PLAN.md): concerns, decisions and open questions.
- `tests/unit/` mirrors the package's sub-packages.
- [AGENTS.md](AGENTS.md): instructions for coding agents.
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
{%- if cookiecutter.include_docker == "yes" %}

## Containers

`compose.yaml` builds the images from the one `Dockerfile`:

```bash
docker compose up --build app        # run the shipping image
{%- if cookiecutter.include_devcontainer == "yes" %}
docker compose run --rm dev bash     # a shell in the development image
{%- endif %}
```

Settings and secrets go in a `.env` file next to `compose.yaml`. It is
optional, git ignores it, and `.dockerignore` keeps it out of every image.
The optional `.env` needs Docker Compose 2.24 or later.

### Adding a service

A service the package needs at run time, such as a database, is a new entry
under `services:`, and `depends_on` starts it before `app`. For PostgreSQL,
add these lines to `compose.yaml`:

```yaml
services:
  app:
    depends_on:
      - db
  db:
    image: postgres:18
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql

volumes:
  pgdata:
```

Put `POSTGRES_PASSWORD=...` in `.env`, which Compose reads. The containers
reach the database at the host name `db`.
{%- if cookiecutter.include_devcontainer == "yes" %} Give `dev` the same
`depends_on` to use the database while developing.
{%- endif %} Pin the image to a major version, as here, so that a rebuild never
upgrades the database unannounced; from PostgreSQL 18 on, the data volume
belongs at `/var/lib/postgresql`, not `/var/lib/postgresql/data`.
{%- endif %}

## License

{% if cookiecutter.license == "Proprietary" %}Proprietary. All rights reserved.{% else %}{{ cookiecutter.license }} — see [LICENSE](LICENSE).{% endif %}
