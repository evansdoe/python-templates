"""Tests for the py-workspace-template Cookiecutter template.

Uses pytest-cookies to bake the template with various parameter combinations
and verify the generated workspace root is structurally correct.

Test tiers:
  - test_bake_*: fast file-existence checks across the parameter matrix
  - test_*_toggle / test_*_content: feature-flag and rendering correctness
  - test_pre_gen_*: pre_gen_project.py validation hook
  - test_no_jinja_leaks / test_yaml_validity: hygiene checks on every render
  - test_integration_*: actually runs uv sync (slow, marked)
"""

import os
import subprocess

import pytest
import yaml

DEFAULTS = {
    "full_name": "Test Author",
    "email": "test@example.com",
    "vcs_username": "testuser",
    "workspace_name": "Test Workspace",
    "workspace_description": "A test workspace",
    "root_kind": "virtual",
    "license": "MIT",
    "copyright_year": "2026",
    "python_version": "3.14",
    "min_python_version": "3.14",
    "ci_platform": "github",
    "type_checker": "mypy",
    "include_docs": "yes",
    "include_precommit": "yes",
    "include_devcontainer": "yes",
    "include_danger": "no",
}

CI_PLATFORMS = ["github", "gitlab", "both"]
TYPE_CHECKERS = ["mypy", "ty", "none"]
ROOT_KINDS = ["virtual", "application"]


def bake(cookies, **overrides):
    """Bake the template with defaults + overrides and assert success."""
    ctx = {**DEFAULTS, **overrides}
    result = cookies.bake(extra_context=ctx)
    assert result.exit_code == 0, f"Bake failed: {result.exception}"
    assert result.exception is None
    assert result.project_path.is_dir()
    return result


def collect_yaml_files(project_path):
    yamls = []
    for root, _, files in os.walk(project_path):
        for f in files:
            if f.endswith((".yml", ".yaml")):
                yamls.append(os.path.join(root, f))
    return yamls


# ──────────────────────────────────────────────────────────────────────────
# Core bake matrix
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
@pytest.mark.parametrize("type_checker", TYPE_CHECKERS)
@pytest.mark.parametrize("root_kind", ROOT_KINDS)
def test_bake_core_matrix(cookies, ci_platform, type_checker, root_kind):
    result = bake(cookies, ci_platform=ci_platform, type_checker=type_checker, root_kind=root_kind)
    assert result.project_path.name == "test-workspace"


# ──────────────────────────────────────────────────────────────────────────
# root_kind: the one toggle most worth locking down — it decides whether
# this repo is itself a package or purely a container for members.
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("root_kind,expect_src", [("virtual", False), ("application", True)])
def test_root_kind_controls_src_and_tests(cookies, root_kind, expect_src):
    result = bake(cookies, root_kind=root_kind)
    assert (result.project_path / "src").exists() == expect_src
    assert (result.project_path / "tests").exists() == expect_src


def test_application_root_has_project_scripts(cookies):
    result = bake(cookies, root_kind="application")
    pyproject = (result.project_path / "pyproject.toml").read_text()
    assert "[project.scripts]" in pyproject
    assert "[tool.uv.sources]" in pyproject


def test_virtual_root_has_no_project_table(cookies):
    result = bake(cookies, root_kind="virtual")
    pyproject = (result.project_path / "pyproject.toml").read_text()
    assert "[project]" not in pyproject
    assert "[project.scripts]" not in pyproject


@pytest.mark.parametrize("root_kind", ROOT_KINDS)
def test_members_glob_always_present(cookies, root_kind):
    result = bake(cookies, root_kind=root_kind)
    assert 'members = ["projects/*"]' in (result.project_path / "pyproject.toml").read_text()


def test_projects_dir_placeholder(cookies):
    """projects/ ships with a .gitkeep so the empty dir survives git."""
    result = bake(cookies)
    assert (result.project_path / "projects" / ".gitkeep").exists()


# ──────────────────────────────────────────────────────────────────────────
# CI platform routing — single ci.yml, no per-module workflow at this layer
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "ci_platform,expect_github,expect_gitlab",
    [("github", True, False), ("gitlab", False, True), ("both", True, True)],
)
def test_ci_platform_file_routing(cookies, ci_platform, expect_github, expect_gitlab):
    result = bake(cookies, ci_platform=ci_platform)
    assert (result.project_path / ".github" / "workflows" / "ci.yml").exists() == expect_github
    assert (result.project_path / ".gitlab-ci.yml").exists() == expect_gitlab
    assert (result.project_path / ".gitlab").exists() == expect_gitlab


def test_discover_script_always_present(cookies):
    result = bake(cookies)
    assert (result.project_path / "scripts" / "ci" / "discover_projects.py").exists()


# ──────────────────────────────────────────────────────────────────────────
# Type checker routing (note the projects/*/tests exclude, unique to this template)
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("type_checker", TYPE_CHECKERS)
def test_type_checker_pyproject(cookies, type_checker):
    result = bake(cookies, type_checker=type_checker)
    pyproject = (result.project_path / "pyproject.toml").read_text()

    if type_checker == "mypy":
        assert "[tool.mypy]" in pyproject
        assert "exclude = ['^projects/[^/]+/tests/']" in pyproject
    elif type_checker == "ty":
        assert "[tool.ty.src]" in pyproject
        assert 'exclude = ["projects/*/tests"]' in pyproject
    else:
        assert "[tool.mypy]" not in pyproject
        assert "[tool.ty.src]" not in pyproject


# ──────────────────────────────────────────────────────────────────────────
# Feature toggles
# ──────────────────────────────────────────────────────────────────────────
def test_danger_toggle(cookies):
    off = bake(cookies, include_danger="no")
    assert not (off.project_path / "scripts" / "danger").exists()

    on = bake(cookies, include_danger="yes")
    assert (on.project_path / "scripts" / "danger" / "dangerfile.ts").exists()


def test_precommit_toggle(cookies):
    result = bake(cookies, include_precommit="no")
    assert not (result.project_path / ".pre-commit-config.yaml").exists()


def test_devcontainer_toggle(cookies):
    result = bake(cookies, include_devcontainer="no")
    assert not (result.project_path / ".devcontainer").exists()


def test_include_docs_only_affects_dependency_groups(cookies):
    """include_docs adds the docs dependency group, but this template ships no
    mkdocs.yml/docs/ of its own — unlike py-package-template and
    py-workspace-member. Documents current behavior; flag to maintainer if
    that asymmetry is unintentional."""
    on = bake(cookies, include_docs="yes")
    pyproject = (on.project_path / "pyproject.toml").read_text()
    assert "mkdocs-material" in pyproject
    assert not (on.project_path / "mkdocs.yml").exists()
    assert not (on.project_path / "docs").exists()

    off = bake(cookies, include_docs="no")
    assert "mkdocs-material" not in (off.project_path / "pyproject.toml").read_text()


# ──────────────────────────────────────────────────────────────────────────
# License generation
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "license_choice,expected_text",
    [
        ("MIT", "MIT License"),
        ("Apache-2.0", "Apache License"),
        ("BSD-3-Clause", "BSD 3-Clause License"),
        ("GPL-3.0-or-later", "GNU General Public License"),
        ("Proprietary", "proprietary and confidential"),
    ],
)
def test_license_content(cookies, license_choice, expected_text):
    result = bake(cookies, license=license_choice)
    assert expected_text in (result.project_path / "LICENSE").read_text()


# ──────────────────────────────────────────────────────────────────────────
# pre_gen_project.py validation
# ──────────────────────────────────────────────────────────────────────────
def test_pre_gen_rejects_min_version_newer_than_target(cookies):
    result = cookies.bake(
        extra_context={**DEFAULTS, "min_python_version": "3.15", "python_version": "3.13"}
    )
    assert result.exit_code != 0


def test_pre_gen_rejects_malformed_python_version(cookies):
    result = cookies.bake(extra_context={**DEFAULTS, "python_version": "3"})
    assert result.exit_code != 0


# ──────────────────────────────────────────────────────────────────────────
# Shared files always present
# ──────────────────────────────────────────────────────────────────────────
def test_core_files_always_present(cookies):
    result = bake(cookies)
    for path in [
        "pyproject.toml",
        "README.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "LICENSE",
        ".gitignore",
        ".editorconfig",
        ".python-version",
        "ruff.toml",
        "scripts/ci/discover_projects.py",
        ".vscode/extensions.json",
        ".vscode/settings.json",
    ]:
        assert (result.project_path / path).exists(), f"{path} should always exist"


# ──────────────────────────────────────────────────────────────────────────
# Hygiene: no Jinja leaks, valid YAML
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
@pytest.mark.parametrize("root_kind", ROOT_KINDS)
def test_no_jinja_leaks(cookies, ci_platform, root_kind):
    result = bake(cookies, ci_platform=ci_platform, root_kind=root_kind)
    for root, _, files in os.walk(result.project_path):
        for f in files:
            path = os.path.join(root, f)
            try:
                content = open(path, encoding="utf-8").read()
            except UnicodeDecodeError:
                continue
            assert "{%" not in content, f"Jinja block tag leak in {path}"
            assert "{{ cookiecutter" not in content, f"Unrendered variable in {path}"


@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
def test_yaml_validity(cookies, ci_platform):
    result = bake(cookies, ci_platform=ci_platform)
    yaml_files = collect_yaml_files(result.project_path)
    assert len(yaml_files) > 0

    for f in yaml_files:
        with open(f) as fp:
            try:
                yaml.safe_load(fp)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {f}: {e}")


# ──────────────────────────────────────────────────────────────────────────
# Integration tests — actually run uv sync (slow, needs network)
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.slow
@pytest.mark.parametrize("root_kind", ROOT_KINDS)
def test_integration_uv_sync(cookies, root_kind):
    """Generated workspace root can actually install dependencies with uv."""
    result = bake(cookies, root_kind=root_kind)
    proc = subprocess.run(
        ["uv", "sync", "--all-packages", "--all-groups"],
        cwd=result.project_path,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, f"uv sync failed:\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
