#!/usr/bin/env python3
"""Run mypy on the workspace's own code and on every member's source.

mypy fails on a listed folder that holds no Python file, and a new workspace
has no members yet, so the member folders are found here when mypy runs
instead of being listed in pyproject.toml. Member tests are left out: members
reuse test file names (tests/test_smoke.py in each), which mypy cannot map to
distinct modules; pytest checks them with --import-mode=importlib.

Extra arguments are passed on to mypy.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def targets(root: Path) -> list[str]:
    """Return the folders mypy checks, relative to the workspace root."""
    own = [name for name in ("src", "tests", "scripts") if (root / name).is_dir()]
    members = sorted(
        path.relative_to(root).as_posix()
        for path in root.glob("projects/*/src")
        if path.is_dir()
    )
    return own + members


def main() -> int:
    """Run mypy and return its exit status."""
    command = [sys.executable, "-m", "mypy", *targets(ROOT), *sys.argv[1:]]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
