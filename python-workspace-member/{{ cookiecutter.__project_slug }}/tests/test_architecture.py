"""The package's import contract (``[tool.importlinter]`` in pyproject.toml) holds.

Running it as a test means every test run, locally and in CI, enforces the
architecture without a separate command.

A failure is a design question. Do not make it pass by renaming a module or
loosening the contract: decide where the code belongs, then declare it.
"""

from pathlib import Path

import pytest
from importlinter.cli import lint_imports

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_import_contracts_hold(capsys: pytest.CaptureFixture[str]) -> None:
    code = lint_imports(config_filename=str(PYPROJECT), no_cache=True, no_logo=True)
    report = capsys.readouterr().out
    assert code == 0, report
