"""Smoke tests for the workspace root package."""

import {{ cookiecutter.__root_module }}


def test_version_is_exposed() -> None:
    assert {{ cookiecutter.__root_module }}.__version__ == "0.1.0"
