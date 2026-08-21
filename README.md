# Python project templates

Three Cookiecutter / Cruft templates for `uv`-based Python projects: PyPI and
public container images throughout, with CI that works on GitHub Actions,
GitLab CI, or both.

## Which one?

```
Is this repo going to hold more than one Python project?
│
├── No  ──────────────────────────────►  py-package-template
│                                        one repo, one distribution
│
└── Yes ──────────────────────────────►  py-workspace-template   (once, for the repo)
                                         then py-workspace-member (per project)
```

| Template                                                                     | Use for                                            |
| ---------------------------------------------------------------------------- | -------------------------------------------------- |
| [`py-package-template`](https://github.com/evansdoe/py-package-template)     | A standalone repo shipping a single Python package |
| [`py-workspace-template`](https://github.com/evansdoe/py-workspace-template) | A uv-workspace monorepo root hosting many projects |
| [`py-workspace-member`](https://github.com/evansdoe/py-workspace-member)     | Adding a project inside an existing workspace      |

## Shared stack

`uv` (workspaces, lockfile, publishing) · `hatchling` · `ruff` (lint + format) ·
`mypy` **or** `ty` **or** neither · `pytest` + `pytest-cov` · `poethepoet` tasks ·
`licensecheck` · optional MkDocs Material, pre-commit, devcontainer, Dockerfile,
and Danger.js (TypeScript, works on GitHub and GitLab).

Every generated project answers to the same commands:

```bash
uv run poe fmt | lint | types | test | cov | check | all
```

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

## Publishing these templates

```bash
cd py-package-template
git init -b main && git add -A && git commit -m "feat: initial template"
gh repo create py-package-template --private --source=. --push
```

Then generate from them with the **SSH** URL:

```bash
cruft create git@github.com:<you>/py-package-template.git
```

## Why the HTTPS clone failed

GitHub stopped accepting account passwords for git operations in 2021, and
private repos prompt for credentials rather than returning 404. So
`cruft create https://github.com/<you>/<private-template>` asks for a password
that can never work. Either use the SSH URL above, or configure a token once:

```bash
gh auth login && gh auth setup-git
```

`cruft` writes whichever URL you used into the generated project's
`.cruft.json`, and reuses it for `cruft update` — so prefer the SSH form for
private templates.

## Verified

Each template was generated in several configurations and the output checked:
all TOML/YAML/JSON parses, no unrendered Jinja, and for real workspaces with two
members under both root shapes — `ruff format --check`, `ruff check`,
`mypy --strict`, `pytest`, `mkdocs build --strict`, `licensecheck` and `uv build`
all pass on generated code, including root-to-member and member-to-member imports.
