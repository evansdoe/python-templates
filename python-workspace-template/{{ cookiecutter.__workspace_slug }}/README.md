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
├── AGENTS.md               # instructions for coding agents
├── scripts/ci/             # project discovery, type-check and test runners
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

## Adding a project

Generate one with the member template — the glob in `[tool.uv.workspace]` picks
it up automatically, and CI discovers it with no pipeline edits:

```bash
cruft create git@github.com:evansdoe/python-templates.git --directory python-workspace-member --output-dir projects/
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

{%- if cookiecutter.include_docker == "yes" %}
## Containers

`compose.yaml` has one development container for the whole workspace, built
from the `dev` stage of the `Dockerfile`; the same file builds images for the
members that ship (below):

```bash
docker compose run --rm dev bash         # a shell in the container
uv sync --all-packages --all-groups      # inside it: install every member
```

The workspace is mounted at `/workspace`, and the container keeps its `.venv`
in its own volume, so the install survives restarts and a `.venv` made on the
host never gets in the way.{% if cookiecutter.include_devcontainer == "yes" %} The devcontainer uses the same `dev` service and runs
the `uv sync` for you.{% endif %}

Settings and secrets go in a `.env` file next to `compose.yaml`. It is
optional, git ignores it, and `.dockerignore` keeps it out of every image.
The optional `.env` needs Docker Compose 2.24 or later.
{%- if cookiecutter.accelerator == "nvidia" %}

### GPUs

The `dev` service reserves every NVIDIA GPU on the host and gets 8 GB of
shared memory, which PyTorch's data-loader workers use to pass batches (raise
`shm_size` in `compose.yaml` if they run out). The image needs no CUDA of its
own: PyTorch's wheels bring their CUDA runtime with them. The host needs an
NVIDIA driver and the NVIDIA Container Toolkit, on Linux or on Windows with
WSL 2; Docker on macOS cannot pass a GPU into a container. To check, with
PyTorch installed in a member:

```bash
docker compose run --rm dev uv run python -c "import torch; print(torch.cuda.is_available())"
```
{%- endif %}

### Shipping a member as an image

The same `Dockerfile` builds an image for one `application` member: its
`build` stage installs that member and the workspace members it uses, and the
`runtime` image holds only that virtual environment and runs the member's
command as a non-root user. Libraries ship inside the applications that use
them; research members are not shipped. `uv.lock` must be committed.

```bash
docker build --build-arg MEMBER=ledger -t ledger .
docker run --rm ledger
```

`compose.yaml` cannot list the members by itself, since they are added later;
give each member that ships a service of its own:

```yaml
services:
  ledger:
    build:
      context: .
      target: runtime
      args:
        MEMBER: ledger
```

### Adding a service

A service the members need, such as a database, is a new entry under
`services:`, and `depends_on` starts it before `dev` (or before a member's
service). For PostgreSQL, add
these lines to `compose.yaml`:

```yaml
services:
  dev:
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
reach the database at the host name `db`. Pin the image to a major version,
as here, so that a rebuild never upgrades the database unannounced; from
PostgreSQL 18 on, the data volume belongs at `/var/lib/postgresql`, not
`/var/lib/postgresql/data`.

{% endif -%}
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

## Working with coding agents

[AGENTS.md](AGENTS.md) holds the instructions for coding agents. Each member
under `projects/` has its own `AGENTS.md` for work inside it, and the shared
skills live in `.github/skills/`.

## License

{% if cookiecutter.license == "Proprietary" %}Proprietary. All rights reserved.{% else %}{{ cookiecutter.license }} — see [LICENSE](LICENSE).{% endif %}
