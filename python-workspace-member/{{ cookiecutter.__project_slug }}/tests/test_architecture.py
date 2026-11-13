"""The package's import contract (``[tool.importlinter]`` in pyproject.toml) holds.

Running it as a test means every test run, locally and in CI, enforces the
architecture without a separate command.

A failure is a design question. Do not make it pass by renaming a module or
loosening the contract: decide where the code belongs, then declare it.
"""

from pathlib import Path

import pytest
from importlinter.cli import lint_imports

MEMBER_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = MEMBER_ROOT / "pyproject.toml"
PACKAGE_ROOT = MEMBER_ROOT / "src" / "{{ cookiecutter.__module_name }}"
UNIT_TESTS = MEMBER_ROOT / "tests" / "unit"


def test_import_contracts_hold(capsys: pytest.CaptureFixture[str]) -> None:
    code = lint_imports(config_filename=str(PYPROJECT), no_cache=True, no_logo=True)
    report = capsys.readouterr().out
    assert code == 0, report


def test_unit_test_folders_mirror_the_package() -> None:
    """Every folder under tests/unit/ is a sub-package of the same path in src/."""
    folders = [
        path
        for path in UNIT_TESTS.rglob("*")
        if path.is_dir() and not path.name.startswith(("_", "."))
    ]
    orphans = sorted(
        f"tests/unit/{folder.relative_to(UNIT_TESTS).as_posix()}"
        for folder in folders
        if not (PACKAGE_ROOT / folder.relative_to(UNIT_TESTS)).is_dir()
    )
    assert not orphans, f"no matching sub-package in src/ for: {orphans}"
