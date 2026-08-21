# py-workspace-template

A Cookiecutter / Cruft template for a **uv workspace monorepo** — one repository
hosting many Python projects that share a single `uv.lock` and one dev toolchain.

Pair it with [`py-workspace-member`](../py-workspace-member) to add projects.

## Use it

```bash
cruft create git@github.com:<you>/py-workspace-template.git
cd my-workspace
uv sync --all-packages --all-groups     # creates uv.lock — commit it
```

## Layout

```
my-workspace/
├── pyproject.toml          # virtual root: members = ["projects/*"], shared dev groups
├── uv.lock                 # one lockfile for every member
├── ruff.toml               # shared lint config
├── scripts/ci/discover_projects.py
└── projects/
    ├── geo-core/
    └── bench-cli/
```

## CI model

Lint, format, type checks and the license audit run **once** at the root over
every member. Tests run **per member**, and only for members the change touches.

The list of members is discovered at runtime by
`scripts/ci/discover_projects.py`, so **adding a project never requires editing a
pipeline file**:

- **GitHub Actions** — a `discover` job emits a JSON matrix; `test` fans out over it.
- **GitLab CI** — `generate-child-pipeline` writes `child-pipelines.yml`, which the
  `projects` job triggers. A member that ships its own `.gitlab-ci.yml` gets
  triggered as a child pipeline instead of the default test job.

Changes to `pyproject.toml`, `uv.lock`, `ruff.toml`, `scripts/` or the CI config
count as affecting every member.

Try the discovery locally:

```bash
uv run poe projects                                        # all members
python scripts/ci/discover_projects.py --format github --base main
python scripts/ci/discover_projects.py --format gitlab --base main
```

## Root shape: `root_kind`

| | `virtual` (default) | `application` |
| --- | --- | --- |
| Repo ships | several independently released projects | one deliverable built from internal libraries |
| Root `pyproject.toml` | no `[project]` table | a real package with `src/` and a console script |
| Members are wired by | the `members = ["projects/*"]` glob alone | the glob, **plus** `dependencies` + `[tool.uv.sources]` for each member the root uses |
| Adding a member | nothing to edit | register it in the root if the root uses it |

Membership never comes from a dependency edge: in both shapes `uv sync` installs
every member editable and the single `uv.lock` covers all of them. Declaring a
dependency only matters when one package *imports* another — root to member, or
member to member — and it always needs the `[tool.uv.sources]` half:

```toml
dependencies = ["geo-core"]

[tool.uv.sources]
geo-core = { workspace = true }
```

Without the sources entry uv looks for `geo-core` on PyPI and `uv lock` fails
with *"is included as a workspace member, but is missing an entry in
`tool.uv.sources`"*.

## Options

`license`, `python_version`, `min_python_version`, `ci_platform`
(github/gitlab/both), `type_checker` (mypy/ty/none), `include_docs`,
`include_precommit`, `include_devcontainer`, `include_danger`.

## Note on type checking

The root mypy config excludes `projects/*/tests/`: members legitimately reuse
test file names (`tests/test_smoke.py` in each), which mypy cannot map to
distinct modules. Pytest handles them via `--import-mode=importlib`.
