# python-package-template

A [Cookiecutter](https://cookiecutter.readthedocs.io) / [Cruft](https://cruft.github.io/cruft/)
template for a **standalone Python package** — one repository, one distribution.

Built on `uv` + `hatchling` + `ruff`, with CI for GitHub Actions, GitLab CI, or both.

## Use it

```bash
uv tool install cruft
cruft create git@github.com:evansdoe/python-templates.git --directory python-package-template
```

Use the **SSH** URL if the template repo is private: GitHub has not accepted
passwords for git operations since 2021, so an HTTPS clone will fail unless you
have a token configured (`gh auth login && gh auth setup-git`).

## Options

| Variable                                | Values                                                       | Notes                                                                  |
| --------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------- |
| `license`                               | MIT, Apache-2.0, BSD-3-Clause, GPL-3.0-or-later, Proprietary | Apache/GPL write a short notice; fetch the full text before publishing |
| `python_version` / `min_python_version` | e.g. `3.14` / `3.14`                                         | Both end up in the CI test matrix                                      |
| `uv_version`                            | `latest` or a pin, e.g. `0.12.5`                             | `latest` tracks the newest uv release everywhere it's referenced      |
| `ci_platform`                           | github, gitlab, both                                         | Unused pipeline files are deleted                                      |
| `type_checker`                          | mypy, ty, none                                               | mypy is configured `strict`                                            |
| `include_docs`                          | yes, no                                                      | MkDocs Material + mkdocstrings                                         |
| `include_precommit`                     | yes, no                                                      | ruff, uv-lock, conventional-commit hooks                               |
| `include_devcontainer`                  | yes, no                                                      | See below for how this interacts with `include_docker`                |
| `include_docker`                        | no, yes                                                      | Multi-stage build/runtime/dev Dockerfile                               |
| `include_danger`                        | no, yes                                                      | Danger.js in TypeScript, works on both platforms                       |
| `publish_to_pypi`                       | no, yes                                                      | Trusted publishing on GitHub, `uv publish` on GitLab                   |

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

## Danger.js rules (`include_danger`)

The rule logic lives in `scripts/danger/danger-rules.ts` as a single
`runDanger(config)` export, not inline in `dangerfile.ts` — `dangerfile.ts`
itself is just:

```ts
import { runDanger } from "./danger-rules";
runDanger({
  // maxCommitsPerAuthor: 5,
  // requireCommitSigning: true,
});
```

Built in, on by default: Conventional Commits PR/MR title, a minimum
description length, a changelog/tests reminder when `src/` changes, and a
changed-lines-of-code size guard. Two more are off by default — pass them in
`dangerfile.ts`'s config object to turn them on:

| Option                 | Default | Effect                                                                                     |
| ----------------------- | ------- | ------------------------------------------------------------------------------------------- |
| `maxCommitsPerAuthor`   | `0` (off) | Warns when one author has more than this many commits on the PR/MR                        |
| `requireCommitSigning`  | `false`   | GitHub: fails on any unsigned commit. GitLab: Danger's MR DSL can't see commit signatures, so this posts an informational message pointing at **Settings → Repository → Push Rules → Reject unsigned commits** instead |

Every other threshold (`minDescriptionLength`, `maxLinesChanged`, etc.) is
also overridable the same way, or set to `0`/`false` to disable that check
entirely. `dangerfile.ts` is intentionally the only file you'd ever touch —
`danger-rules.ts` is the shared, tested module.

Linting for the danger scripts themselves runs through
[Biome](https://biomejs.dev) (`pnpm lint` / `pnpm format`), which both CI
platforms run before `danger ci --failOnErrors`.

## Devcontainer (`include_devcontainer`)

When `include_docker=yes`, the devcontainer builds from the same
`Dockerfile` as the production image — `target: dev`, a stage with the
same base image and `uv`, plus git/ssh/curl for day-to-day dev work — so
the dev environment can't drift from what actually ships. There's one
Dockerfile to maintain, not two.

When `include_docker=no`, there's no Dockerfile to build from, so the
devcontainer falls back to a generic `mcr.microsoft.com/devcontainers/python`
image with a `uv` feature layered on. Functionally fine, just decoupled
from the rest of the project.

## Keeping projects up to date

`cruft` records the template commit in `.cruft.json`. After you improve the
template, run `cruft update` inside any generated project to pull the changes in
as a diff.
