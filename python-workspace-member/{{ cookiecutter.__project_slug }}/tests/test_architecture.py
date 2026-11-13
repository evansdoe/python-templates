"""The package's import contract (``[tool.importlinter]`` in pyproject.toml) holds.

Running it as a test means every test run, locally and in CI, enforces the
architecture without a separate command.

A failure is a design question. Do not make it pass by renaming a module or
loosening the contract: decide where the code belongs, then declare it.
"""

import re
import tomllib
from pathlib import Path

import pytest
from importlinter.cli import lint_imports

MEMBER_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = MEMBER_ROOT / "pyproject.toml"
PACKAGE_ROOT = MEMBER_ROOT / "src" / "{{ cookiecutter.__module_name }}"
UNIT_TESTS = MEMBER_ROOT / "tests" / "unit"
PACKAGE_MAP = MEMBER_ROOT / "docs" / "design" / "package-map.md"


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


def _names_in_contract() -> set[str]:
    """Top-level names the import contract declares, entry point aside."""
    config = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    names: set[str] = set()
    for contract in config["tool"]["importlinter"]["contracts"]:
        if contract.get("type") != "layers":
            continue
        for line in contract.get("layers", []):
            names.update(part.strip(" ()") for part in re.split(r"[|:]", line))
        names.update(contract.get("exhaustive_ignores", []))
    return names - {"__main__", ""}


def _names_in_package_map() -> set[str]:
    """Names in the first column of the table under the map's "## Map" heading."""
    text = PACKAGE_MAP.read_text(encoding="utf-8")
    section = text.split("## Map", 1)[1].split("\n## ", 1)[0]
    return set(re.findall(r"^\|\s*`([^`]+)`\s*\|", section, flags=re.MULTILINE))


def test_package_map_and_contract_name_the_same_sub_packages() -> None:
    """The approved design (package map) and the enforced one (contract) agree."""
    in_contract = _names_in_contract()
    in_map = _names_in_package_map()
    unmapped = sorted(in_contract - in_map)
    unenforced = sorted(in_map - in_contract)
    assert not unmapped, f"in the contract but not in the package map: {unmapped}"
    assert not unenforced, f"in the package map but not in the contract: {unenforced}"
