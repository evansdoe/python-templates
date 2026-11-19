# syntax=docker/dockerfile:1

ARG PYTHON_VERSION={{ cookiecutter.python_version }}
ARG UV_VERSION={{ cookiecutter.uv_version }}

# Named stage because Docker doesn't expand ARGs in `COPY --from=<image>`;
# ghcr.io/astral-sh/uv:${UV_VERSION} always resolves, "latest" included.
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ---------- dev ----------
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
