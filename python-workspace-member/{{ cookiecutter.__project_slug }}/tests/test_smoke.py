"""Smoke tests for {{ cookiecutter.__module_name }}."""

import {{ cookiecutter.__module_name }}


def test_version_is_exposed() -> None:
    assert {{ cookiecutter.__module_name }}.__version__ == "{{ cookiecutter.version }}"
