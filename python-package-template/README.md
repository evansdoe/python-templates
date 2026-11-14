# python-package-template

A [Cookiecutter](https://cookiecutter.readthedocs.io) / [Cruft](https://cruft.github.io/cruft/)
template for a **standalone Python package** — one repository, one distribution.

Built on `uv` + `hatchling` + `ruff`, with CI for GitHub Actions, GitLab CI, or both.

## Use it

```bash
uv tool install cruft
cruft create git@github.com:evansdoe/python-templates.git --directory python-package-template
```

The repository is public, so the HTTPS URL
(`https://github.com/evansdoe/python-templates.git`) works as well as SSH. For
a private copy, use SSH or configure a token (`gh auth login && gh auth
setup-git`): GitHub has not accepted passwords for git operations since 2021.

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
| `include_architecture_docs`             | no, yes                                                      | Architecture-document skills and `docs/architecture/` checker          |
| `publish_to_pypi`                       | no, yes                                                      | Trusted publishing on GitHub, `uv publish` on GitLab                   |

## What you get

```
my-package/
├── pyproject.toml          # uv + hatchling, dependency-groups, poe tasks, import contract
├── ruff.toml               # lint + format config, with function size limits
├── AGENTS.md               # instructions for coding agents; CLAUDE.md imports it
├── src/my_package/         # src layout, with py.typed
├── tests/                  # test_architecture.py, unit/ mirrors the package
├── docs/PLAN.md            # concerns, decisions log, open questions
├── docs/design/package-map.md
├── .github/skills/         # dev-workflow, python-design (+ architecture skills)
├── .github/agents/         # tdd-refactor subagent (Copilot); .claude/ holds the Claude Code copies
├── .github/workflows/      # ci.yml + release.yml
├── .gitlab-ci.yml          # + .gitlab/ci/{lint,test,build,danger}.yml
└── Dockerfile, .devcontainer/, scripts/danger/   (optional)
```

Tasks: `uv run poe fmt | lint | types | test | cov | licenses | docs | check | all`.

## Agent tooling

Every generated package carries instructions for coding agents, so an agent
plans, tests and places code the way the project owner expects. These files
are always baked; only the architecture skills are optional.

| Path | Purpose |
| --- | --- |
| `AGENTS.md` | Entry point: where things are, the commands, the rules. `CLAUDE.md` contains only `@AGENTS.md`, so Claude Code reads the same text. Kept to 60 lines by a test. |
| `docs/PLAN.md` | The concerns (one branch each), the decisions log and the open questions. |
| `docs/design/package-map.md` | The sub-packages the owner approved: role, what belongs there, what each may import. |
| `[tool.importlinter]` + `tests/test_architecture.py` | The package map as an exhaustive `layers` contract, run by pytest, which also checks that `tests/unit/` mirrors the package. |
| `.github/skills/dev-workflow` | How a change is made: example map, predictive TDD, a pace the owner chooses, gates through `poe`, one pull request. `references/pace.md` covers unattended runs. |
| `.github/skills/python-design` | Where code lives and what shape it takes, and when a module, class or sub-package is justified. |
| `.github/agents/tdd-refactor.agent.md`, `.claude/agents/tdd-refactor.md` | Optional subagent that runs the Refactor step in a fresh context. |
| `.claude/skills` | Symlinks to `.github/skills`, so Claude Code finds the same skills. |

`ruff.toml` enables the size rules `PLR0911`, `PLR0912`, `PLR0913` and
`PLR0915`. When one fires, the skills tell the agent to propose a split by
responsibility, not to raise the limit or add `noqa`.

## Architecture documents (`include_architecture_docs`)

Off by default. When on, the package also gets the
`.github/skills/document-engineering-architecture` and
`document-executive-architecture` skills and a checker,
`scripts/check_architecture_doc.py` inside the engineering skill. After an
architecture-affecting change, an agent runs both skills to create or update
`docs/architecture/engineering.md` and `docs/architecture/executive.md`, and
edits them only through the skills. The checker validates their structure,
provenance, links and Mermaid diagrams (exit 0: no issues, 1: issues,
2: usage or path error). The pages are excluded from the MkDocs site.

## Danger.js rules (`include_danger`)

The rule logic lives in [`danger-rules`](https://github.com/evansdoe/danger-rules),
a small shared package pinned by tag in `scripts/danger/package.json` —
not a local file, and not inline in `dangerfile.ts`. It's shared with
`python-workspace-template` so a fix lands in one place instead of two
copies that can silently drift apart. `dangerfile.ts` itself is just:

```ts
import { runDanger } from "danger-rules";
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
see the [`danger-rules` README](https://github.com/evansdoe/danger-rules)
for the full rule set and why it imports things the way it does.

Linting for the danger scripts themselves runs through
[Biome](https://biomejs.dev) (`pnpm lint` / `pnpm format`), which both CI
platforms run before `danger ci --failOnErrors`.

On GitHub the job requests `contents: read` and `pull-requests: write`. A
repository whose default workflow permissions are read-only caps what any job
may request, so if Danger still returns 403 *Resource not accessible by
integration*, raise that default under **Settings -> Actions -> General ->
Workflow permissions**. Pull requests from forks always get a read-only token
whatever the job asks for, so Danger cannot comment on those.

The job runs on `pull_request`, including the `edited` action, so correcting a
title or a description re-runs it without needing a new commit.

## Docker (`include_docker`)

Three stages: `build` resolves dependencies with uv, `runtime` ships them on a
slim base as a non-root user, and `dev` (present when
`include_devcontainer=yes`) backs the devcontainer. `runtime` is deliberately
last, because `docker build` builds the last stage unless told otherwise:

```bash
docker build -t my-package .                    # runtime image
docker build --target dev -t my-package:dev .   # what the devcontainer builds
```

`.dockerignore` keeps `.env`, caches and any `node_modules/` out of the build
context, so `COPY . /app` cannot bake secrets into an image.

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
