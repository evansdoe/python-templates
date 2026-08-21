"""Validate cookiecutter answers before the project is generated."""

from __future__ import annotations

import re
import sys

MODULE = "{{ cookiecutter.__module_name }}"
SLUG = "{{ cookiecutter.__package_slug }}"
MIN_PY = "{{ cookiecutter.min_python_version }}"
PY = "{{ cookiecutter.python_version }}"

errors: list[str] = []

if not re.fullmatch(r"[a-z_][a-z0-9_]*", MODULE):
    errors.append(
        f"'{MODULE}' is not a valid Python module name. "
        "Use letters, digits and underscores, and do not start with a digit."
    )

if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*[a-z0-9]", SLUG):
    errors.append(f"'{SLUG}' is not a valid PEP 508 distribution name.")

for label, value in (("min_python_version", MIN_PY), ("python_version", PY)):
    if not re.fullmatch(r"3\.\d+", value):
        errors.append(f"{label} must look like '3.12', got '{value}'.")

if not errors and tuple(map(int, MIN_PY.split("."))) > tuple(map(int, PY.split("."))):
    errors.append(f"min_python_version ({MIN_PY}) is newer than python_version ({PY}).")

if errors:
    for err in errors:
        print(f"ERROR: {err}", file=sys.stderr)
    sys.exit(1)
