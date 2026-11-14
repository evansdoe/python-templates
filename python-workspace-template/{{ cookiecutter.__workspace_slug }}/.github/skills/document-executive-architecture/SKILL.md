---
name: document-executive-architecture
description: >
  Generate and synchronize an evidence-backed executive architecture document
  for one package: a standalone package or a workspace member. Use after an architecture-affecting change, before a merge request is ready, or when
  product managers, project managers or directors need the project's
  capabilities, status, risks, dependencies, roadmap and decisions with
  Mermaid visuals.
---

# Document executive architecture

Create or synchronize `<package>/docs/architecture/executive.md` for one
package. `<package>` is `.` for a standalone package and `projects/<name>` for a
member of a uv workspace. Paths below are relative to the repository root. Its architecture-affecting changes must keep this document in sync. It is the executive view of the same package that `document-engineering-architecture` describes for engineers.

The primary readers are product managers, project managers and directors: they
use the document to learn what the project enables, where it stands, what
changed, what could go wrong, and what they must decide. The executive summary
also serves C-level readers, who may read nothing else. Use minimal
implementation terminology. Do not hide material operational, privacy,
security, cost, or delivery risk behind simplified language.

This skill changes and validates documentation only. It never commits, pushes,
or opens an MR, and it never creates or edits the project status file.



## Required input

Identify:

1. the package (`<package>`);
2. whether this is an initial generation (no document yet) or a
   synchronization;
3. for synchronization, a revision to compare from, only when the user gives
   one; otherwise step 1 of Change-aware synchronization finds it;
4. the completed implementation scope being documented.

## Investigation

When both architecture skills run for one change, run
`document-engineering-architecture` first.

If `<package>/docs/architecture/engineering.md` exists with `status: current`
and the `source_revision` you are documenting, use it as your map: read its
provenance block, then only the sections and table rows you need (search it,
don't read it whole). It is a peer document, not evidence. Verify each claim
you make against the repository sources it points to, and cite those sources.
Otherwise, for an initial generation or a full regeneration, read
`references/investigation.md` and build the map yourself.

Read economically; the cost of a run is mostly what you read:

- search before you read: find symbols, artifact paths and names, then read
  only the matching parts;
- never read a notebook, data file or lock file whole; search it, or extract
  what you need with a short script;
- read a reference file only at the step that names it.

The project tree defines the scope; a document may declare exclusions, and a
change inside an exclusion is reported, not documented.

## Project status file

Ownership, milestones, targets and cost rarely live in code. They come from
`<package>/docs/project-status.md`, which the project owner maintains from
`assets/project-status.template.md`. It is the only source for these facts:

- present each fact as stated, not verified: "Target date 2026-12-15, stated
  by <Updated by> on <Last updated> [S4]";
- never create or edit the file; when it is missing or a field is empty,
  list the missing input once under `### Missing management inputs` in
  `Decisions and gaps`, and write `Unknown` with a link to that list where
  the fact would go;
- add the file to `inspected_paths` when it exists.

## Fact and evidence rules

1. Inspect the implementation before writing. Only repository content is
   evidence of what the project does; knowledge from chat, memory, or outside
   the repository is not.
2. Cite every substantive claim with a source marker: a link whose text is
   `S<n>`, for example `[S6](../../src/pkg/admission.py)`. Every marker has
   a row with the same target in the `Sources` table, and every row there is
   used. Link files or headings, never lines (`#L42`).
3. Never present assumptions, issue descriptions, plans, or tests alone as
   proof of current behavior. Progress comes from git history: a step is
   `done` only when its work is merged into the main branch. Never cite text
   that this branch added to a plan, README or status file as evidence of a
   status.
4. When evidence conflicts, state the conflict under `### Evidence conflicts`
   in `Decisions and gaps`; do not silently choose the more convenient
   version. When the code settles it (for example a README that overstates
   capabilities), describe what the code does and name the stale source there.
5. Do not expose secrets, credentials, private environment values, raw or
   identifying session data, or other sensitive examples.
6. Each table uses its own fixed values, and no others:

   | Column | Used in | Values |
   |---|---|---|
   | `Status` | Capabilities and status; Dependencies | `current`, `planned`, `deprecated`, `unknown` |
   | `Enforcement` | Controls and risks | `code`, `process`, `planned`, `none` |
   | `State` | Controls and risks | `open`, `mitigated`, `decision needed` |
   | `Progress` | Roadmap and resourcing | `done`, `in progress`, `planned` |

   `current` means implemented at the documented revision and verified;
   `planned` means absent from the code and proposed in a cited repository
   plan or design (a folder or stub without the behavior is still planned;
   never label a control planned unless a cited source proposes it);
   `deprecated` means present and marked for removal by a cited source;
   `unknown` means neither code nor repository documents settle it.
   `process` means a rule people follow that no code enforces. Qualifiers
   ("optional", "tested") go in another column, not in these.
7. Prefer measurable facts. Measurements of the project's real data and
   outcomes are welcome when dated: "As of 2026-11-10, 340 of 380 committed
   reports were admitted". Give the revision you measured in your report.
   Leave out test counts, coverage results,
   run logs, checker output, and the result of comparing with the
   engineering document; those go in your report.
8. State each fact once, in the section that owns it, and link to it from
   elsewhere. Decisions live only in `Decisions and gaps`; risks only in
   `Controls and risks`.

## Change-aware synchronization

For an existing document, do these steps in order. Steps 0 to 2 cost almost
nothing; read no other file until step 2 says there is impact. Run every
command from the repository root.

0. **Check the structure.** Run the checker (see Validation). If it reports
   any issue, the document predates the current rules: say so first and run a
   full regeneration against the current revision, recording `regenerated` as
   the only impact category. Synchronization applies only to a document that
   passes the checker.
1. **Find the baseline.** The baseline is the commit the document describes.
   A revision the user gives replaces it. Otherwise use the document's
   `source_revision` when it is a commit and an ancestor of `HEAD`
   (`git merge-base --is-ancestor`). When it is not (for example the branch
   was squashed after the document was written), use the parent of the last
   commit that changed the document's `source_revision` line:
   `git log -1 --format=%H -G'^source_revision:' -- <package>/docs/architecture/executive.md`,
   then `<that commit>^`. Documentation is committed together with the code it
   describes, so that commit survives squashing; taking its parent reports
   too much rather than too little, and step 3 dismisses changes the document
   already describes. A typo fix to the document does not move either
   baseline. If there is still no baseline, say so first and run a full
   regeneration against the current revision, recording `regenerated` as the
   only impact category.
2. **Triage from the diff.** Run
   `git diff --stat <baseline> -- <package> ':(exclude)<package>/docs/architecture'`
   and `git ls-files --others --exclude-standard -- <package> ':(exclude)<package>/docs/architecture'`,
    The first compares against the working tree, so uncommitted
   changes count, including the project status file; the second lists new
   files git does not track yet. If both list nothing, the run is a no-op
   (step 4). Otherwise read the diff of the listed files, not the whole
   project, and classify it.
3. **Classify** the changes in these impact categories. A category applies
   only when the document does not already describe the change. Each one
   names the sections it may change:

   | Impact category | Sections |
   |---|---|
   | business capabilities and outcomes | Executive summary; Capabilities and status |
   | actors, systems, and project boundaries | How it works |
   | data and runtime flow | How it works |
   | controls, privacy, and security | Controls and risks |
   | operations, reliability, and observability | How it works; Controls and risks |
   | cost or resource profile | Roadmap and resourcing |
   | dependencies and cross-project connections | Dependencies |
   | risks, roadmap, and decisions | Controls and risks; Roadmap and resourcing; Decisions and gaps |

4. **No-op.** If none applies, do not touch the file, not even its
   provenance. Start your report with this exact line:
   `no executive architecture update required`; then give the baseline, the
   compared revision, the changed paths, and why no category applies.
5. **Edit in place.** If impact exists, read further only as far as the
   affected categories need. Edit only the sections their rows name, plus
   `What changed`, and `Executive summary` when a fact it states changed.
   Also update `Sources` when the edited sections add, change or remove a
   citation: add a row for each new marker, fix a row whose target changed,
   and delete a row whose last citation was removed. Leave every other row
   as it is, and give new markers the next unused number rather than
   renumbering. Add a `Glossary` entry for each new term the edits
   introduce. Every other section stays byte-identical. Never rewrite the
   whole file during synchronization.
6. Preserve the block from `<!-- BEGIN HUMAN NOTES -->` through
   `<!-- END HUMAN NOTES -->` byte-for-byte. A document has exactly one;
   missing, repeated or malformed markers are an error; do not guess what
   should be preserved.
7. Refresh provenance after validation: `source_revision` is `HEAD`,
   `base_revision` the baseline, `impact_categories` the categories that
   applied. If validation fails, follow the failure rule at the end of
   Validation.

Run synchronization after each completed architecture-affecting subtask and
again before MR readiness. Documentation changes belong on the implementation
branch and in that subtask's final squashed commit.

## Required document structure

Use this order, and read a section's part of `references/section-guide.md`
before you write or rebuild it:

1. `# <Project> executive architecture`
2. provenance block
3. `## Executive summary`
4. `## What changed`
5. `## Capabilities and status`
6. `## How it works`
7. `## Controls and risks`
8. `## Dependencies`
9. `## Roadmap and resourcing`
10. `## Decisions and gaps`
11. `## Glossary`
12. `## Sources`
13. human-note block

Do not fill sections with generic architecture advice. If a required topic is
not evidenced, say `Unknown` and identify the evidence needed.

## Provenance block

Place this directly below the title and keep it machine-readable:

```markdown
<!-- ARCHITECTURE-DOC
schema: 1
audience: executive
project: <package>
status: current|stale
source_revision: <commit>
base_revision: <baseline commit, or none>
generated_at: <UTC date and time>
owners: <owner from the project status file, or unknown>
inspected_paths:
  - <repository-relative path>
impact_categories:
  - <category, initial or regenerated>
-->
```

The document's architecture items may individually be current, planned,
deprecated, or unknown. The provenance `status` describes whether the document
matches the recorded source revision.

`source_revision` is the `HEAD` commit the run documented. For an initial
generation or a full regeneration without a baseline, set `base_revision` to
`none`. For an initial generation, record `initial` as the only impact
category. Write `generated_at` as `YYYY-MM-DDTHH:MM:SSZ`. `inspected_paths`
lists every repository path a fact rests on; every path the document links
must lie under an entry, except the peer document in `<package>/docs/architecture/`.
Whenever you change the document after writing its provenance, refresh
`generated_at` and `inspected_paths` in the same edit.

Set `status: current` only when every validation step you could run passed;
record steps you could not run as gaps in your report. The engineering and
executive skills use different impact categories on purpose, for their
different readers.

## Required visual illustrations

Use Mermaid embedded in Markdown and follow every diagram with a short,
accessible prose description. Both required diagrams go in `How it works`.

### 1. Context

Show the primary users and stakeholders, the project boundary, verified
upstream and downstream systems, the important data entering and leaving, and
trust or control boundaries when evidenced.

### 2. Value flow

Show the normal path from trigger or input to business outcome, plus material
review, validation, or rejection gates. Use a flowchart or sequence diagram,
whichever communicates the verified behavior most clearly.

### Optional: component view

Add a component view only when the project has more than one deployable or
runtime part. Express business responsibility, not class or function
inventories, and never show folders, tests or CI as components.

Diagram rules:

- use stable, readable node identifiers;
- keep labels short and define technical terms in the glossary;
- do not invent components to make a diagram look complete;
- use the classes `current`, `planned`, `deprecated`, `unknown` and
  `external` (for anything outside the project), with a legend listing only
  the classes the diagram uses;
- keep sensitive data out of labels and examples;
- ensure diagram arrows agree with the prose and evidence.

## Audience rules

- Lead with outcomes and decisions, not packages or algorithms.
- Explain technical controls in terms of risk reduced and residual risk.
- Separate current capability from roadmap.
- Prefer measurable facts. Do not claim scale, savings, reliability, safety,
  compliance, or production readiness without evidence.
- For each decision, say who decides, what it blocks, and what happens if
  nobody decides; write `Unknown` where no source says.
- Write for a reader who does not open the code. Leave out internal ticket
  and step IDs, hashes, command flags, library and tool versions, and file
  formats, unless the reader needs one to act; then explain it in plain words
  on first use.
- Keep the document short: for a single-package project, aim for at most
  about 200 lines outside diagrams. Link to the engineering document's
  sections for detail instead of restating them.

## Human notes

End the document with:

```markdown
## Human notes

<!-- BEGIN HUMAN NOTES -->
<!-- Add manually maintained context here. This block is preserved verbatim. -->
<!-- END HUMAN NOTES -->
```

Generated claims must not be placed inside this block. Human notes are not
automatically treated as verified evidence; management facts belong in the
project status file, not here.

## Validation

First run the structural checker (shared with the engineering skill) from the
repository root:

```bash
uv run python .github/skills/document-engineering-architecture/scripts/check_architecture_doc.py \
  <package>/docs/architecture/executive.md
```

Exit 0 prints `no issues`; exit 1 prints one `FAIL` line per structural
issue, each naming what to fix; exit 2 means the document could not be
checked (message on stderr). The checker's docstring lists what it checks. It
does not check that content is accurate.

A no-op synchronization (step 4) ends after step 4; the steps below apply
when you write or change the document.

Before finishing:

1. verify all repository links and source markers;
2. verify every substantive claim has evidence or an explicit status;
3. verify both required diagrams exist and agree with the prose;
4. validate Mermaid syntax when repository tooling is available; otherwise
   perform a structural check and report that rendered validation was not run;
5. verify documented commands, configuration names, and project connections
   against implementation, and each `done` step against git history;
6. compare with `<package>/docs/architecture/engineering.md` when it exists:
   every capability, component, control and dependency that appears in both
   must have the same status. Compare the two documents' status columns and
   diagram classes by searching them, not by reading both in full. Where they differ, check the code. If this
   document is wrong, fix it; if the engineering document is wrong, never
   edit it: report the difference so `document-engineering-architecture` can
   fix it. It is a peer document, not evidence: do not cite it as a source
   or list it in `inspected_paths`. If it does not exist, do not link to it;
   say so in your report;
7. verify the human-note block is unchanged;
8. report changed sections, impact categories, validation performed,
   measurements behind any dated figures, unknowns, and any decisions needed.

Fix every checker issue (exit 1); they are structural and always fixable. If
another validation step fails and you cannot fix its cause, write the document
with `status: stale` and list the failures in your report. Never report a
failing document as current.
