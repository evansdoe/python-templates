#!/usr/bin/env python3
"""Run licensecheck for every package in the workspace.

licensecheck checks the dependencies in the ``[project]`` table of the folder
it runs from. A virtual workspace root has no such table: older licensecheck
releases crash there, and newer ones report "No packages" and pass without
checking anything. So this script runs licensecheck once in each member's
folder, and in the root when the root is a package itself, and fails when any
of those runs fails.

Extra arguments are passed on to licensecheck, for example ``--zero``.
"""

from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def is_package(pyproject: Path) -> bool:
    """Return whether a pyproject.toml declares a package (a ``[project]`` table)."""
    if not pyproject.is_file():
        return False
    with pyproject.open("rb") as handle:
        return "project" in tomllib.load(handle)


def targets(root: Path) -> list[Path]:
    """Return the folders to check: a package root first, then each member."""
    folders = [root] if is_package(root / "pyproject.toml") else []
    members = sorted(path.parent for path in root.glob("projects/*/pyproject.toml"))
    packages = [member for member in members if is_package(member / "pyproject.toml")]
    return folders + packages


def combined(codes: list[int]) -> int:
    """Return the first non-zero exit status, or 0 when every run passed."""
    return next((code for code in codes if code), 0)


def main() -> int:
    """Run licensecheck in every target folder and return the combined status."""
    folders = targets(ROOT)
    if not folders:
        print("No package to check yet: the workspace has no members.")
        return 0
    codes = []
    for folder in folders:
        print(f"== licensecheck: {folder.relative_to(ROOT).as_posix()}", flush=True)
        command = [sys.executable, "-m", "licensecheck", *sys.argv[1:]]
        codes.append(subprocess.run(command, cwd=folder, check=False).returncode)
    return combined(codes)


if __name__ == "__main__":
    sys.exit(main())
