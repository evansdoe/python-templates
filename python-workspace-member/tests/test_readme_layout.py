"""Generated READMEs keep every heading on its own line, after a blank line.

Jinja's `{%-` and `-%}` strip whitespace on one side of a tag. Around an
optional section that easily glues the next heading onto the previous
sentence ("...command`.## How CI works"), which Markdown then shows as text.
"""

import re

import pytest
from test_bake import bake

GLUED_HEADING = re.compile(r"[^\s#]#{2,6} \S")
INLINE_CODE = re.compile(r"`[^`]*`")


def heading_problems(text):
    """Return every heading glued to text or missing its blank line."""
    problems = []
    lines = text.splitlines()
    in_code = False
    for number, line in enumerate(lines, start=1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if GLUED_HEADING.search(INLINE_CODE.sub("", line)):
            problems.append(f"line {number}: heading glued to text: {line[:70]}")
        if line.startswith("#") and number > 1 and lines[number - 2].strip():
            problems.append(f"line {number}: no blank line before {line!r}")
    return problems


def test_heading_problems_finds_both_faults():
    text = "# Title\n\nSome text.## Glued\n\nMore text.\n## Cramped\n\n### Fine\n\nQuote `## Heading` freely.\n\n```bash\n# a comment\n```\n"
    assert heading_problems(text) == [
        "line 3: heading glued to text: Some text.## Glued",
        "line 6: no blank line before '## Cramped'",
    ]


@pytest.mark.parametrize("project_kind", ["library", "application", "research"])
@pytest.mark.parametrize("member_dependencies", ["", "geo-core"])
def test_generated_readme_headings_stand_on_their_own(cookies, project_kind, member_dependencies):
    root = bake(cookies, project_kind=project_kind, member_dependencies=member_dependencies).project_path
    assert heading_problems((root / "README.md").read_text()) == []
