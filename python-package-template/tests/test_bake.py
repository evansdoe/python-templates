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

import hashlib
import os
import re
import subprocess
import sys
import tomllib

from pathlib import Path

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
    "include_architecture_docs": "no",
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
    assert (result.project_path / ".github" / "workflows").exists() == expect_github
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


def test_types_job_installs_test_dependencies(cookies):
    """mypy checks tests/ as well as src/, so the type-check job needs the
    test group installed. Without it, the first CI run of any project whose
    tests import pytest fails with import-not-found. The generated smoke
    test imports only the package itself, which is why this went unseen."""
    result = bake(cookies, ci_platform="github", type_checker="mypy")
    ci = yaml.safe_load((result.project_path / ".github" / "workflows" / "ci.yml").read_text())
    syncs = [step["run"] for step in ci["jobs"]["types"]["steps"] if "run" in step]
    assert any("--group lint" in s and "--group test" in s for s in syncs), syncs


@pytest.mark.parametrize(
    "min_version,target_version,expected",
    [("3.14", "3.14", ["3.14"]), ("3.13", "3.14", ["3.13", "3.14"])],
)
def test_each_python_version_appears_once(cookies, min_version, target_version, expected):
    """Equal min/target versions rendered ["3.14", "3.14"], which runs two
    identical test jobs whose coverage uploads collide on the artifact name,
    failing the second one. The classifiers duplicated the same way."""
    result = bake(cookies, min_python_version=min_version, python_version=target_version)
    ci = yaml.safe_load((result.project_path / ".github" / "workflows" / "ci.yml").read_text())
    assert ci["jobs"]["test"]["strategy"]["matrix"]["python-version"] == expected

    classifiers = [
        line
        for line in (result.project_path / "pyproject.toml").read_text().splitlines()
        if "Programming Language :: Python :: 3." in line
    ]
    assert len(classifiers) == len(expected), classifiers


def test_danger_job_declares_token_permissions(cookies):
    """A job that declares no permissions inherits the repository default,
    which carries no pull-requests scope when that default is read-only:
    every Danger API call then returns 403 "Resource not accessible by
    integration" and the job fails before it can review anything."""
    result = bake(cookies, include_danger="yes", ci_platform="github")
    ci = yaml.safe_load((result.project_path / ".github" / "workflows" / "ci.yml").read_text())
    assert ci["jobs"]["danger"]["permissions"] == {
        "contents": "read",
        "pull-requests": "write",
    }


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
    assert not (off.project_path / "docs" / "index.md").exists()
    assert not (off.project_path / "mkdocs.yml").exists()
    assert (off.project_path / "docs" / "PLAN.md").exists(), "the plan is not part of the site"

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


def test_danger_reruns_when_the_pull_request_is_edited(cookies):
    """Danger judges the title and the description, and both are edited after
    a pull request is opened. GitHub's default pull_request types are opened,
    synchronize and reopened, so without `edited` a corrected title left the
    failed check standing until someone pushed a commit. Projects without
    Danger do not want a full CI run every time a description is touched."""
    on = bake(cookies, include_danger="yes", ci_platform="github")
    ci = yaml.safe_load((on.project_path / ".github" / "workflows" / "ci.yml").read_text())
    # PyYAML reads an unquoted `on:` key as the boolean True (YAML 1.1).
    triggers = ci[True] if True in ci else ci["on"]
    assert triggers["pull_request"]["types"] == [
        "opened",
        "synchronize",
        "reopened",
        "edited",
    ]

    off = bake(cookies, include_danger="no", ci_platform="github")
    ci_off = yaml.safe_load(
        (off.project_path / ".github" / "workflows" / "ci.yml").read_text()
    )
    triggers_off = ci_off[True] if True in ci_off else ci_off["on"]
    assert triggers_off["pull_request"] is None


def test_danger_rules_come_from_shared_package(cookies):
    """Rule logic lives in the danger-rules npm package (github:evansdoe/
    danger-rules), not a copy-pasted local file -- dangerfile.ts is just
    config. This used to be a local danger-rules.ts, duplicated (and prone
    to drifting) across python-package-template and python-workspace-template;
    extracting it to a shared, versioned dependency means a fix lands in one
    place, pinned by tag, instead of two files kept in sync by hand."""
    result = bake(cookies, include_danger="yes")
    danger_dir = result.project_path / "scripts" / "danger"
    assert not (danger_dir / "danger-rules.ts").exists()

    dangerfile = (danger_dir / "dangerfile.ts").read_text()
    assert 'from "danger-rules"' in dangerfile
    assert "runDanger" in dangerfile
    assert "fail(" not in dangerfile
    assert "schedule(" not in dangerfile

    package_json = (danger_dir / "package.json").read_text()
    assert '"danger-rules": "github:evansdoe/danger-rules#v1.0.2"' in package_json


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


def test_dockerfile_dev_stage_matches_devcontainer(cookies):
    """The dev stage only exists when something actually builds it: the
    devcontainer's build.target. Previously the Dockerfile shipped a
    vestigial `dev` stage that nothing referenced (no devcontainer build
    target, no CI job) -- now it's gated on include_devcontainer, and the
    devcontainer builds from it instead of a generic third-party image, so
    the dev environment can't drift from what actually ships."""
    both = bake(cookies, include_docker="yes", include_devcontainer="yes")
    dockerfile = (both.project_path / "Dockerfile").read_text()
    assert "FROM python:${PYTHON_VERSION}-slim-bookworm AS dev" in dockerfile
    devcontainer = (both.project_path / ".devcontainer" / "devcontainer.json").read_text()
    assert '"target": "dev"' in devcontainer
    assert '"dockerfile": "../Dockerfile"' in devcontainer

    no_devcontainer = bake(cookies, include_docker="yes", include_devcontainer="no")
    assert "AS dev" not in (no_devcontainer.project_path / "Dockerfile").read_text()

    no_docker = bake(cookies, include_docker="no", include_devcontainer="yes")
    devcontainer_fallback = (no_docker.project_path / ".devcontainer" / "devcontainer.json").read_text()
    assert "mcr.microsoft.com/devcontainers/python" in devcontainer_fallback
    assert '"target": "dev"' not in devcontainer_fallback


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


def test_dockerignore_excludes_secrets_and_nested_node_modules(cookies):
    """`COPY . /app` would otherwise bake a .env, and its API keys, into the
    image. Unlike .gitignore, .dockerignore patterns are anchored to the
    context root, so scripts/danger/node_modules needs the ** prefix."""
    result = bake(cookies, include_docker="yes", include_danger="yes")
    patterns = (result.project_path / ".dockerignore").read_text().split()
    assert ".env" in patterns
    assert ".env.*" in patterns
    assert "**/node_modules/" in patterns


@pytest.mark.parametrize("include_devcontainer", ["yes", "no"])
def test_runtime_is_the_last_stage(cookies, include_devcontainer):
    """`docker build .` builds the last stage by default, so while dev came
    last a plain build produced the dev image: no application, no
    entrypoint, and every apt package the dev stage installs."""
    result = bake(
        cookies, include_docker="yes", include_devcontainer=include_devcontainer
    )
    dockerfile = (result.project_path / "Dockerfile").read_text()
    stages = re.findall(r"^FROM .* AS (\w+)$", dockerfile, re.MULTILINE)
    assert stages[-1] == "runtime", stages
    assert ("dev" in stages) == (include_devcontainer == "yes"), stages


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
# Architecture gate: an import contract plus a test that runs it, so a new
# package cannot grow a flat pile of top-level modules unnoticed
# ──────────────────────────────────────────────────────────────────────────
def run_package_tests(project_path, *pytest_args):
    """Run the baked package's own tests against its src/ folder."""
    env = {**os.environ, "PYTHONPATH": str(project_path / "src")}
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *pytest_args],
        cwd=project_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def add_module(project_path, relative, content):
    """Write a file under the baked project, creating package folders."""
    target = project_path / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if "src" in target.parts:
        (target.parent / "__init__.py").touch()
    target.write_text(content)


def test_architecture_test_file_is_baked(cookies):
    assert (bake(cookies).project_path / "tests" / "test_architecture.py").exists()


def test_import_linter_is_a_test_dependency(cookies):
    pyproject = tomllib.loads((bake(cookies).project_path / "pyproject.toml").read_text())
    test_group = pyproject["dependency-groups"]["test"]
    assert any(dep.startswith("import-linter") for dep in test_group), test_group


def test_layers_contract_is_exhaustive_for_the_package(cookies):
    pyproject = tomllib.loads((bake(cookies).project_path / "pyproject.toml").read_text())
    config = pyproject.get("tool", {}).get("importlinter", {})
    assert config.get("root_package") == "test_package"
    layers = [c for c in config.get("contracts", []) if c.get("type") == "layers"]
    assert len(layers) == 1, config
    assert layers[0].get("containers") == ["test_package"]
    assert layers[0].get("exhaustive") is True


def test_fresh_package_passes_its_architecture_test(cookies):
    proc = run_package_tests(bake(cookies).project_path, "tests/test_architecture.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_undeclared_top_level_module_fails_the_architecture_test(cookies):
    root = bake(cookies).project_path
    (root / "src" / "test_package" / "llm_cache.py").write_text("VALUE = 1\n")
    proc = run_package_tests(root, "tests/test_architecture.py")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "test_package.llm_cache" in proc.stdout


def test_unit_folder_is_baked(cookies):
    assert (bake(cookies).project_path / "tests" / "unit").is_dir()


def test_pytest_uses_importlib_mode(cookies):
    pyproject = tomllib.loads((bake(cookies).project_path / "pyproject.toml").read_text())
    assert "--import-mode=importlib" in pyproject["tool"]["pytest"]["ini_options"]["addopts"]


def test_same_named_test_files_in_two_unit_folders_collect(cookies):
    root = bake(cookies).project_path
    for part in ("sources", "storage"):
        add_module(root, f"src/test_package/{part}/models.py", "VALUE = 1\n")
        add_module(
            root,
            f"tests/unit/{part}/test_models.py",
            f"from test_package.{part}.models import VALUE\n\n\n"
            "def test_value():\n    assert VALUE == 1\n",
        )
    proc = run_package_tests(root, "tests/unit")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "2 passed" in proc.stdout


def test_unit_folder_without_matching_package_fails_the_architecture_test(cookies):
    root = bake(cookies).project_path
    add_module(root, "tests/unit/ghost/test_something.py", "def test_nothing():\n    assert True\n")
    proc = run_package_tests(root, "tests/test_architecture.py")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "tests/unit/ghost" in proc.stdout


# ──────────────────────────────────────────────────────────────────────────
# Agent and planning files. docs/PLAN.md and docs/design/ are baked whether or
# not the MkDocs site (include_docs) is, so the plan and the map always exist
# ──────────────────────────────────────────────────────────────────────────
AGENTS_MD_MAX_LINES = 60
DOCS_CHOICES = ["yes", "no"]


def headings(path):
    return [line.strip() for line in path.read_text().splitlines() if line.startswith("#")]


def test_agents_md_is_short_and_points_to_the_design_files(cookies):
    agents = bake(cookies).project_path / "AGENTS.md"
    assert agents.exists()
    text = agents.read_text()
    assert len(text.splitlines()) <= AGENTS_MD_MAX_LINES
    for pointer in ["docs/PLAN.md", "docs/design/package-map.md", "tests/test_architecture.py", "uv run pytest"]:
        assert pointer in text, f"AGENTS.md should mention {pointer}"


def test_agents_md_says_when_to_split_a_module(cookies):
    text = " ".join((bake(cookies).project_path / "AGENTS.md").read_text().split())
    assert "one module per role" in text.lower()
    assert "150 lines" in text
    assert "two reasons to change" in text


def test_claude_md_only_imports_agents_md(cookies):
    assert (bake(cookies).project_path / "CLAUDE.md").read_text().strip() == "@AGENTS.md"


@pytest.mark.parametrize("include_docs", DOCS_CHOICES)
def test_plan_has_concerns_decisions_and_open_sections(cookies, include_docs):
    plan = bake(cookies, include_docs=include_docs).project_path / "docs" / "PLAN.md"
    assert plan.exists()
    assert headings(plan) == ["# Plan", "## Concerns", "## Decisions log", "## Open"]
    assert "| # | Branch | Delivers | Status |" in plan.read_text()


@pytest.mark.parametrize("include_docs", DOCS_CHOICES)
def test_package_map_has_one_row_per_sub_package_slot(cookies, include_docs):
    package_map = bake(cookies, include_docs=include_docs).project_path / "docs" / "design" / "package-map.md"
    assert package_map.exists()
    text = package_map.read_text()
    assert "| Sub-package | Role | What belongs here | May import |" in text
    assert "test_package" in text
    assert "[tool.importlinter]" in text


def test_docs_site_files_still_follow_include_docs(cookies):
    root = bake(cookies, include_docs="no").project_path
    assert not (root / "mkdocs.yml").exists()
    assert not (root / "docs" / "index.md").exists()


def declare_sub_package(project_path, name, *, in_map, in_contract):
    """Create src/test_package/<name>/ and declare it in the map, the contract, or both."""
    add_module(project_path, f"src/test_package/{name}/models.py", "VALUE = 1\n")
    if in_contract:
        pyproject = project_path / "pyproject.toml"
        text = pyproject.read_text()
        assert 'layers = ["(__main__)"]' in text
        pyproject.write_text(text.replace('layers = ["(__main__)"]', f'layers = ["(__main__)", "{name}"]'))
    if in_map:
        package_map = project_path / "docs" / "design" / "package-map.md"
        text = package_map.read_text()
        assert "| _none yet_ | | | |" in text
        row = f"| `{name}` | subject logic | Data types of the subject | nothing |"
        package_map.write_text(text.replace("| _none yet_ | | | |", row))


@pytest.mark.parametrize("include_docs", DOCS_CHOICES)
def test_sub_package_in_map_and_contract_passes(cookies, include_docs):
    root = bake(cookies, include_docs=include_docs).project_path
    declare_sub_package(root, "domain", in_map=True, in_contract=True)
    proc = run_package_tests(root, "tests/test_architecture.py")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_sub_package_missing_from_map_fails(cookies):
    root = bake(cookies).project_path
    declare_sub_package(root, "domain", in_map=False, in_contract=True)
    proc = run_package_tests(root, "tests/test_architecture.py")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "in the contract but not in the package map: ['domain']" in proc.stdout


def test_sub_package_missing_from_contract_fails(cookies):
    root = bake(cookies).project_path
    declare_sub_package(root, "domain", in_map=True, in_contract=False)
    proc = run_package_tests(root, "tests/test_architecture.py")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "in the package map but not in the contract: ['domain']" in proc.stdout


# ──────────────────────────────────────────────────────────────────────────
# Skills and agents: python-design (shared with the workspace template),
# dev-workflow and the tdd-refactor subagent
# ──────────────────────────────────────────────────────────────────────────
WORKSPACE_TEMPLATE = Path(__file__).resolve().parents[2] / "python-workspace-template"
SKILLS = {
    "python-design": [
        "SKILL.md",
        "references/boundaries.md",
        "references/code-shapes.md",
        "references/existing-packages.md",
        "references/quality-checks.md",
    ],
    "dev-workflow": [
        "SKILL.md",
        "references/isolated-refactor.md",
        "references/pace.md",
        "references/review-comments.md",
    ],
}
AGENT_COPILOT = ".github/agents/tdd-refactor.agent.md"
AGENT_CLAUDE = ".claude/agents/tdd-refactor.md"
PRIVATE_NAME_HASHES = {
    "990bb270a89d9423", "54a3c6aaf3e5e627", "5990287170f076d9", "f01d6a140bd94f2b",
    "27d5a2e73131fdf9", "e48d6e93afa904e9", "d4d9592a499bbf85", "ee3caf2caa313b81",
    "4dcf4c826d72fa20", "a0b40b11e98e15f1", "b1968b190dd92b35",
}  # fmt: skip
TICKET_ID = re.compile(r"(?<![\w.])[A-Z]{2,10}-\d{2,6}(?![\w.])")
ABSOLUTE_HOME_PATH = re.compile(r"(?<![\w.])/(root|home/\w+|Users/\w+)/")


def split_frontmatter(path):
    _, front, body = path.read_text().split("---", 2)
    return yaml.safe_load(front), body


def agent_files_text(root):
    files = [root / AGENT_COPILOT, root / AGENT_CLAUDE]
    files += [root / ".github/skills/dev-workflow" / name for name in SKILLS["dev-workflow"]]
    return "\n".join(path.read_text() for path in files)


@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
def test_skills_are_baked_and_linked_for_claude(cookies, ci_platform):
    root = bake(cookies, ci_platform=ci_platform).project_path
    for skill, files in SKILLS.items():
        for name in files:
            assert (root / ".github/skills" / skill / name).is_file(), f"missing {skill}/{name}"
        assert split_frontmatter(root / ".github/skills" / skill / "SKILL.md")[0]["name"] == skill
        link = root / ".claude/skills" / skill
        assert link.is_symlink(), f".claude/skills/{skill} should be a symlink"
        assert os.readlink(link) == f"../../.github/skills/{skill}"


def test_gitlab_package_keeps_skills_but_drops_workflows(cookies):
    root = bake(cookies, ci_platform="gitlab").project_path
    assert not (root / ".github/workflows").exists()
    assert (root / ".github/skills/python-design/SKILL.md").is_file()


def test_skills_and_agents_are_the_same_as_in_the_workspace_template(cookies):
    """One text per skill and agent, two templates: a change must reach both."""
    root = bake(cookies).project_path
    workspace = WORKSPACE_TEMPLATE / "{{ cookiecutter.__workspace_slug }}"
    shared = [f".github/skills/{skill}/{name}" for skill, files in SKILLS.items() for name in files]
    for rel in [*shared, AGENT_COPILOT, AGENT_CLAUDE]:
        assert (root / rel).read_text() == (workspace / rel).read_text(), rel


def test_refactor_agent_has_one_body_for_copilot_and_claude(cookies):
    root = bake(cookies).project_path
    copilot_front, copilot_body = split_frontmatter(root / AGENT_COPILOT)
    claude_front, claude_body = split_frontmatter(root / AGENT_CLAUDE)
    assert copilot_front["name"] == claude_front["name"] == "tdd-refactor"
    assert copilot_body == claude_body


def test_agents_md_points_to_both_skills(cookies):
    text = (bake(cookies).project_path / "AGENTS.md").read_text()
    assert ".github/skills/python-design/SKILL.md" in text
    assert ".github/skills/dev-workflow/SKILL.md" in text


@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
def test_baked_package_has_no_private_names(cookies, ci_platform):
    root = bake(cookies, ci_platform=ci_platform, include_danger="yes").project_path
    found = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        for token in set(re.findall(r"[a-z0-9][a-z0-9_-]*", text.lower())):
            if hashlib.sha256(token.encode()).hexdigest()[:16] in PRIVATE_NAME_HASHES:
                found.append(f"{path.relative_to(root)}: private name")
        found += [f"{path.relative_to(root)}: path {m.group(0)}" for m in ABSOLUTE_HOME_PATH.finditer(text)]
    assert not found, "\n".join(found)


def test_agent_files_have_no_ticket_ids(cookies):
    assert TICKET_ID.findall(agent_files_text(bake(cookies).project_path)) == []


@pytest.mark.parametrize("type_checker", TYPE_CHECKERS)
def test_agent_files_name_only_poe_tasks_that_exist(cookies, type_checker):
    root = bake(cookies, type_checker=type_checker).project_path
    defined = set(tomllib.loads((root / "pyproject.toml").read_text())["tool"]["poe"]["tasks"])
    text = agent_files_text(root)
    mentioned = set(re.findall(r"uv run poe ([\w:]+)", text))
    assert {"check", "test"} <= mentioned
    assert mentioned <= defined, f"undefined poe tasks: {mentioned - defined}"
    assert not re.search(r"\b(ty check|mypy)\b", text), "call the type checker through poe"


def test_agent_files_point_only_to_files_that_exist(cookies):
    root = bake(cookies).project_path
    paths = set(re.findall(r"`(\.(?:github|claude)/[^`*<>\s]+)`", agent_files_text(root)))
    assert paths
    missing = sorted(p for p in paths if not (root / p).exists())
    assert not missing, f"named but not baked: {missing}"


def test_agent_markdown_code_blocks_pass_ruff_format(cookies):
    root = bake(cookies).project_path
    proc = subprocess.run(["uvx", "ruff", "format", "--check", ".github"], cwd=root, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ──────────────────────────────────────────────────────────────────────────
# Size limits: ruff flags functions that do too much
# ──────────────────────────────────────────────────────────────────────────
SIZE_LIMITS = {"max-args": 5, "max-branches": 12, "max-statements": 50, "max-returns": 6}
TOO_MANY_ARGS = (
    '"""Doc."""\n\n\ndef build(a: int, b: int, c: int, d: int, e: int, f: int) -> int:\n'
    '    """Doc."""\n    return a + b + c + d + e + f\n'
)
TOO_COMPLEX = (
    '"""Doc."""\n\n\ndef grade(x: int) -> str:\n    """Doc."""\n'
    + "".join(f"    if x == {i}:\n        return 'v{i}'\n" for i in range(11))
    + "    return 'none'\n"
)
MANY_FIXTURES = "def test_many(a, b, c, d, e, f):\n    assert a\n"


def ruff_findings(root, files):
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    proc = subprocess.run(
        ["uvx", "ruff", "check", "--output-format", "concise", *files], cwd=root, capture_output=True, text=True
    )
    return proc.stdout


def test_ruff_sets_size_limits(cookies):
    config = tomllib.loads((bake(cookies).project_path / "ruff.toml").read_text())
    assert {"C90", "PLR0911", "PLR0912", "PLR0913", "PLR0915"} <= set(config["lint"]["select"])
    assert config["lint"]["mccabe"]["max-complexity"] == 10
    assert {k: config["lint"]["pylint"][k] for k in SIZE_LIMITS} == SIZE_LIMITS


def test_ruff_flags_functions_that_do_too_much(cookies):
    root = bake(cookies).project_path
    out = ruff_findings(root, {"src/test_package/args.py": TOO_MANY_ARGS, "src/test_package/branches.py": TOO_COMPLEX})
    assert "args.py" in out and "PLR0913" in out, out
    assert "branches.py" in out and "C901" in out, out
    assert "PLR0911" in out, out


def test_ruff_size_limits_spare_test_fixtures(cookies):
    out = ruff_findings(bake(cookies).project_path, {"tests/test_many.py": MANY_FIXTURES})
    assert "PLR0913" not in out, out


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


# ──────────────────────────────────────────────────────────────────────────
# Architecture-document skills: an opt-in bake option, off by default
# ──────────────────────────────────────────────────────────────────────────
ARCH_SKILLS = ["document-executive-architecture", "document-engineering-architecture"]
CHECKER = ".github/skills/document-engineering-architecture/scripts/check_architecture_doc.py"


def test_architecture_docs_are_off_by_default(cookies):
    root = bake(cookies).project_path
    for skill in ARCH_SKILLS:
        assert not (root / ".github/skills" / skill).exists(), skill
        assert not (root / ".claude/skills" / skill).exists(), skill
    assert not (root / "docs/architecture").exists()
    assert "document-executive-architecture" not in (root / "AGENTS.md").read_text()


def test_architecture_docs_on_bakes_skills_checker_and_links(cookies):
    root = bake(cookies, include_architecture_docs="yes").project_path
    expected = {
        "document-executive-architecture": [
            "SKILL.md",
            "references/investigation.md",
            "references/section-guide.md",
            "assets/project-status.template.md",
        ],
        "document-engineering-architecture": [
            "SKILL.md",
            "references/section-guide.md",
            "scripts/check_architecture_doc.py",
        ],
    }
    for skill, files in expected.items():
        for name in files:
            assert (root / ".github/skills" / skill / name).is_file(), f"missing {skill}/{name}"
        assert split_frontmatter(root / ".github/skills" / skill / "SKILL.md")[0]["name"] == skill
        assert os.readlink(root / ".claude/skills" / skill) == f"../../.github/skills/{skill}"
    text = (root / "AGENTS.md").read_text()
    assert "document-engineering-architecture/SKILL.md" in text
    assert "docs/architecture/" in text


def test_architecture_checker_reports_usage_and_rejects_paths_outside_docs(cookies, tmp_path):
    root = bake(cookies, include_architecture_docs="yes").project_path
    usage = subprocess.run([sys.executable, CHECKER], cwd=root, capture_output=True, text=True)
    assert usage.returncode == 2
    outside = root / "engineering.md"
    outside.write_text("# not in docs\n")
    wrong_place = subprocess.run([sys.executable, CHECKER, str(outside)], cwd=root, capture_output=True, text=True)
    assert wrong_place.returncode == 2
    assert "not under docs/architecture/" in wrong_place.stderr


def test_architecture_checker_flags_a_document_missing_its_structure(cookies):
    root = bake(cookies, include_architecture_docs="yes").project_path
    doc = root / "docs/architecture/executive.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Sample executive architecture\n")
    proc = subprocess.run([sys.executable, CHECKER, str(doc)], cwd=root, capture_output=True, text=True)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "FAIL provenance: block missing" in proc.stdout
    assert "FAIL sections: missing Executive summary" in proc.stdout


@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
def test_architecture_docs_on_has_no_private_names_or_jinja(cookies, ci_platform):
    root = bake(cookies, ci_platform=ci_platform, include_architecture_docs="yes").project_path
    for skill in ARCH_SKILLS:
        for path in (root / ".github/skills" / skill).rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            assert "{%" not in text and "{{" not in text, path
            for token in set(re.findall(r"[a-z0-9][a-z0-9_-]*", text.lower())):
                digest = hashlib.sha256(token.encode()).hexdigest()[:16]
                assert digest not in PRIVATE_NAME_HASHES, f"{path.relative_to(root)} contains a private name"
            assert not ABSOLUTE_HOME_PATH.search(text), path
            assert not TICKET_ID.search(text), path


def test_architecture_checker_passes_the_packages_own_lint(cookies):
    """The checker ships in the package, so it must pass the package's own ruff gate."""
    root = bake(cookies, include_architecture_docs="yes").project_path
    proc = subprocess.run(
        ["uvx", "ruff", "check", "--output-format", "concise", CHECKER],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout


def test_architecture_pages_are_kept_out_of_the_docs_site(cookies):
    """Generated architecture pages are not MkDocs pages; strict builds would fail on them."""
    on = bake(cookies, include_architecture_docs="yes").project_path
    assert "exclude_docs" in (on / "mkdocs.yml").read_text()
    off = bake(cookies).project_path
    assert "exclude_docs" not in (off / "mkdocs.yml").read_text()
