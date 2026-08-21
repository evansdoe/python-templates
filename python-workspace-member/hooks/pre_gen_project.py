"""Validate answers and check that we are inside a uv workspace."""

from __future__ import annotations

import re
import sys
from pathlib import Path

MODULE = "{{ cookiecutter.__module_name }}"
SLUG = "{{ cookiecutter.__project_slug }}"

errors: list[str] = []

if not re.fullmatch(r"[a-z_][a-z0-9_]*", MODULE):
    errors.append(f"'{MODULE}' is not a valid Python module name.")
if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*[a-z0-9]", SLUG):
    errors.append(f"'{SLUG}' is not a valid PEP 508 distribution name.")

if errors:
    for err in errors:
        print(f"ERROR: {err}", file=sys.stderr)
    sys.exit(1)

# cookiecutter runs the pre-gen hook in a temporary directory, so look upward
# from the requested output directory instead.
here = Path.cwd()
candidates = [here, *here.parents]
in_workspace = any(
    (parent / "pyproject.toml").is_file()
    and "[tool.uv.workspace]" in (parent / "pyproject.toml").read_text(encoding="utf-8")
    for parent in candidates[:4]
)
if not in_workspace:
    print(
        "WARNING: no [tool.uv.workspace] found in a parent directory.\n"
        "         Generate this inside a workspace, e.g.\n"
        "             cruft create <url> --output-dir projects/\n"
        "         from the workspace root.",
        file=sys.stderr,
    )
