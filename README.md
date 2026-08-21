# py-package-template

A [Cookiecutter](https://cookiecutter.readthedocs.io) / [Cruft](https://cruft.github.io/cruft/)
template for a **standalone Python package** — one repository, one distribution.

Built on `uv` + `hatchling` + `ruff`, with CI for GitHub Actions, GitLab CI, or both.

## Use it

```bash
uv tool install cruft
cruft create git@github.com:<you>/py-package-template.git
```

Use the **SSH** URL if the template repo is private: GitHub has not accepted
passwords for git operations since 2021, so an HTTPS clone will fail unless you
have a token configured (`gh auth login && gh auth setup-git`).

## Options

| Variable | Values | Notes |
| --- | --- | --- |
| `license` | MIT, Apache-2.0, BSD-3-Clause, GPL-3.0-or-later, Proprietary | Apache/GPL write a short notice; fetch the full text before publishing |
| `python_version` / `min_python_version` | e.g. `3.12` / `3.11` | Both end up in the CI test matrix |
| `ci_platform` | github, gitlab, both | Unused pipeline files are deleted |
| `type_checker` | mypy, ty, none | mypy is configured `strict` |
| `include_docs` | yes, no | MkDocs Material + mkdocstrings |
| `include_precommit` | yes, no | ruff, uv-lock, conventional-commit hooks |
| `include_devcontainer` | yes, no | |
| `include_docker` | no, yes | Multi-stage build/runtime/dev Dockerfile |
| `include_danger` | no, yes | Danger.js in TypeScript, works on both platforms |
| `publish_to_pypi` | no, yes | Trusted publishing on GitHub, `uv publish` on GitLab |

## What you get

```
my-package/
├── pyproject.toml          # uv + hatchling, dependency-groups, poe tasks
├── ruff.toml               # lint + format config
├── src/my_package/         # src layout, with py.typed
├── tests/
├── .github/workflows/      # ci.yml + release.yml
├── .gitlab-ci.yml          # + .gitlab/ci/{lint,test,build,danger}.yml
└── docs/, Dockerfile, .devcontainer/, scripts/danger/   (optional)
```

Tasks: `uv run poe fmt | lint | types | test | cov | licenses | docs | check | all`.

## Keeping projects up to date

`cruft` records the template commit in `.cruft.json`. After you improve the
template, run `cruft update` inside any generated project to pull the changes in
as a diff.
