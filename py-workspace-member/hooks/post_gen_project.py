"""Prune optional files and print next steps."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path.cwd()
SLUG = "{{ cookiecutter.__project_slug }}"
KIND = "{{ cookiecutter.project_kind }}"
DOCS = "{{ cookiecutter.include_docs }}" == "yes"
CUSTOM_PIPELINE = "{{ cookiecutter.custom_gitlab_pipeline }}" == "yes"
RUFF_OVERRIDE = "{{ cookiecutter.ruff_override }}" == "yes"
DEPS = [d.strip() for d in "{{ cookiecutter.member_dependencies }}".split(",") if d.strip()]


def drop(*relative_paths: str) -> None:
    for rel in relative_paths:
        target = ROOT / rel
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


if not DOCS:
    drop("docs")
if not CUSTOM_PIPELINE:
    drop(".gitlab-ci.yml")
if not RUFF_OVERRIDE:
    drop("ruff.toml")
if KIND != "application":
    drop("src/{{ cookiecutter.__module_name }}/__main__.py")

line = "=" * 72
print(f"\n{line}\n  Created workspace member: {SLUG}\n{line}\n")
print("  From the workspace root:\n")
print("    uv sync --all-packages --all-groups")
print(f"    uv run --package {SLUG} pytest projects/{SLUG}\n")
print('  Nothing else to wire up: the members = ["projects/*"] glob picks it')
print("  up, and CI discovers it automatically.\n")

if DEPS:
    print(f"  Declared workspace dependencies: {', '.join(DEPS)}")
    print("  Each is wired through [tool.uv.sources] with workspace = true.\n")

# If the workspace root is an application root, new members have to be
# registered there by hand; a virtual root needs nothing.
for parent in list(Path.cwd().parents)[:3]:
    root = parent / "pyproject.toml"
    if root.is_file():
        text = root.read_text(encoding="utf-8")
        if "[tool.uv.workspace]" in text and "[project]" in text:
            print("  This workspace has an APPLICATION root. If the root should")
            print("  depend on this member, add it there:\n")
            print(f'    dependencies = [..., "{SLUG}"]')
            print("    [tool.uv.sources] entry:")
            print(f"    {SLUG} = " + "{ workspace = true }\n")
        break
print(f"{line}\n")
