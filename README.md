# Python project templates

Three Cookiecutter / Cruft templates for `uv`-based Python projects: PyPI and
public container images throughout, with CI that works on GitHub Actions,
GitLab CI, or both.

## Which one?

```
Is this repo going to hold more than one Python project?
│
├── No  ──────────────────────────────►  python-package-template
│                                        one repo, one distribution
│
└── Yes ──────────────────────────────►  python-workspace-template   (once, for the repo)
                                         then python-workspace-member (per project)
```

| Template                                             | Use for                                            |
| ----------------------------------------------------- | -------------------------------------------------- |
| [`python-package-template`](python-package-template)         | A standalone repo shipping a single Python package |
| [`python-workspace-template`](python-workspace-template)     | A uv-workspace monorepo root hosting many projects |
| [`python-workspace-member`](python-workspace-member)         | Adding a project inside an existing workspace      |

All three live in this one repository. Cruft/Cookiecutter target a specific
template with `--directory`:

```bash
uv tool install cruft
cruft create git@github.com:evansdoe/python-templates.git --directory python-package-template
cruft create git@github.com:evansdoe/python-templates.git --directory python-workspace-template
cruft create git@github.com:evansdoe/python-templates.git --directory python-workspace-member --output-dir projects/
```

`cruft update` remembers the `directory` it was created with (recorded in the
generated project's `.cruft.json`), so later updates need no extra flag.

## Shared stack

`uv` (workspaces, lockfile, publishing) · `hatchling` · `ruff` (lint + format) ·
`mypy` **or** `ty` **or** neither · `pytest` + `pytest-cov` · `poethepoet` tasks ·
`licensecheck` · optional MkDocs Material, pre-commit, devcontainer, Dockerfile,
and Danger.js (TypeScript, works on GitHub and GitLab).

Every generated project answers to the same commands:

```bash
uv run poe fmt | lint | types | test | cov | check | all
```

## Agent tooling

Every generated project is set up for coding agents as well as people. The
same files serve Claude Code, GitHub Copilot and other agents that read
`AGENTS.md`:

- `AGENTS.md`, the short entry point (`CLAUDE.md` only imports it);
- `docs/PLAN.md` and `docs/design/package-map.md` per package or member, with
  the package map enforced by an import-linter contract and
  `tests/test_architecture.py`;
- the skills `dev-workflow` (example map, predictive TDD, gates, one pull
  request) and `python-design` (where code lives and when to split), plus an
  optional `tdd-refactor` subagent;
- with `include_architecture_docs=yes`, two skills and a checker that keep an
  engineering and an executive architecture document in step with the code.

Each template's README lists the exact files.

## Workspace conventions

- **Root shape** — `root_kind=virtual` (default) for a repo of independently
  released projects; `root_kind=application` when the repo ships one deliverable
  composed of internal libraries.
- **Dependencies** — the `members = ["projects/*"]` glob decides membership, not
  dependency edges. A dependency is only needed where one package *imports*
  another, and always comes in two parts: the name in `dependencies` plus a
  `{ workspace = true }` entry in `[tool.uv.sources]`.
- **Ruff** — one root `ruff.toml`. Members inherit it by having no config of
  their own. A member that must deviate uses `extend = "../../ruff.toml"`;
  a bare member config silently replaces the root ruleset with ruff's defaults.

## Verified

Each template's `tests/test_bake.py` bakes it across its parameter matrix and
checks the output: no unrendered Jinja, valid YAML, correct feature-toggle
routing, and (behind `--run-slow`) an actual `uv sync`. The same tests check
the agent files: every generated `AGENTS.md` stays within 60 lines; no bake
contains a private name or an absolute home path; the package and workspace
agent files contain no ticket ID; their skills and agents are identical;
and their READMEs name every option and agent file. A separate
[`integration.yml`](.github/workflows/integration.yml) workflow bakes a
workspace plus two members — one depending on the other — and runs
`uv sync` / `uv lock --check` over the assembled result, since that pairing
can't be verified by testing either template alone. All of this runs in CI
on every push and PR, scoped by path so a change to one template doesn't
trigger the others' workflows.
