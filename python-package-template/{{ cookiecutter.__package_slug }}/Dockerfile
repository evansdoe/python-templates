# syntax=docker/dockerfile:1

ARG PYTHON_VERSION={{ cookiecutter.python_version }}
ARG UV_VERSION={{ cookiecutter.uv_version }}

# Named stage rather than `COPY --from=ghcr.io/astral-sh/uv:${UV_VERSION}`
# directly -- Docker doesn't expand ARGs in COPY --from='s image reference,
# only in FROM. Decoupling PYTHON_VERSION from UV_VERSION this way (instead
# of a combined python-version+uv-version tag) matters because Astral
# doesn't publish every combination of the two, so a pinned UV_VERSION can
# 404 against an arbitrary PYTHON_VERSION with the combined-tag approach.
# ghcr.io/astral-sh/uv:${UV_VERSION} always resolves, "latest" included.
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# ---------- build ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS build
COPY --from=uv /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies first, for layer caching.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-default-groups

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-default-groups

# ---------- runtime ----------
FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY --from=build --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH"

USER app
CMD ["python", "-c", "import {{ cookiecutter.__module_name }}; print({{ cookiecutter.__module_name }}.__version__)"]
{%- if cookiecutter.include_devcontainer == "yes" %}

# ---------- dev ----------
# Local dev container. Referenced by .devcontainer/devcontainer.json's
# `build.target` -- one Dockerfile to maintain instead of two, and the dev
# environment is guaranteed to match what actually ships (same base image,
# same uv, same non-root user) instead of drifting from a generic
# third-party devcontainer image.
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
{%- endif %}
