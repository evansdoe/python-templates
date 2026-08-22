"""Tests for the python-package-template Cookiecutter template.

Uses pytest-cookies to bake the template with various parameter combinations
and verify the generated project is structurally correct.

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
    "package_name": "Test Package",
    "package_description": "A test package",
    "version": "0.1.0",
    "license": "MIT",
    "copyright_year": "2026",
    "python_version": "3.14",
    "min_python_version": "3.14",
    "ci_platform": "github",
    "type_checker": "mypy",
    "include_docs": "yes",
    "include_precommit": "yes",
    "include_devcontainer": "yes",
    "include_docker": "no",
    "include_danger": "no",
    "publish_to_pypi": "no",
}

CI_PLATFORMS = ["github", "gitlab", "both"]
TYPE_CHECKERS = ["mypy", "ty", "none"]


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
def test_bake_core_matrix(cookies, ci_platform, type_checker):
    result = bake(cookies, ci_platform=ci_platform, type_checker=type_checker)
    assert result.project_path.name == "test-package"


# ──────────────────────────────────────────────────────────────────────────
# CI platform routing
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "ci_platform,expect_github,expect_gitlab",
    [("github", True, False), ("gitlab", False, True), ("both", True, True)],
)
def test_ci_platform_file_routing(cookies, ci_platform, expect_github, expect_gitlab):
    result = bake(cookies, ci_platform=ci_platform)
    assert (result.project_path / ".github").exists() == expect_github
    assert (result.project_path / ".gitlab-ci.yml").exists() == expect_gitlab
    assert (result.project_path / ".gitlab").exists() == expect_gitlab


def test_github_ci_files(cookies):
    result = bake(cookies, ci_platform="github")
    assert (result.project_path / ".github" / "workflows" / "ci.yml").exists()
    assert (result.project_path / ".github" / "workflows" / "release.yml").exists()


def test_uv_version_not_pinned_stale(cookies):
    """UV_VERSION was hardcoded to 0.5.29, which predates Python 3.14 and
    broke CI the moment python_version's default moved to 3.14 -- "latest"
    means this can't go stale the same way again."""
    result = bake(cookies, ci_platform="github", publish_to_pypi="yes")
    ci_yml = (result.project_path / ".github" / "workflows" / "ci.yml").read_text()
    assert 'UV_VERSION: "latest"' in ci_yml
    release_yml = (result.project_path / ".github" / "workflows" / "release.yml").read_text()
    assert 'version: "latest"' in release_yml


# ──────────────────────────────────────────────────────────────────────────
# Feature toggles
# ──────────────────────────────────────────────────────────────────────────
def test_docker_toggle(cookies):
    off = bake(cookies, include_docker="no")
    assert not (off.project_path / "Dockerfile").exists()
    assert not (off.project_path / ".dockerignore").exists()

    on = bake(cookies, include_docker="yes")
    assert (on.project_path / "Dockerfile").exists()
    assert (on.project_path / ".dockerignore").exists()


def test_devcontainer_toggle(cookies):
    result = bake(cookies, include_devcontainer="no")
    assert not (result.project_path / ".devcontainer").exists()


def test_docs_toggle(cookies):
    off = bake(cookies, include_docs="no")
    assert not (off.project_path / "docs").exists()
    assert not (off.project_path / "mkdocs.yml").exists()

    on = bake(cookies, include_docs="yes")
    assert (on.project_path / "mkdocs.yml").exists()
    assert (on.project_path / "docs" / "index.md").exists()


def test_precommit_toggle(cookies):
    result = bake(cookies, include_precommit="no")
    assert not (result.project_path / ".pre-commit-config.yaml").exists()


def test_danger_toggle(cookies):
    off = bake(cookies, include_danger="no")
    assert not (off.project_path / "scripts" / "danger").exists()

    on = bake(cookies, include_danger="yes")
    assert (on.project_path / "scripts" / "danger" / "dangerfile.ts").exists()
    assert (on.project_path / "scripts" / "danger" / "package.json").exists()


def test_danger_rules_extracted_to_shared_module(cookies):
    """Rule logic lives in danger-rules.ts; dangerfile.ts is just config."""
    result = bake(cookies, include_danger="yes")
    danger_dir = result.project_path / "scripts" / "danger"
    assert (danger_dir / "danger-rules.ts").exists()
    dangerfile = (danger_dir / "dangerfile.ts").read_text()
    assert "runDanger" in dangerfile
    assert "fail(" not in dangerfile
    assert "schedule(" not in dangerfile


def test_danger_rules_does_not_value_import_danger(cookies):
    """Danger's CLI only strips `import ... from "danger"` out of the literal
    entrypoint dangerfile.ts -- the same import in any other file (like this
    one) survives into a real `require("danger")` call, which throws at
    runtime ("looks like you're trying to import the danger module").
    Verified against the actual danger CLI (danger local). Only a type-only
    import is safe here, since it always erases at compile time."""
    result = bake(cookies, include_danger="yes")
    rules = (result.project_path / "scripts" / "danger" / "danger-rules.ts").read_text()
    assert "import type" in rules
    assert "DangerDSLType" in rules
    assert "import { danger" not in rules
    assert "import {danger" not in rules


def test_danger_ci_fails_on_errors(cookies):
    """--failOnErrors is invoked directly in CI (not a package.json script
    here) -- without it, fail() rules never actually fail the job."""
    result = bake(cookies, include_danger="yes", ci_platform="both")
    gitlab_danger_yml = (result.project_path / ".gitlab" / "ci" / "danger.yml").read_text()
    assert "--failOnErrors" in gitlab_danger_yml

    github_ci_yml = (result.project_path / ".github" / "workflows" / "ci.yml").read_text()
    assert "--failOnErrors" in github_ci_yml


def test_danger_scripts_use_biome(cookies):
    result = bake(cookies, include_danger="yes", ci_platform="both")
    danger_dir = result.project_path / "scripts" / "danger"
    assert (danger_dir / "biome.json").exists()
    package_json = (danger_dir / "package.json").read_text()
    assert "@biomejs/biome" in package_json
    assert '"lint": "biome lint"' in package_json

    gitlab_danger_yml = (result.project_path / ".gitlab" / "ci" / "danger.yml").read_text()
    assert "pnpm lint" in gitlab_danger_yml
    assert "pnpm format" in gitlab_danger_yml

    github_ci_yml = (result.project_path / ".github" / "workflows" / "ci.yml").read_text()
    assert "pnpm lint" in github_ci_yml
    assert "pnpm format" in github_ci_yml


def test_dockerfile_has_no_unused_dev_stage(cookies):
    """The dev stage was vestigial -- nothing referenced it (no devcontainer
    build target, no CI job)."""
    result = bake(cookies, include_docker="yes")
    dockerfile = (result.project_path / "Dockerfile").read_text()
    assert "AS dev" not in dockerfile


@pytest.mark.parametrize("uv_version", ["latest", "0.12.5"])
def test_dockerfile_uv_version_decoupled_from_python_version(cookies, uv_version):
    """A combined python-version+uv-version tag (e.g.
    ghcr.io/astral-sh/uv:0.12.5-python3.14-bookworm-slim) doesn't reliably
    exist -- Astral doesn't publish every combination. Copying the uv binary
    from a bare-tag stage (which always resolves) avoids that entirely."""
    result = bake(cookies, include_docker="yes", uv_version=uv_version)
    dockerfile = (result.project_path / "Dockerfile").read_text()
    # The FROM line itself uses Docker's own ${UV_VERSION} substitution (resolved
    # at `docker build` time), not cookiecutter's -- only the ARG default varies.
    assert f"ARG UV_VERSION={uv_version}" in dockerfile
    assert "FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv" in dockerfile
    assert "COPY --from=uv /uv /uvx /bin/" in dockerfile


def test_uv_version_defaults_to_latest(cookies):
    result = bake(cookies, include_docker="yes")
    dockerfile = (result.project_path / "Dockerfile").read_text()
    assert "ARG UV_VERSION=latest" in dockerfile


# ──────────────────────────────────────────────────────────────────────────
# publish_to_pypi: release.yml always exists, only its content changes
# ──────────────────────────────────────────────────────────────────────────
def test_publish_to_pypi_off(cookies):
    result = bake(cookies, publish_to_pypi="no", ci_platform="github")
    release = (result.project_path / ".github" / "workflows" / "release.yml").read_text()
    assert "pypi:" not in release
    assert "id-token: write" not in release


def test_publish_to_pypi_on(cookies):
    result = bake(cookies, publish_to_pypi="yes", ci_platform="github")
    release = (result.project_path / ".github" / "workflows" / "release.yml").read_text()
    assert "pypi:" in release
    assert "id-token: write" in release


# ──────────────────────────────────────────────────────────────────────────
# Type checker routing
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("type_checker", TYPE_CHECKERS)
def test_type_checker_pyproject(cookies, type_checker):
    result = bake(cookies, type_checker=type_checker)
    pyproject = (result.project_path / "pyproject.toml").read_text()

    if type_checker == "mypy":
        assert '"mypy>=' in pyproject
        assert "[tool.mypy]" in pyproject
        assert "[tool.ty.src]" not in pyproject
    elif type_checker == "ty":
        assert '"ty>=' in pyproject
        assert "[tool.ty.src]" in pyproject
        assert "[tool.mypy]" not in pyproject
    else:
        assert '"mypy>=' not in pyproject
        assert '"ty>=' not in pyproject
        assert "[tool.mypy]" not in pyproject
        assert "[tool.ty.src]" not in pyproject


def test_type_checker_poe_task(cookies):
    with_types = bake(cookies, type_checker="mypy")
    assert "types" in (with_types.project_path / "pyproject.toml").read_text()

    without_types = bake(cookies, type_checker="none")
    pyproject = (without_types.project_path / "pyproject.toml").read_text()
    assert 'types = "mypy"' not in pyproject
    assert 'types = "ty check"' not in pyproject


def test_py_typed_always_present(cookies):
    """Unlike the type_checker-gated old template, py.typed here is unconditional."""
    result = bake(cookies, type_checker="none")
    assert (result.project_path / "src" / "test_package" / "py.typed").exists()


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


def test_proprietary_license_not_declared_in_pyproject(cookies):
    result = bake(cookies, license="Proprietary")
    pyproject = (result.project_path / "pyproject.toml").read_text()
    assert 'license = "Proprietary"' not in pyproject
    assert "Private :: Do Not Upload" in pyproject


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


def test_pre_gen_accepts_valid_versions(cookies):
    result = cookies.bake(
        extra_context={**DEFAULTS, "min_python_version": "3.13", "python_version": "3.15"}
    )
    assert result.exit_code == 0


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
        "src/test_package/__init__.py",
        "tests/test_smoke.py",
    ]:
        assert (result.project_path / path).exists(), f"{path} should always exist"


def test_python_version_file(cookies):
    result = bake(cookies, python_version="3.15")
    content = (result.project_path / ".python-version").read_text().strip()
    assert content == "3.15"


# ──────────────────────────────────────────────────────────────────────────
# Hygiene: no Jinja leaks, valid YAML
# ──────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
def test_no_jinja_leaks(cookies, ci_platform):
    result = bake(cookies, ci_platform=ci_platform)
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
    assert len(yaml_files) > 0, "Should have at least one YAML file"

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
@pytest.mark.parametrize("type_checker", TYPE_CHECKERS)
def test_integration_uv_sync(cookies, type_checker):
    """Generated project can actually install dependencies with uv."""
    result = bake(cookies, type_checker=type_checker)
    proc = subprocess.run(
        ["uv", "sync", "--all-groups"],
        cwd=result.project_path,
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, f"uv sync failed:\nstdout: {proc.stdout}\nstderr: {proc.stderr}"


@pytest.mark.slow
def test_integration_danger_lint_and_format(cookies):
    """Actually run install/lint/format against the generated danger scripts
    (via npm -- pnpm isn't assumed to be on the dev machine, but the CI
    templates themselves still use pnpm). Caught for real: danger-rules.ts
    imported real values from "danger" (crashes danger CI -- see
    test_danger_rules_does_not_value_import_danger) and, separately, wasn't
    run through biome format after editing (biome format exits non-zero on
    the mismatch, which would have failed CI's own format step)."""
    result = bake(cookies, include_danger="yes")
    danger_dir = result.project_path / "scripts" / "danger"
    install = subprocess.run(
        ["npm", "install", "--no-save"], cwd=danger_dir, capture_output=True, text=True, timeout=120
    )
    assert install.returncode == 0, f"npm install failed:\n{install.stdout}\n{install.stderr}"

    lint = subprocess.run(["npm", "run", "lint"], cwd=danger_dir, capture_output=True, text=True, timeout=60)
    assert lint.returncode == 0, f"lint failed:\n{lint.stdout}\n{lint.stderr}"

    fmt = subprocess.run(["npm", "run", "format"], cwd=danger_dir, capture_output=True, text=True, timeout=60)
    assert fmt.returncode == 0, f"format failed:\n{fmt.stdout}\n{fmt.stderr}"
