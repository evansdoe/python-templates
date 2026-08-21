# python-workspace-member

A Cookiecutter / Cruft template for a **single project inside an existing uv
workspace** (see [`python-workspace-template`](../python-workspace-template)).

## Use it

Run from the **workspace root**, generating into `projects/`:

```bash
cruft create git@github.com:evansdoe/python-templates.git --directory python-workspace-member --output-dir projects/
uv sync --all-packages --all-groups
```

Nothing else to wire up: the `members = ["projects/*"]` glob picks the project
up, and CI discovers it automatically.

## Options

| Variable                 | Values                                           | Notes                                                                                                                                          |
| ------------------------ | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `project_kind`           | library, application, research                   | `application` adds a `__main__.py` and a console script; `research` marks it not-for-upload                                                    |
| `include_docs`           | no, yes                                          | A `docs/` stub                                                                                                                                 |
| `custom_gitlab_pipeline` | no, yes                                          | Emits a member `.gitlab-ci.yml` that the workspace triggers instead of the default test job — for extra services, longer timeouts, GPU runners |
| `member_dependencies`    | comma-separated names, e.g. `geo-core, io-utils` | Sibling members this project imports; writes both `dependencies` and `[tool.uv.sources]`                                                       |
| `ruff_override`          | no, yes                                          | Emits a `ruff.toml` containing only `extend = "../../ruff.toml"`                                                                               |

The template warns if it cannot find `[tool.uv.workspace]` in a parent
directory, which usually means you ran it from the wrong place.

## Depending on another member

Membership in the workspace does **not** create a dependency. If this project
imports a sibling, it needs both halves:

```toml
dependencies = ["geo-core"]

[tool.uv.sources]
geo-core = { workspace = true }
```

Without the `[tool.uv.sources]` entry uv resolves `geo-core` from PyPI and
`uv lock` fails. `member_dependencies` writes both for you. `uv sync --package
<name>` then pulls the sibling in automatically, so the CI job needs no change.

## Ruff

By default a member has no ruff config and inherits the workspace root. Ruff
does not merge configs — the nearest one wins outright — so a bare `ruff.toml`
or a `[tool.ruff]` section in `pyproject.toml` would silently drop every root
rule for this member. `ruff_override=yes` generates a stub that starts from
`extend = "../../ruff.toml"`; add only the deltas beneath it.

## Working on a member

```bash
uv run --package <name> pytest projects/<name>
uv add --package <name> httpx           # dependency for this member only
```

Shared tooling (ruff, pytest, the type checker, poe) stays in the workspace
root. A member declares only its own runtime dependencies plus a `test`
dependency group, so `uv sync --package <name> --group test` works in isolation
in CI.
