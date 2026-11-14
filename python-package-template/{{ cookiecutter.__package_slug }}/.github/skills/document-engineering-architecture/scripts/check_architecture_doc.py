"""Check an architecture document's structure against its skill.

Both audiences:
- title `# <Project> <audience> architecture`;
- provenance block with the skill's keys; `audience` and `project` match the
  file's path; `status` is `current` or `stale`; `source_revision` is 7 to 40
  lowercase hex characters; `generated_at` is `YYYY-MM-DDTHH:MM:SSZ`;
- the skill's required `##` sections in order, and no other `##` heading
  except `Human notes` (headings in code and human notes are ignored);
- at least three (engineering) or two (executive) Mermaid blocks, each
  followed by prose;
- exactly one pair of human-note markers;
- relative links resolve, use no line anchor (`#L42`) and stay in the
  repository (links in code and human notes are ignored);
- `inspected_paths` entries are repository-relative and exist;
- every relative link outside the project's own `docs/architecture/` lies
  under an `inspected_paths` entry;
- table columns with fixed values hold only the audience's values (see
  COLUMN_VALUES), and every row of the audience's evidence column (`Evidence`
  or `Source`, see EVIDENCE_COLUMN) has a relative link.

Executive documents also:
- every `[S<n>](...)` source marker has a row with the same target in the
  `Sources` table, and every row there is cited;
- the executive summary has at most 20 non-empty lines.

It does not check that content is accurate. The usage line must stay last.

usage: python check_architecture_doc.py docs/architecture/<engineering|executive>.md
"""

import os
import posixpath
import re
import sys
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[2]
PROVENANCE = re.compile(r"^<!-- ARCHITECTURE-DOC\n(.*?)^-->$", re.MULTILINE | re.DOTALL)
FIELD = re.compile(r"^([a-z_]+):[ \t]*(.*)$", re.MULTILINE)
FENCE = re.compile(r"^(`{3,}|~{3,}).*?^\1[ \t]*$", re.MULTILINE | re.DOTALL)
HUMAN_NOTES = re.compile(
    r"<!-- BEGIN HUMAN NOTES -->.*?<!-- END HUMAN NOTES -->", re.DOTALL
)
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
URL_SCHEME = re.compile(r"[a-z][a-z0-9+.-]*:")
LINE_ANCHOR = re.compile(r"L\d+(-L?\d+)?")
CELL_SPLIT = re.compile(r"(?<!\\)\|")
MARKER = re.compile(r"\[(S\d+)\]\(([^)\s]+)\)")
VALUE_RULES = (
    ("status", r"current|stale", "is not current or stale"),
    ("source_revision", r"[0-9a-f]{7,40}", "is not a commit"),
    ("generated_at", r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", "is not YYYY-MM-DDTHH:MM:SSZ"),
)
STATUS = ("current", "planned", "deprecated", "unknown")
COLUMN_VALUES = {
    "engineering": {"Status": STATUS, "Scope": ("internal", "external")},
    "executive": {
        "Status": STATUS,
        "Enforcement": ("code", "process", "planned", "none"),
        "State": ("open", "mitigated", "decision needed"),
        "Progress": ("done", "in progress", "planned"),
    },
}
EVIDENCE_COLUMN = {"engineering": "Evidence", "executive": "Source"}
MIN_DIAGRAMS = {"engineering": 3, "executive": 2}
SUMMARY_LIMIT = 20


class CheckError(Exception):
    """The document or its skill cannot be checked at all."""


def skill_part(skill: Path, heading: str) -> str:
    """Return the skill text after the heading line."""
    try:
        text = skill.read_text(encoding="utf-8")
    except OSError as error:
        raise CheckError(f"{skill}: cannot read ({error.strerror})") from error
    if heading not in text:
        raise CheckError(f"{skill}: no {heading!r} heading")
    return text.split(heading, 1)[1]


def required_sections(skill: Path) -> list[str]:
    """Return the required top-level section names listed in the skill, in order."""
    structure = skill_part(skill, "## Required document structure").split("\n## ", 1)[0]
    sections = re.findall(r"`## ([^`]+)`", structure)
    if not sections:
        raise CheckError(f"{skill}: no required sections listed")
    return sections


def provenance_keys(skill: Path) -> list[str]:
    """Return the top-level keys of the skill's provenance template, in order."""
    match = PROVENANCE.search(skill_part(skill, "## Provenance block"))
    if match is None:
        raise CheckError(f"{skill}: no provenance template")
    return [key for key, _ in FIELD.findall(match.group(1))]


def checked_text(text: str) -> str:
    """Return the document without code fences and human-note block."""
    return HUMAN_NOTES.sub("", FENCE.sub("", text))


def section_text(text: str, name: str) -> str | None:
    """Return the body of the `## name` section, or None when the section is absent."""
    match = re.search(
        rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL
    )
    return match.group(1) if match else None


def check(document: Path) -> list[str]:
    """Return one message per structural issue; empty when it conforms."""
    audience = document.stem
    if document.name not in ("engineering.md", "executive.md"):
        raise CheckError(f"{document}: not named engineering.md or executive.md")
    folder = document.resolve().parent
    if folder.parts[-2:] != ("docs", "architecture"):
        raise CheckError(f"{document}: not under docs/architecture/")
    root = folder.parents[1]
    project = "."
    skill = SKILLS / f"document-{audience}-architecture/SKILL.md"
    try:
        text = document.read_text(encoding="utf-8")
    except OSError as error:
        raise CheckError(f"{document}: cannot read ({error.strerror})") from error
    issues = []
    if not re.fullmatch(rf"# \S.* {audience} architecture", text.split("\n", 1)[0]):
        issues.append(f"title: first line is not # <Project> {audience} architecture")
    issues += provenance_issues(text, skill, {"audience": audience, "project": project})
    issues += section_issues(text, skill)
    issues += diagram_issues(text, MIN_DIAGRAMS[audience])
    begin, end = "<!-- BEGIN HUMAN NOTES -->", "<!-- END HUMAN NOTES -->"
    if (
        text.count(begin) != 1
        or text.count(end) != 1
        or text.index(begin) > text.index(end)
    ):
        issues.append("human notes: markers missing, repeated or reversed")
    issues += link_issues(text, document.parent)
    block = PROVENANCE.search(text)
    inspected = None
    if block:
        inspected = provenance_list(block.group(1), "inspected_paths")
        issues += inspected_paths_issues(inspected, root)
    issues += link_scope_issues(text, folder, root, inspected)
    issues += table_issues(text, audience)
    if audience == "executive":
        issues += marker_issues(text)
        issues += summary_issues(text)
    return issues


def provenance_list(block: str, key: str) -> list[str]:
    """Return the items of a list provenance key; empty when absent."""
    match = re.search(rf"^{key}:[ \t]*\n((?:[ \t]+- .*\n?)*)", block, re.MULTILINE)
    return (
        [line.split("- ", 1)[1].strip() for line in match.group(1).splitlines()]
        if match
        else []
    )


def inspected_paths_issues(entries: list[str], root: Path) -> list[str]:
    """Report inspected_paths entries that are absolute, outside, or missing."""
    issues = []
    for entry in entries:
        normalized = posixpath.normpath(entry)
        if (
            posixpath.isabs(normalized)
            or normalized == ".."
            or normalized.startswith("../")
        ):
            issues.append(
                f"provenance: inspected_paths entry is not repository-relative: {entry}"
            )
        elif not (root / normalized).exists():
            issues.append(f"provenance: inspected_paths entry does not exist: {entry}")
    return issues


def link_scope_issues(
    text: str, folder: Path, root: Path, inspected: list[str] | None
) -> list[str]:
    """Report line anchors, outside links, and links no inspected_paths entry covers.

    Coverage is skipped when there is no provenance block (inspected is None).
    """
    prose = re.sub(r"`[^`\n]*`", "", checked_text(text))
    entries = [posixpath.normpath(entry.rstrip("/")) for entry in inspected or []]
    own_docs = "docs/architecture/"
    issues = []
    for target in dict.fromkeys(LINK.findall(prose)):
        path, _, fragment = target.partition("#")
        if not path or URL_SCHEME.match(path):
            continue
        if LINE_ANCHOR.fullmatch(fragment):
            issues.append(f"links: line anchor: {target}")
        relative = Path(os.path.relpath(folder / path, root)).as_posix()
        if relative == ".." or relative.startswith("../"):
            issues.append(f"links: outside the repository: {target}")
        elif (
            inspected is not None
            and not relative.startswith(own_docs)
            and not any(
                relative == entry or relative.startswith(entry + "/")
                for entry in entries
            )
        ):
            issues.append(
                f"provenance: linked path not under inspected_paths: {relative}"
            )
    return list(dict.fromkeys(issues))


def tables(text: str) -> list[tuple[int, list[str], list[list[str]]]]:
    """Return (number, header cells, body rows) for each Markdown table."""
    found, block = [], []
    for line in [*checked_text(text).splitlines(), ""]:
        if line.lstrip().startswith("|"):
            block.append(
                [cell.strip() for cell in CELL_SPLIT.split(line.strip().strip("|"))]
            )
            continue
        if len(block) >= 2 and all(
            re.fullmatch(r":?-{3,}:?", cell) for cell in block[1]
        ):
            found.append((len(found) + 1, block[0], block[2:]))
        block = []
    return found


def table_issues(text: str, audience: str) -> list[str]:
    """Report cells outside a column's fixed values and evidence without links."""
    values, evidence = COLUMN_VALUES[audience], EVIDENCE_COLUMN[audience]
    issues = []
    for number, header, rows in tables(text):
        for column, name in enumerate(header):
            for row in rows:
                cell = row[column] if column < len(row) else ""
                value = cell.strip("`* ")
                if name in values and value not in values[name]:
                    allowed = ", ".join(values[name])
                    issues.append(
                        f"tables: table {number} {name} {value!r} "
                        f"is not one of {allowed}"
                    )
                links = [
                    target
                    for target in LINK.findall(cell)
                    if not URL_SCHEME.match(target)
                ]
                if name == evidence and not any(
                    not target.startswith("#") for target in links
                ):
                    issues.append(
                        f"tables: table {number} row {row[0]!r} has no evidence link"
                    )
    return issues


def marker_issues(text: str) -> list[str]:
    """Report source markers without a Sources row, and unused Sources rows."""
    prose = checked_text(text)
    sources = section_text(prose, "Sources")
    listed: dict[str, str] = {}
    for _, header, rows in tables(sources or ""):
        if "Marker" in header and "Source" in header:
            marker, source = header.index("Marker"), header.index("Source")
            for row in rows:
                if len(row) > max(marker, source):
                    links = LINK.findall(row[source])
                    listed[row[marker].strip("`* ")] = links[0] if links else ""
    body = re.sub(r"`[^`\n]*`", "", prose.replace(sources, "") if sources else prose)
    cited = list(dict.fromkeys(MARKER.findall(body)))
    issues = []
    for marker, target in cited:
        if marker not in listed:
            issues.append(f"sources: {marker} has no row in Sources")
        elif listed[marker].split("#")[0] != target.split("#")[0]:
            issues.append(
                f"sources: {marker} links {target}, but Sources lists {listed[marker]}"
            )
    used = {marker for marker, _ in cited}
    issues.extend(
        f"sources: {marker} is never cited" for marker in listed if marker not in used
    )
    return issues


def summary_issues(text: str) -> list[str]:
    """Report an executive summary longer than SUMMARY_LIMIT non-empty lines."""
    summary = section_text(checked_text(text), "Executive summary") or ""
    count = sum(1 for line in summary.splitlines() if line.strip())
    return (
        [f"summary: {count} non-empty lines, at most {SUMMARY_LIMIT}"]
        if count > SUMMARY_LIMIT
        else []
    )


def link_issues(text: str, folder: Path) -> list[str]:
    """Report relative links that do not resolve."""
    prose = re.sub(r"`[^`\n]*`", "", checked_text(text))
    issues = []
    for target in LINK.findall(prose):
        path = target.split("#", 1)[0]
        if path and not URL_SCHEME.match(path) and not (folder / path).exists():
            issues.append(f"links: does not resolve: {target}")
    return issues


def provenance_issues(text: str, skill: Path, expected: dict[str, str]) -> list[str]:
    """Report missing or invalid provenance keys and values."""
    block = PROVENANCE.search(text)
    if block is None:
        return ["provenance: block missing"]
    fields = dict(FIELD.findall(block.group(1)))
    issues = []
    missing = [key for key in provenance_keys(skill) if key not in fields]
    if missing:
        issues.append(f"provenance: missing keys {', '.join(missing)}")
    for key, value in expected.items():
        if fields.get(key, value) != value:
            issues.append(f"provenance: {key} is {fields[key]}, expected {value}")
    for key, pattern, problem in VALUE_RULES:
        if key in fields and not re.fullmatch(pattern, fields[key]):
            issues.append(f"provenance: {key} {problem}")
    return issues


def section_issues(text: str, skill: Path) -> list[str]:
    """Report missing, misordered and unexpected top-level sections."""
    headings = re.findall(r"^## (.+)$", checked_text(text), re.MULTILINE)
    required = required_sections(skill)
    issues = [f"sections: missing {name}" for name in required if name not in headings]
    if [name for name in headings if name in required] != [
        name for name in required if name in headings
    ]:
        issues.append("sections: out of order")
    issues.extend(
        f"sections: unexpected heading {name}"
        for name in headings
        if name not in [*required, "Human notes"]
    )
    return issues


def diagram_issues(text: str, minimum: int) -> list[str]:
    """Report too few Mermaid blocks and blocks without a prose description."""
    diagrams = [
        fence
        for fence in FENCE.finditer(text)
        if re.match(r"(`{3,}|~{3,})[ \t]*mermaid\b", fence.group(0))
    ]
    issues = []
    if len(diagrams) < minimum:
        issues.append(
            f"diagrams: {len(diagrams)} Mermaid blocks, at least {minimum} required"
        )
    for number, diagram in enumerate(diagrams, 1):
        following = text[diagram.end() :]
        stop = re.search(r"^(#{1,6} |`{3,}|~{3,})", following, re.MULTILINE)
        region = following[: stop.start() if stop else len(following)]
        if not any(
            line.strip() and not line.lstrip().startswith("|")
            for line in region.splitlines()
        ):
            issues.append(f"diagrams: block {number} has no prose description")
    return issues


def main(argv: list[str]) -> int:
    """Run the checker on one document; return the exit status."""
    if len(argv) != 1:
        print((__doc__ or "").strip().splitlines()[-1], file=sys.stderr)
        return 2
    try:
        issues = check(Path(argv[0]))
    except CheckError as error:
        print(error, file=sys.stderr)
        return 2
    for issue in issues:
        print(f"FAIL {issue}")
    if issues:
        return 1
    print("no issues")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
