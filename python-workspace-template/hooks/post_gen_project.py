"""Prune files the user opted out of, then print next steps."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path.cwd()

CI = "{{ cookiecutter.ci_platform }}"
SLUG = "{{ cookiecutter.__workspace_slug }}"
DOCS = "{{ cookiecutter.include_docs }}" == "yes"
PRECOMMIT = "{{ cookiecutter.include_precommit }}" == "yes"
DEVCONTAINER = "{{ cookiecutter.include_devcontainer }}" == "yes"
DANGER = "{{ cookiecutter.include_danger }}" == "yes"
APPLICATION_ROOT = "{{ cookiecutter.root_kind }}" == "application"


def drop(*relative_paths: str) -> None:
    for rel in relative_paths:
        target = ROOT / rel
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


if CI == "github":
    drop(".gitlab-ci.yml", ".gitlab")
elif CI == "gitlab":
    drop(".github")

if not DANGER:
    drop("scripts/danger", ".gitlab/ci/danger.yml")
if not DOCS:
    drop("docs", "mkdocs.yml")
if not PRECOMMIT:
    drop(".pre-commit-config.yaml")
if not DEVCONTAINER:
    drop(".devcontainer")
if not APPLICATION_ROOT:
    drop("src", "tests")

line = "=" * 72
print(f"\n{line}\n  Created workspace: {SLUG}\n{line}\n")
print("  Next steps:\n")
print(f"    cd {SLUG}")
print("    git init -b main && git add -A && git commit -m 'chore: initial commit'")
print("    uv sync --all-packages --all-groups   # creates uv.lock — commit it\n")
if APPLICATION_ROOT:
    print("  This is an APPLICATION root: it is itself a package, and each member")
    print("  it uses must be added to both `dependencies` and [tool.uv.sources].\n")
print("  Add your first project (from the workspace root):\n")
print("    cruft create <python-workspace-member-url> --output-dir projects/")
print("    uv sync --all-packages --all-groups\n")
if DANGER:
    print("  Danger.js needs a lockfile before CI will pass:\n")
    print("    (cd scripts/danger && pnpm install)\n")
print(f"{line}\n")
