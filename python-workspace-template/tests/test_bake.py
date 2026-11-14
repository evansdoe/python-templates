"""Tests for the python-workspace-template Cookiecutter template.

Uses pytest-cookies to bake the template with various parameter combinations
and verify the generated workspace root is structurally correct.

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
    "include_architecture_docs": "no",
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


def test_uv_version_not_pinned_stale(cookies):
    """UV_VERSION was hardcoded to 0.5.29, which predates Python 3.14 and
    broke CI the moment python_version's default moved to 3.14 -- "latest"
    (now the default for the uv_version cookiecutter option) means this
    can't go stale the same way again."""
    result = bake(cookies, ci_platform="github")
    ci_yml = (result.project_path / ".github" / "workflows" / "ci.yml").read_text()
    assert 'UV_VERSION: "latest"' in ci_yml


def test_uv_version_configurable(cookies):
    result = bake(cookies, ci_platform="github", uv_version="0.12.5")
    ci_yml = (result.project_path / ".github" / "workflows" / "ci.yml").read_text()
    assert 'UV_VERSION: "0.12.5"' in ci_yml


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
    assert "sourcePathMarker" in dangerfile  # this template overrides the package default
    assert "fail(" not in dangerfile
    assert "schedule(" not in dangerfile

    package_json = (danger_dir / "package.json").read_text()
    assert '"danger-rules": "github:evansdoe/danger-rules#v1.0.2"' in package_json


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


def test_types_job_installs_test_dependencies(cookies):
    """mypy checks tests/ as well as src/, so the type-check job needs the
    test group installed. Without it, the first CI run of any project whose
    tests import pytest fails with import-not-found. The generated smoke
    test imports only the package itself, which is why this went unseen."""
    result = bake(cookies, ci_platform="github", type_checker="mypy")
    ci = yaml.safe_load((result.project_path / ".github" / "workflows" / "ci.yml").read_text())
    syncs = [step["run"] for step in ci["jobs"]["types"]["steps"] if "run" in step]
    assert any("--group lint" in s and "--group test" in s for s in syncs), syncs


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


def test_precommit_toggle(cookies):
    result = bake(cookies, include_precommit="no")
    assert not (result.project_path / ".pre-commit-config.yaml").exists()


def test_devcontainer_toggle(cookies):
    result = bake(cookies, include_devcontainer="no")
    assert not (result.project_path / ".devcontainer").exists()


def test_docs_toggle(cookies):
    """include_docs ships a root mkdocs.yml + docs/index.md, matching
    python-package-template and python-workspace-member: mkdocstrings needs
    no per-member `paths:` because `uv sync --all-packages` installs every
    member editable into the one shared .venv, so their modules are already
    importable."""
    on = bake(cookies, include_docs="yes")
    pyproject = (on.project_path / "pyproject.toml").read_text()
    assert "mkdocs-material" in pyproject
    assert (on.project_path / "mkdocs.yml").exists()
    assert (on.project_path / "docs" / "index.md").exists()

    off = bake(cookies, include_docs="no")
    assert "mkdocs-material" not in (off.project_path / "pyproject.toml").read_text()
    assert not (off.project_path / "mkdocs.yml").exists()
    assert not (off.project_path / "docs").exists()


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
        "AGENTS.md",
        "CLAUDE.md",
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
# Agent files: a short root AGENTS.md with the gate commands and pointers,
# and a CLAUDE.md that imports it, whatever the CI platform
# ──────────────────────────────────────────────────────────────────────────
AGENTS_MD_MAX_LINES = 60


@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
def test_root_agent_files_are_baked(cookies, ci_platform):
    result = bake(cookies, ci_platform=ci_platform)
    agents = result.project_path / "AGENTS.md"
    assert agents.exists()
    assert len(agents.read_text().splitlines()) <= AGENTS_MD_MAX_LINES
    assert (result.project_path / "CLAUDE.md").read_text().strip() == "@AGENTS.md"


@pytest.mark.parametrize("type_checker", TYPE_CHECKERS)
def test_root_agents_md_names_only_poe_tasks_that_exist(cookies, type_checker):
    result = bake(cookies, type_checker=type_checker)
    pyproject = tomllib.loads((result.project_path / "pyproject.toml").read_text())
    defined = set(pyproject["tool"]["poe"]["tasks"])
    mentioned = set(re.findall(r"uv run poe ([\w:]+)", (result.project_path / "AGENTS.md").read_text()))
    assert {"check", "test"} <= mentioned
    assert mentioned <= defined, f"AGENTS.md names undefined poe tasks: {mentioned - defined}"


def test_root_agents_md_points_to_member_files(cookies):
    result = bake(cookies)
    text = (result.project_path / "AGENTS.md").read_text()
    for pointer in [
        "projects/<member>/AGENTS.md",
        "docs/PLAN.md",
        "docs/design/package-map.md",
        "--output-dir projects/",
    ]:
        assert pointer in text, f"AGENTS.md should mention {pointer}"


# ──────────────────────────────────────────────────────────────────────────
# Skills: python-design under .github/skills, linked from .claude/skills
# ──────────────────────────────────────────────────────────────────────────
SKILL_DIR = ".github/skills/python-design"
SKILL_FILES = [
    "SKILL.md",
    "references/boundaries.md",
    "references/code-shapes.md",
    "references/existing-packages.md",
    "references/quality-checks.md",
]


@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
def test_python_design_skill_is_baked(cookies, ci_platform):
    root = bake(cookies, ci_platform=ci_platform).project_path
    for name in SKILL_FILES:
        assert (root / SKILL_DIR / name).is_file(), f"missing {SKILL_DIR}/{name}"
    frontmatter = (root / SKILL_DIR / "SKILL.md").read_text().split("---")[1]
    assert "name: python-design" in frontmatter
    assert "description:" in frontmatter


def test_claude_skills_point_to_the_github_skill(cookies):
    """Claude Code reads .claude/skills; one copy of the text, linked."""
    root = bake(cookies).project_path
    link = root / ".claude/skills/python-design"
    assert link.is_symlink(), ".claude/skills/python-design should be a symlink"
    assert os.readlink(link) == "../../.github/skills/python-design"
    assert (link / "SKILL.md").read_text() == (root / SKILL_DIR / "SKILL.md").read_text()


def test_gitlab_workspace_keeps_skills_but_drops_workflows(cookies):
    root = bake(cookies, ci_platform="gitlab").project_path
    assert not (root / ".github/workflows").exists()
    assert (root / SKILL_DIR / "SKILL.md").is_file()


def test_root_agents_md_points_to_the_skill(cookies):
    text = (bake(cookies).project_path / "AGENTS.md").read_text()
    assert f"{SKILL_DIR}/SKILL.md" in text


def test_agent_markdown_code_blocks_pass_ruff_format(cookies):
    """Ruff formats Python blocks in Markdown; a fresh workspace must pass.

    uvx runs the newest ruff, which is what the workspace's `ruff>=0.9` resolves to.
    """
    root = bake(cookies).project_path
    proc = subprocess.run(
        ["uvx", "ruff", "format", "--check", ".github"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


# ──────────────────────────────────────────────────────────────────────────
# dev-workflow skill and tdd-refactor subagent (sanitised from a private repo)
# ──────────────────────────────────────────────────────────────────────────
WORKFLOW_DIR = ".github/skills/dev-workflow"
WORKFLOW_FILES = [
    "SKILL.md",
    "references/isolated-refactor.md",
    "references/pace.md",
    "references/review-comments.md",
]
AGENT_COPILOT = ".github/agents/tdd-refactor.agent.md"
AGENT_CLAUDE = ".claude/agents/tdd-refactor.md"

# SHA-256 prefixes of private names (employer, internal projects and groups)
# that must never reach this public template. Hashed so this file does not
# publish them.
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
    files += [root / WORKFLOW_DIR / name for name in WORKFLOW_FILES]
    return "\n".join(path.read_text() for path in files)


@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
def test_dev_workflow_skill_and_refactor_agent_are_baked(cookies, ci_platform):
    root = bake(cookies, ci_platform=ci_platform).project_path
    for name in WORKFLOW_FILES:
        assert (root / WORKFLOW_DIR / name).is_file(), f"missing {WORKFLOW_DIR}/{name}"
    assert split_frontmatter(root / WORKFLOW_DIR / "SKILL.md")[0]["name"] == "dev-workflow"
    assert (root / ".claude/skills/dev-workflow/SKILL.md").is_file()
    assert (root / AGENT_COPILOT).is_file()
    assert (root / AGENT_CLAUDE).is_file()


def test_refactor_agent_has_one_body_for_copilot_and_claude(cookies):
    root = bake(cookies).project_path
    copilot_front, copilot_body = split_frontmatter(root / AGENT_COPILOT)
    claude_front, claude_body = split_frontmatter(root / AGENT_CLAUDE)
    assert copilot_front["name"] == claude_front["name"] == "tdd-refactor"
    assert copilot_body == claude_body


@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
def test_baked_workspace_has_no_private_names(cookies, ci_platform):
    root = bake(cookies, ci_platform=ci_platform, include_danger="yes", include_architecture_docs="yes").project_path
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
    text = agent_files_text(bake(cookies).project_path)
    assert TICKET_ID.findall(text) == []


@pytest.mark.parametrize("type_checker", TYPE_CHECKERS)
def test_agent_files_name_only_poe_tasks_that_exist(cookies, type_checker):
    """Gates go through poe, so they follow the chosen type checker."""
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
    assert paths, "expected the agent files to name their companions"
    missing = sorted(p for p in paths if not (root / p).exists())
    assert not missing, f"named but not baked: {missing}"


def test_root_agents_md_points_to_the_workflow(cookies):
    """Tools that read only AGENTS.md (no skill discovery) still find it."""
    text = (bake(cookies).project_path / "AGENTS.md").read_text()
    assert f"{WORKFLOW_DIR}/SKILL.md" in text


# ──────────────────────────────────────────────────────────────────────────
# Size limits: ruff flags functions that do too much
# ──────────────────────────────────────────────────────────────────────────
SIZE_LIMITS = {"max-args": 5, "max-branches": 12, "max-statements": 50, "max-returns": 6}

TOO_MANY_ARGS = '''"""Doc."""


def build(a: int, b: int, c: int, d: int, e: int, f: int) -> int:
    """Doc."""
    return a + b + c + d + e + f
'''

TOO_COMPLEX = '"""Doc."""\n\n\ndef grade(x: int) -> str:\n    """Doc."""\n' + "".join(
    f"    if x == {i}:\n        return 'v{i}'\n" for i in range(11)
) + "    return 'none'\n"

MANY_FIXTURES = """def test_many(a, b, c, d, e, f):
    assert a
"""


def ruff_findings(root, files):
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    proc = subprocess.run(
        ["uvx", "ruff", "check", "--output-format", "concise", "projects"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    return proc.stdout


@pytest.mark.parametrize("root_kind", ROOT_KINDS)
def test_ruff_sets_size_limits(cookies, root_kind):
    config = tomllib.loads((bake(cookies, root_kind=root_kind).project_path / "ruff.toml").read_text())
    selected = set(config["lint"]["select"])
    assert {"C90", "PLR0911", "PLR0912", "PLR0913", "PLR0915"} <= selected
    assert config["lint"]["mccabe"]["max-complexity"] == 10
    assert {k: config["lint"]["pylint"][k] for k in SIZE_LIMITS} == SIZE_LIMITS


def test_ruff_flags_functions_that_do_too_much(cookies):
    root = bake(cookies).project_path
    out = ruff_findings(
        root,
        {
            "projects/m/src/m/__init__.py": '"""Doc."""\n',
            "projects/m/src/m/args.py": TOO_MANY_ARGS,
            "projects/m/src/m/branches.py": TOO_COMPLEX,
        },
    )
    assert "args.py" in out and "PLR0913" in out, out
    assert "branches.py" in out and "C901" in out, out
    assert "PLR0911" in out, out


def test_ruff_size_limits_spare_test_fixtures(cookies):
    """A test may take many fixtures; that is not a design smell."""
    root = bake(cookies).project_path
    out = ruff_findings(root, {"projects/m/tests/test_many.py": MANY_FIXTURES})
    assert "PLR0913" not in out, out


@pytest.mark.parametrize("root_kind", ROOT_KINDS)
def test_ruff_sorts_a_members_package_as_first_party(cookies, root_kind):
    """A member's tests import its package; ruff must not call it third-party."""
    root = bake(cookies, root_kind=root_kind).project_path
    member = root / "projects" / "my-member"
    (member / "src" / "my_member").mkdir(parents=True)
    (member / "src" / "my_member" / "__init__.py").write_text("")
    (member / "tests").mkdir()
    (member / "tests" / "test_a.py").write_text("import yaml\n\nfrom my_member import a\n")
    proc = subprocess.run(
        ["uvx", "ruff", "check", "--select", "I", "projects"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


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
# Architecture-document skills: an opt-in bake option, off by default.
# Documents live per member, in projects/<name>/docs/architecture/.
# ──────────────────────────────────────────────────────────────────────────
ARCH_SKILLS = ["document-executive-architecture", "document-engineering-architecture"]
CHECKER = ".github/skills/document-engineering-architecture/scripts/check_architecture_doc.py"


def run_checker(root, document):
    return subprocess.run([sys.executable, "-I", CHECKER, str(document)], cwd=root, capture_output=True, text=True)


def test_architecture_docs_are_off_by_default(cookies):
    root = bake(cookies).project_path
    for skill in ARCH_SKILLS:
        assert not (root / ".github/skills" / skill).exists(), skill
        assert not (root / ".claude/skills" / skill).exists(), skill
    assert "document-engineering-architecture" not in (root / "AGENTS.md").read_text()


@pytest.mark.parametrize("ci_platform", CI_PLATFORMS)
def test_architecture_docs_on_bakes_skills_checker_and_links(cookies, ci_platform):
    root = bake(cookies, ci_platform=ci_platform, include_architecture_docs="yes").project_path
    assert (root / CHECKER).is_file()
    for skill in ARCH_SKILLS:
        assert split_frontmatter(root / ".github/skills" / skill / "SKILL.md")[0]["name"] == skill
        assert os.readlink(root / ".claude/skills" / skill) == f"../../.github/skills/{skill}"


def test_root_agents_md_tells_agents_to_document_the_changed_member(cookies):
    text = (bake(cookies, include_architecture_docs="yes").project_path / "AGENTS.md").read_text()
    assert ".github/skills/document-executive-architecture/SKILL.md" in text
    assert ".github/skills/document-engineering-architecture/SKILL.md" in text
    assert "projects/<member>/docs/architecture/" in text


def test_architecture_checker_accepts_a_members_document(cookies):
    root = bake(cookies, include_architecture_docs="yes").project_path
    doc = root / "projects/demo/docs/architecture/executive.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Demo executive architecture\n")
    proc = run_checker(root, doc)
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert "FAIL provenance: block missing" in proc.stdout


def test_architecture_checker_rejects_a_document_outside_docs_architecture(cookies):
    root = bake(cookies, include_architecture_docs="yes").project_path
    doc = root / "projects/demo/engineering.md"
    doc.parent.mkdir(parents=True)
    doc.write_text("# Demo\n")
    proc = run_checker(root, doc)
    assert proc.returncode == 2
    assert "not under docs/architecture/" in proc.stderr


def test_architecture_checker_passes_the_workspace_lint(cookies):
    root = bake(cookies, include_architecture_docs="yes").project_path
    proc = subprocess.run(
        ["uvx", "ruff", "check", "--output-format", "concise", CHECKER], cwd=root, capture_output=True, text=True
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_architecture_skills_have_no_ticket_ids(cookies):
    """The full scan above covers private names and paths; ticket IDs are checked here."""
    root = bake(cookies, include_architecture_docs="yes").project_path
    found = []
    for skill in ARCH_SKILLS:
        for path in (root / ".github/skills" / skill).rglob("*"):
            if path.is_file():
                found += [f"{path.relative_to(root)}: {m}" for m in TICKET_ID.findall(path.read_text())]
    assert not found, "\n".join(found)
