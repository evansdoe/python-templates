"""The description becomes the package docstring; it must pass the project's own lint.

Ruff runs with the generated projects' docstring settings (pydocstyle, Google
convention, line length 88), given on the command line so that every
template's test checks the same rules.
"""

import ast
import subprocess

import pytest
from test_bake import DEFAULTS, bake

LIMIT = 88
LONG = (
    "A long description of what this package does, written in one sentence that "
    "runs well past the line limit of the formatter"
)
URL = "https://example.org/" + "a-very-long-path-segment-" * 4 + "end"


def sentence(length):
    """Words, then a period: exactly `length` characters, so E501 cannot skip it as one word."""
    words = ("lorem ipsum dolor sit amet " * 10)[: length - 1].rstrip()
    return words + "x" * (length - 1 - len(words)) + "."


RUFF_CONFIG = ["--config", f"line-length={LIMIT}", "--config", 'lint.pydocstyle.convention="google"']


def ruff(*args, cwd):
    return subprocess.run(["uvx", "ruff", *args, *RUFF_CONFIG], cwd=cwd, capture_output=True, text=True, check=False)


def lint_problems(init):
    """Ruff's docstring and line-length findings for one file, plus format drift."""
    check = ruff("check", "--select", "D,E501", "--output-format", "concise", init.name, cwd=init.parent)
    fmt = ruff("format", "--check", init.name, cwd=init.parent)
    return [line for line in (check.stdout + fmt.stdout).splitlines() if init.name in line]


DESCRIPTION = "package_description"
NAME = DEFAULTS["package_name"]
EXTRA = {}


def _init(cookies, description):
    root = bake(cookies, **{DESCRIPTION: description}, **EXTRA).project_path
    return next(root.glob("src/*/__init__.py"))


@pytest.mark.parametrize(
    "description",
    [
        None,
        "A tool without a final period",
        "Ends with a question?",
        sentence(82),
        sentence(83),
        LONG,
        f"{LONG}; the details live at {URL}",
    ],
    ids=["test-suite-default-has-no-period", "no-period", "question", "82-chars", "83-chars", "long", "long-with-url"],
)
def test_package_docstring_passes_lint(cookies, description):
    if description is None:
        init = next(bake(cookies, **EXTRA).project_path.glob("src/*/__init__.py"))
    else:
        init = _init(cookies, description)
    assert lint_problems(init) == []


def test_sentence_helper_builds_exact_lengths():
    assert [len(sentence(n)) for n in (82, 83)] == [82, 83]
    assert " " in sentence(83)


def test_short_description_stays_a_one_line_docstring_with_a_period(cookies):
    text = _init(cookies, "A tool without a final period").read_text()
    assert text.splitlines()[0] == '"""A tool without a final period."""'


def test_long_description_moves_below_a_summary_line(cookies):
    init = _init(cookies, LONG)
    lines = init.read_text().splitlines()
    assert lines[0] == f'"""{NAME}.'
    assert lines[1] == ""
    assert max(len(line) for line in lines) <= LIMIT
    assert ast.get_docstring(ast.parse(init.read_text())).split("\n\n", 1)[1].split() == f"{LONG}.".split()


def test_a_long_url_is_never_broken(cookies):
    init = _init(cookies, f"{LONG}; the details live at {URL}")
    assert URL in init.read_text().split()[-2] or any(line.strip().startswith(URL) for line in init.read_text().splitlines())
