# syntax=docker/dockerfile:1

ARG PYTHON_VERSION={{ cookiecutter.python_version }}
ARG UV_VERSION={{ cookiecutter.uv_version }}

# Named stage because Docker doesn't expand ARGs in `COPY --from=<image>`;
# ghcr.io/astral-sh/uv:${UV_VERSION} always resolves, "latest" included.
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ---------- build ----------
# Installs one member, and the workspace members it uses, into /app/.venv:
#   docker build --build-arg MEMBER=<name> -t <name> .
FROM python:${PYTHON_VERSION}-slim-bookworm AS build
COPY --from=uv /uv /uvx /bin/
ARG MEMBER
RUN test -n "$MEMBER" \
    || { echo "Pass the member to build: --build-arg MEMBER=<name>" >&2; exit 1; }

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Third-party dependencies first, for layer caching. --frozen, because uv
# cannot check the lockfile without every member's pyproject.toml.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-workspace --package "$MEMBER" --no-editable --no-default-groups

# Then the member itself. --no-editable installs real copies, so the runtime
# image needs the virtual environment and no source code.
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --package "$MEMBER" --no-editable --no-default-groups

# ---------- dev ----------
# Before runtime, so a plain `docker build` gives the shipping image.
# One development container for the whole workspace, used by compose.yaml's
# `dev` service{% if cookiecutter.include_devcontainer == "yes" %} and by .devcontainer/devcontainer.json{% endif %}. The project
# folder is mounted at /workspace; `uv sync --all-packages --all-groups`
# installs every member into the container's own .venv.
FROM python:${PYTHON_VERSION}-slim-bookworm AS dev
COPY --from=uv /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

RUN apt-get update -qq && apt-get install -qq -y --no-install-recommends \
        git \
        ssh \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Avoid CRLF diffs on Windows hosts.
RUN git config --global core.autocrlf input \
    && git config --global core.eol lf

WORKDIR /workspace

# ---------- runtime ----------
# Last, because `docker build` builds the last stage by default.
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime
ARG MEMBER
ENV MEMBER=${MEMBER} \
    PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home --uid 1000 app
WORKDIR /app
COPY --from=build --chown=app:app /app/.venv /app/.venv

USER app
# An application member's command is named after the member.
CMD ["sh", "-c", "exec \"$MEMBER\""]
