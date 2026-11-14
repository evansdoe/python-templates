"""Prune files the user opted out of, then print next steps."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path.cwd()

CI = "{{ cookiecutter.ci_platform }}"
SLUG = "{{ cookiecutter.__package_slug }}"
OPTIONS = {
    "docs": "{{ cookiecutter.include_docs }}" == "yes",
    "precommit": "{{ cookiecutter.include_precommit }}" == "yes",
    "devcontainer": "{{ cookiecutter.include_devcontainer }}" == "yes",
    "docker": "{{ cookiecutter.include_docker }}" == "yes",
    "danger": "{{ cookiecutter.include_danger }}" == "yes",
    "architecture_docs": "{{ cookiecutter.include_architecture_docs }}" == "yes",
}


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
    drop(".github/workflows")  # .github/skills and .github/agents stay


if not OPTIONS["architecture_docs"]:
    drop(
        ".github/skills/document-executive-architecture",
        ".github/skills/document-engineering-architecture",
    )


def link_skills() -> None:
    """Expose each .github/skills/<name> to Claude Code as .claude/skills/<name>."""
    claude_skills = ROOT / ".claude" / "skills"
    claude_skills.mkdir(parents=True, exist_ok=True)
    for skill in sorted((ROOT / ".github" / "skills").iterdir()):
        link = claude_skills / skill.name
        try:
            link.symlink_to(Path("..", "..", ".github", "skills", skill.name))
        except OSError:  # e.g. Windows without Developer Mode: copy instead
            shutil.copytree(skill, link)


link_skills()

if not OPTIONS["danger"]:
    drop("scripts/danger", ".gitlab/ci/danger.yml")
if not OPTIONS["docs"]:
    # Only the MkDocs site; docs/PLAN.md and docs/design/ are always kept.
    drop("mkdocs.yml", "docs/index.md", "docs/api.md")
if not OPTIONS["precommit"]:
    drop(".pre-commit-config.yaml")
if not OPTIONS["devcontainer"]:
    drop(".devcontainer")
if not OPTIONS["docker"]:
    drop("Dockerfile", ".dockerignore")

scripts = ROOT / "scripts"
if scripts.is_dir() and not any(scripts.iterdir()):
    scripts.rmdir()

line = "=" * 72
print(f"\n{line}\n  Created: {SLUG}\n{line}\n")
print("  Next steps:\n")
print(f"    cd {SLUG}")
print("    git init -b main && git add -A && git commit -m 'chore: initial commit'")
print("    uv sync --all-groups")
if OPTIONS["precommit"]:
    print("    uv run pre-commit install")
print("    uv run poe all\n")
if OPTIONS["danger"]:
    print("  Danger.js needs a lockfile before CI will pass:\n")
    print("    (cd scripts/danger && pnpm install)")
    print("    git add scripts/danger/pnpm-lock.yaml\n")
print(f"{line}\n")
