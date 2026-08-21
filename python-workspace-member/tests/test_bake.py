"""Tests for the python-workspace-member Cookiecutter template.

Uses pytest-cookies to bake the template with various parameter combinations
and verify the generated project is structurally correct.

This template's two distinguishing behaviors, absent from python-package-template
and python-workspace-template, get dedicated coverage:
  - it renders correctly even though it depends on a parent workspace it
    cannot see when baked standalone (pre_gen only warns, never fails);
  - it wires sibling dependencies through both `dependencies` and
    `[tool.uv.sources]` from a single comma-separated string.

Test tiers:
  - test_bake_*: fast file-existence checks across the parameter matrix
  - test_*_toggle / test_*_content: feature-flag and rendering correctness
  - test_pre_gen_*: pre_gen_project.py validation hook
  - test_no_jinja_leaks / test_yaml_validity: hygiene checks on every render
  - test_integration_*: actually runs uv sync inside a real workspace (slow, marked)
"""

import os
import subprocess
from pathlib import Path

import pytest
import yaml

TEMPLATE_ROOT = Path(__file__).parent.parent

DEFAULTS = {
    "full_name": "Test Author",
    "email": "test@example.com",
    "project_name": "Test Project",
    "project_description": "A test project",
    "version": "0.1.0",
    "python_version": "3.14",
    "min_python_version": "3.14",
    "project_kind": "library",
    "include_docs": "no",
    "custom_gitlab_pipeline": "no",
    "member_dependencies": "",
    "ruff_override": "no",
}

PROJECT_KINDS = ["library", "application", "research"]


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
@pytest.mark.parametrize("project_kind", PROJECT_KINDS)
@pytest.mark.parametrize("include_docs", ["yes", "no"])
def test_bake_core_matrix(cookies, project_kind, include_docs):
    result = bake(cookies, project_kind=project_kind, include_docs=include_docs)
    assert result.project_path.name == "test-project"


# ──────────────────────────────────────────────────────────────────────────
# project_kind
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "project_kind,expect_main",
    [("library", False), ("application", True), ("research", False)],
)
def test_project_kind_controls_main(cookies, project_kind, expect_main):
    result = bake(cookies, project_kind=project_kind)
    main = result.project_path / "src" / "test_project" / "__main__.py"
    assert main.exists() == expect_main


def test_application_has_project_scripts(cookies):
    result = bake(cookies, project_kind="application")
    assert "[project.scripts]" in (result.project_path / "pyproject.toml").read_text()


def test_research_marks_do_not_upload(cookies):
    result = bake(cookies, project_kind="research")
    pyproject = (result.project_path / "pyproject.toml").read_text()
    assert 'classifiers = ["Private :: Do Not Upload"]' in pyproject


def test_library_has_neither(cookies):
    result = bake(cookies, project_kind="library")
    pyproject = (result.project_path / "pyproject.toml").read_text()
    assert "[project.scripts]" not in pyproject
    assert "Do Not Upload" not in pyproject


# ──────────────────────────────────────────────────────────────────────────
# Feature toggles
# ──────────────────────────────────────────────────────────────────────────
def test_docs_toggle(cookies):
    off = bake(cookies, include_docs="no")
    assert not (off.project_path / "docs").exists()

    on = bake(cookies, include_docs="yes")
    assert (on.project_path / "docs" / "index.md").exists()


def test_custom_gitlab_pipeline_toggle(cookies):
    off = bake(cookies, custom_gitlab_pipeline="no")
    assert not (off.project_path / ".gitlab-ci.yml").exists()

    on = bake(cookies, custom_gitlab_pipeline="yes")
    assert (on.project_path / ".gitlab-ci.yml").exists()


def test_ruff_override_toggle(cookies):
    off = bake(cookies, ruff_override="no")
    assert not (off.project_path / "ruff.toml").exists()

    on = bake(cookies, ruff_override="yes")
    ruff_toml = (on.project_path / "ruff.toml").read_text()
    assert 'extend = "../../ruff.toml"' in ruff_toml


# ──────────────────────────────────────────────────────────────────────────
# member_dependencies: the dependencies + [tool.uv.sources] wiring
# ──────────────────────────────────────────────────────────────────────────
def test_no_dependencies_by_default(cookies):
    result = bake(cookies, member_dependencies="")
    pyproject = (result.project_path / "pyproject.toml").read_text()
    assert "dependencies = []" in pyproject
    assert "[tool.uv.sources]" not in pyproject


def test_member_dependencies_wiring(cookies):
    result = bake(cookies, member_dependencies="geo-core, io-utils")
    pyproject = (result.project_path / "pyproject.toml").read_text()
    assert '"geo-core"' in pyproject
    assert '"io-utils"' in pyproject
    assert "[tool.uv.sources]" in pyproject
    assert "geo-core = { workspace = true }" in pyproject
    assert "io-utils = { workspace = true }" in pyproject


def test_member_dependencies_trims_whitespace(cookies):
    result = bake(cookies, member_dependencies="  geo-core  ,   io-utils  ")
    pyproject = (result.project_path / "pyproject.toml").read_text()
    assert '"geo-core"' in pyproject
    assert '"io-utils"' in pyproject
    assert "  geo-core  " not in pyproject


# ──────────────────────────────────────────────────────────────────────────
# pre_gen_project.py: warns but never fails when no parent workspace exists,
# since pytest-cookies bakes into an isolated temp directory
# ──────────────────────────────────────────────────────────────────────────
def test_pre_gen_warns_but_does_not_fail_outside_workspace(cookies):
    result = bake(cookies)
    assert result.exit_code == 0


def test_pre_gen_rejects_invalid_project_name_slug(cookies):
    result = cookies.bake(extra_context={**DEFAULTS, "project_name": "!!!"})
    assert result.exit_code != 0


# ──────────────────────────────────────────────────────────────────────────
# Shared files always present
# ──────────────────────────────────────────────────────────────────────────
def test_core_files_always_present(cookies):
    result = bake(cookies)
    for path in [
        "pyproject.toml",
        "README.md",
        "src/test_project/__init__.py",
        "src/test_project/py.typed",
        "tests/test_smoke.py",
    ]:
        assert (result.project_path / path).exists(), f"{path} should always exist"


def test_no_ruff_section_in_pyproject(cookies):
    """A [tool.ruff] section here would silently replace the workspace root config.

    (The file's own comments mention "[tool.ruff]" as a warning, so this checks
    for an actual TOML table header rather than doing a plain substring search.)
    """
    result = bake(cookies)
    lines = (result.project_path / "pyproject.toml").read_text().splitlines()
    assert not any(line.strip() == "[tool.ruff]" for line in lines)


# ──────────────────────────────────────────────────────────────────────────
# Hygiene: no Jinja leaks, valid YAML
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("project_kind", PROJECT_KINDS)
def test_no_jinja_leaks(cookies, project_kind):
    result = bake(cookies, project_kind=project_kind, member_dependencies="geo-core")
    for root, _, files in os.walk(result.project_path):
        for f in files:
            path = os.path.join(root, f)
            try:
                content = open(path, encoding="utf-8").read()
            except UnicodeDecodeError:
                continue
            assert "{%" not in content, f"Jinja block tag leak in {path}"
            assert "{{ cookiecutter" not in content, f"Unrendered variable in {path}"


def test_yaml_validity(cookies):
    result = bake(cookies, custom_gitlab_pipeline="yes")
    yaml_files = collect_yaml_files(result.project_path)
    assert len(yaml_files) > 0

    for f in yaml_files:
        with open(f) as fp:
            try:
                yaml.safe_load(fp)
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML in {f}: {e}")


# ──────────────────────────────────────────────────────────────────────────
# Integration test — bake this member INTO a real python-workspace-template
# workspace and confirm the pair actually locks and syncs together.
#
# pytest-cookies' `cookies.bake()` always bakes to an isolated pytest tmpdir
# and has no `output_dir` option, so this drives `cookiecutter()` directly
# for both bakes to reproduce the real `--output-dir projects/` workflow.
# Skipped unless a sibling checkout of python-workspace-template is available,
# since that's what CI wires up (see python-templates' integration workflow).
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.slow
def test_integration_uv_sync_inside_workspace(tmp_path):
    workspace_template = os.environ.get("WORKSPACE_TEMPLATE_PATH")
    if not workspace_template:
        pytest.skip("WORKSPACE_TEMPLATE_PATH not set — need a checkout of python-workspace-template")

    from cookiecutter.main import cookiecutter

    workspace_dir = cookiecutter(
        workspace_template,
        no_input=True,
        output_dir=str(tmp_path),
        extra_context={"workspace_name": "Integration Workspace"},
    )

    member_dir = cookiecutter(
        str(TEMPLATE_ROOT),
        no_input=True,
        output_dir=os.path.join(workspace_dir, "projects"),
        extra_context={**DEFAULTS, "project_name": "Integration Member"},
    )
    assert os.path.isdir(member_dir)

    proc = subprocess.run(
        ["uv", "sync", "--all-packages", "--all-groups"],
        cwd=workspace_dir,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, f"uv sync failed:\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
