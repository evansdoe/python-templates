# syntax=docker/dockerfile:1

ARG PYTHON_VERSION={{ cookiecutter.python_version }}
ARG UV_VERSION=0.5.29

# ---------- build ----------
FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_VERSION}-bookworm-slim AS build

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

# ---------- dev ----------
FROM build AS dev
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked --all-groups
ENV PATH="/app/.venv/bin:$PATH"
CMD ["bash"]
