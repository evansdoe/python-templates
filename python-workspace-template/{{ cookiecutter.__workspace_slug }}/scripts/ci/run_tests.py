#!/usr/bin/env python3
"""Run pytest for the whole workspace.

pytest exits with status 5 when it collects no tests. A new workspace has no
members yet, so that is expected there and must not fail ``poe test`` or
``poe all``. Once any test file exists, status 5 is a real failure again.

Extra arguments are passed on to pytest.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NO_TESTS_COLLECTED = 5


def has_test_files(root: Path) -> bool:
    """Return whether the workspace root or any member holds a test file."""
    patterns = ("tests/**/test_*.py", "projects/*/tests/**/test_*.py")
    return any(next(root.glob(pattern), None) for pattern in patterns)


def exit_status(code: int, root: Path) -> int:
    """Map pytest's exit status; "no tests collected" is fine in an empty workspace."""
    if code == NO_TESTS_COLLECTED and not has_test_files(root):
        return 0
    return code


def main() -> int:
    """Run pytest and return its adjusted exit status."""
    command = [sys.executable, "-m", "pytest", *sys.argv[1:]]
    return exit_status(subprocess.run(command, cwd=ROOT, check=False).returncode, ROOT)


if __name__ == "__main__":
    sys.exit(main())
