#!/usr/bin/env python3
"""Discover workspace members, optionally filtered to those affected by a diff.

Used by CI so that adding a project under ``projects/`` requires no pipeline edits.

Examples:
    python scripts/ci/discover_projects.py --format list --all
    python scripts/ci/discover_projects.py --format github --base origin/main
    python scripts/ci/discover_projects.py --format gitlab -o child.yml
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECTS_DIR = ROOT / "projects"

# A change to any of these invalidates every member, so all of them are rebuilt.
SHARED_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "ruff.toml",
    ".github/",
    ".gitlab/",
    ".gitlab-ci.yml",
    "scripts/",
    "src/",
    "tests/",
)


def all_projects() -> list[str]:
    """Return the sorted directory names of every workspace member."""
    if not PROJECTS_DIR.is_dir():
        return []
    return sorted(
        p.name for p in PROJECTS_DIR.iterdir() if (p / "pyproject.toml").is_file()
    )


def changed_files(base: str) -> list[str]:
    """Return files changed between ``base`` and HEAD, or [] if git cannot tell."""
    for rev_range in (f"{base}...HEAD", f"{base}..HEAD"):
        result = subprocess.run(
            ["git", "diff", "--name-only", rev_range],
            capture_output=True,
            text=True,
            cwd=ROOT,
            check=False,
        )
        if result.returncode == 0:
            return [line for line in result.stdout.splitlines() if line]
    print(f"warning: could not diff against {base}; assuming all", file=sys.stderr)
    return []


def affected_projects(base: str) -> list[str]:
    """Return members touched by the diff, or all of them if shared files changed."""
    every = all_projects()
    files = changed_files(base)
    if not files:
        return every
    if any(f.startswith(SHARED_PATHS) for f in files):
        return every
    touched = {
        parts[1]
        for f in files
        if len(parts := f.split("/")) > 2 and parts[0] == "projects"
    }
    return [name for name in every if name in touched]


def gitlab_yaml(projects: list[str]) -> str:
    """Render a GitLab child pipeline that tests each affected member."""
    header = (
        "default:\n"
        "  image: $UV_IMAGE\n"
        "  cache:\n"
        "    key:\n"
        "      files:\n"
        "        - uv.lock\n"
        "    paths:\n"
        "      - .uv-cache\n"
        "\n"
        "stages:\n"
        "  - test\n\n"
    )
    if not projects:
        return (
            header
            + "no-op:\n  stage: test\n  script:\n    - echo 'Nothing affected.'\n"
        )
    blocks = []
    for name in projects:
        if (PROJECTS_DIR / name / ".gitlab-ci.yml").is_file():
            blocks.append(
                f"{name}:\n"
                f"  stage: test\n"
                f"  trigger:\n"
                f"    include: projects/{name}/.gitlab-ci.yml\n"
                f"    strategy: depend\n"
            )
        else:
            blocks.append(
                f"{name}:\n"
                f"  stage: test\n"
                f"  script:\n"
                f"    - uv sync --package {name} --no-default-groups --group test\n"
                f"    - uv run --no-sync pytest projects/{name}"
                f" --cov=projects/{name} --cov-report=term"
                f" --junitxml=report-{name}.xml\n"
                f"  artifacts:\n"
                f"    reports:\n"
                f"      junit: report-{name}.xml\n"
                f"    when: always\n"
            )
    return header + "\n".join(blocks)


def main() -> int:
    """Parse arguments and emit the discovered members."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format", choices=("list", "github", "gitlab"), default="list"
    )
    parser.add_argument("--base", default="origin/main", help="git ref to diff against")
    parser.add_argument("--all", action="store_true", help="ignore the diff")
    parser.add_argument("-o", "--output", type=Path, help="write to a file")
    args = parser.parse_args()

    projects = all_projects() if args.all else affected_projects(args.base)

    if args.format == "list":
        text = "\n".join(projects)
    elif args.format == "github":
        text = json.dumps({"project": projects})
    else:
        text = gitlab_yaml(projects)

    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
