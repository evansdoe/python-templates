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

import json
import os
import subprocess
import sys
import tomllib
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
def test_bake_core_matrix(cookies, project_kind):
    result = bake(cookies, project_kind=project_kind)
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
@pytest.mark.parametrize("project_kind", PROJECT_KINDS)
def test_docs_are_always_baked(cookies, project_kind):
    result = bake(cookies, project_kind=project_kind)
    assert (result.project_path / "docs" / "index.md").exists()


def test_include_docs_is_not_a_bake_option():
    options = json.loads((TEMPLATE_ROOT / "cookiecutter.json").read_text())
    assert "include_docs" not in options
    assert "include_docs" not in (TEMPLATE_ROOT / "README.md").read_text()


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
# Architecture gate: an import contract plus a test that runs it, so a new
# member cannot grow a flat pile of top-level modules unnoticed
# ──────────────────────────────────────────────────────────────────────────
def run_member_tests(project_path, *pytest_args):
    """Run the baked member's own tests against its src/ folder."""
    env = {**os.environ, "PYTHONPATH": str(project_path / "src")}
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *pytest_args],
        cwd=project_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_architecture_test_file_is_baked(cookies):
    result = bake(cookies)
    assert (result.project_path / "tests" / "test_architecture.py").exists()


def test_import_linter_is_a_test_dependency(cookies):
    result = bake(cookies)
    pyproject = tomllib.loads((result.project_path / "pyproject.toml").read_text())
    test_group = pyproject["dependency-groups"]["test"]
    assert any(dep.startswith("import-linter") for dep in test_group), test_group


def test_layers_contract_is_exhaustive_for_the_package(cookies):
    result = bake(cookies)
    pyproject = tomllib.loads((result.project_path / "pyproject.toml").read_text())
    config = pyproject.get("tool", {}).get("importlinter", {})
    assert config.get("root_package") == "test_project"
    layers = [c for c in config.get("contracts", []) if c.get("type") == "layers"]
    assert len(layers) == 1, config
    assert layers[0].get("containers") == ["test_project"]
    assert layers[0].get("exhaustive") is True


@pytest.mark.parametrize("project_kind", PROJECT_KINDS)
def test_fresh_member_passes_its_architecture_test(cookies, project_kind):
    result = bake(cookies, project_kind=project_kind)
    proc = run_member_tests(result.project_path, "tests/test_architecture.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_undeclared_top_level_module_fails_the_architecture_test(cookies):
    result = bake(cookies)
    stray = result.project_path / "src" / "test_project" / "llm_cache.py"
    stray.write_text("VALUE = 1\n")
    proc = run_member_tests(result.project_path, "tests/test_architecture.py")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "test_project.llm_cache" in proc.stdout


# ──────────────────────────────────────────────────────────────────────────
# Test layout: unit tests live in tests/unit/ and mirror the package's
# sub-packages, so a move in src/ forces the matching move in tests/
# ──────────────────────────────────────────────────────────────────────────
def add_module(project_path, relative, content):
    """Write a file under the baked project, creating package folders."""
    target = project_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if "src" in target.parts:
        (target.parent / "__init__.py").touch()
    target.write_text(content)


def test_unit_folder_is_baked(cookies):
    result = bake(cookies)
    assert (result.project_path / "tests" / "unit").is_dir()


def test_pytest_uses_importlib_mode(cookies):
    result = bake(cookies)
    pyproject = tomllib.loads((result.project_path / "pyproject.toml").read_text())
    addopts = pyproject["tool"]["pytest"]["ini_options"]["addopts"]
    assert "--import-mode=importlib" in addopts


def test_same_named_test_files_in_two_unit_folders_collect(cookies):
    result = bake(cookies)
    for part in ("sources", "storage"):
        add_module(result.project_path, f"src/test_project/{part}/models.py", "VALUE = 1\n")
        add_module(
            result.project_path,
            f"tests/unit/{part}/test_models.py",
            f"from test_project.{part}.models import VALUE\n\n\n"
            "def test_value():\n    assert VALUE == 1\n",
        )
    proc = run_member_tests(result.project_path, "tests/unit")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "2 passed" in proc.stdout


def test_unit_folder_without_matching_package_fails_the_architecture_test(cookies):
    result = bake(cookies)
    add_module(
        result.project_path,
        "tests/unit/ghost/test_something.py",
        "def test_nothing():\n    assert True\n",
    )
    proc = run_member_tests(result.project_path, "tests/test_architecture.py")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "tests/unit/ghost" in proc.stdout


# ──────────────────────────────────────────────────────────────────────────
# Agent and planning files: where an agent (or a new teammate) learns how this
# member is built, what is planned, and which sub-packages exist and why
# ──────────────────────────────────────────────────────────────────────────
AGENTS_MD_MAX_LINES = 60


def headings(path):
    return [line.strip() for line in path.read_text().splitlines() if line.startswith("#")]


def test_agents_md_is_short_and_points_to_the_design_files(cookies):
    result = bake(cookies)
    agents = result.project_path / "AGENTS.md"
    assert agents.exists()
    text = agents.read_text()
    assert len(text.splitlines()) <= AGENTS_MD_MAX_LINES
    for pointer in [
        "docs/PLAN.md",
        "docs/design/package-map.md",
        "tests/test_architecture.py",
        "uv run --package test-project pytest",
    ]:
        assert pointer in text, f"AGENTS.md should mention {pointer}"


def test_claude_md_only_imports_agents_md(cookies):
    result = bake(cookies)
    assert (result.project_path / "CLAUDE.md").read_text().strip() == "@AGENTS.md"


def test_plan_has_concerns_decisions_and_open_sections(cookies):
    result = bake(cookies)
    plan = result.project_path / "docs" / "PLAN.md"
    assert plan.exists()
    assert headings(plan) == ["# Plan", "## Concerns", "## Decisions log", "## Open"]
    assert "| # | Branch | Delivers | Status |" in plan.read_text()


def test_package_map_has_one_row_per_sub_package_slot(cookies):
    result = bake(cookies)
    package_map = result.project_path / "docs" / "design" / "package-map.md"
    assert package_map.exists()
    text = package_map.read_text()
    assert "| Sub-package | Role | What belongs here | May import |" in text
    assert "test_project" in text
    assert "[tool.importlinter]" in text


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
