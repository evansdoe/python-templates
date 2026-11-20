"""Licenses are checked once per member, because the workspace root is virtual.

licensecheck reads the `[project]` table in the folder it runs from. A virtual
workspace root has none: older releases crash there, and newer ones report "No
packages" and pass without checking anything. scripts/ci/run_licensecheck.py
runs it in every member's folder instead.
"""

import importlib.util
import os
import subprocess
import sys
import tomllib

import pytest
from test_bake import _add_member, bake

SCRIPT = "scripts/ci/run_licensecheck.py"
RUN = "uv run --no-sync python scripts/ci/run_licensecheck.py"


def load(root):
    """Import the baked script without running it."""
    spec = importlib.util.spec_from_file_location("run_licensecheck", root / SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def test_poe_and_ci_run_the_script(cookies):
    root = bake(cookies, ci_platform="both").project_path
    pyproject = tomllib.loads((root / "pyproject.toml").read_text())
    assert pyproject["tool"]["poe"]["tasks"]["licenses"] == f"python {SCRIPT}"
    assert pyproject["dependency-groups"]["license"] == ["licensecheck>=2026.0.7"]
    assert RUN in (root / ".github/workflows/ci.yml").read_text()
    assert RUN in (root / ".gitlab/ci/lint.yml").read_text()


def test_targets_are_the_members_and_a_package_root(cookies, tmp_path):
    module = load(bake(cookies).project_path)
    write(tmp_path / "pyproject.toml", "[tool.uv.workspace]\nmembers = ['projects/*']\n")
    write(tmp_path / "projects/ledger/pyproject.toml", "[project]\nname = 'ledger'\n")
    write(tmp_path / "projects/notes/pyproject.toml", "[project]\nname = 'notes'\n")
    write(tmp_path / "projects/scratch/notes.txt", "not a member\n")
    assert module.targets(tmp_path) == [tmp_path / "projects/ledger", tmp_path / "projects/notes"]
    write(tmp_path / "pyproject.toml", "[project]\nname = 'root'\n\n[tool.uv.workspace]\nmembers = ['projects/*']\n")
    assert module.targets(tmp_path)[0] == tmp_path


def test_the_first_failure_decides_the_exit_status(cookies):
    module = load(bake(cookies).project_path)
    assert module.combined([0, 0]) == 0
    assert module.combined([0, 3, 1]) == 3
    assert module.combined([]) == 0


def test_an_empty_workspace_has_nothing_to_check(cookies):
    root = bake(cookies).project_path
    result = subprocess.run([sys.executable, SCRIPT], cwd=root, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert "No package to check yet" in result.stdout


def _run(root, *args):
    env = {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}
    return subprocess.run(
        ["uv", "run", "--no-sync", "python", SCRIPT, *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )


@pytest.mark.slow
def test_integration_licensecheck_runs_in_every_member(cookies):
    root = bake(cookies).project_path
    _add_member(root, "Ledger", "library", dependency="attrs")
    _add_member(root, "Notes", "library", dependency="rich")
    sync = subprocess.run(
        ["uv", "sync", "--all-packages", "--no-default-groups", "--group", "license"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    assert sync.returncode == 0, sync.stderr

    result = _run(root)
    assert result.returncode == 0, result.stdout + result.stderr
    for expected in ("projects/ledger", "projects/notes", "attrs", "rich"):
        assert expected in result.stdout, expected

    # Arguments pass through, and a failing member fails the whole run.
    failing = _run(root, "--zero", "--fail-licenses", "MIT")
    assert failing.returncode != 0, failing.stdout


def test_script_passes_the_workspace_ruff_rules(cookies):
    """The script ships in every workspace, so it must pass that workspace's own ruff config."""
    root = bake(cookies).project_path
    for command in (["check", "--output-format", "concise"], ["format", "--check"]):
        result = subprocess.run(
            ["uvx", "ruff", *command, SCRIPT], cwd=root, capture_output=True, text=True, check=False
        )
        assert result.returncode == 0, result.stdout + result.stderr
