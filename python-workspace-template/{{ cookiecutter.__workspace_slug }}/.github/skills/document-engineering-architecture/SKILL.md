---
name: document-engineering-architecture
description: >
  Generate and synchronize an evidence-backed engineering architecture
  document for one package: a standalone package or a workspace member. Use after an architecture-affecting change, before a merge request is ready, or when
  engineers need current components, interfaces, contracts, runtime flows,
  configuration, security, failure modes, testing, deployment, observability,
  and extension points with Mermaid visuals.
---

# Document engineering architecture

Create or synchronize `<package>/docs/architecture/engineering.md` for one
package. `<package>` is `.` for a standalone package and `projects/<name>` for a
member of a uv workspace. Paths below are relative to the repository root. Its architecture-affecting changes must keep this document in sync.

The document is for engineers who need to understand, operate, change, test,
or integrate the implementation. Describe architecture and important internal
modules without turning the document into a generated API or file listing.

This skill changes and validates documentation only. It never commits, pushes,
or opens an MR.

One reference file holds detail most runs don't need:

- `references/section-guide.md`: what each technical section must cover.
  Read a section's part before you write or rebuild that section.


## Required input

Identify:

1. the package (`<package>`);
2. whether this is an initial generation (no document yet) or a
   synchronization;
3. for synchronization, a revision to compare from, only when the user gives
   one; otherwise step 1 of Change-aware synchronization finds it;
4. the completed implementation scope being documented.

## Repository investigation

For an initial generation or a full regeneration, build an evidence map
before writing. During synchronization, investigate only what the affected
impact categories need, including the whole-repository search of item 11 for
the artifacts those categories touch. The evidence map covers:

1. entry points, public commands, workers, jobs, and runtime processes;
2. packages/modules and their dependency direction;
3. schemas, models, file formats, persistence, and boundary validation;
4. internal and external interfaces, including CLI, HTTP, model, storage, and
   cross-project contracts;
5. configuration sources, precedence, defaults, feature gates, and secrets;
6. runtime paths, retries, resumability, idempotency, concurrency, and state
   transitions;
7. privacy, security, authorization, trust boundaries, and sensitive data;
8. errors, quarantine/dead-letter behavior, recovery, and operator actions;
9. logs, metrics, traces, manifests, reports, and provenance;
10. test layers, fixtures, quality gates, deployment, packaging, and CI,
    including CI jobs whose path rules or globs match the package's files;
11. verified upstream/downstream connections to any other program or repository, supported or not. For every artifact the project reads or
    writes (file, folder, table, schema), search the whole repository for
    every other program that writes or reads its path or name: other programs' source, scripts, notebooks and CI files, not only the producer
    a README names. A second writer of an input is part of the input
    contract. Name each search (pattern and scope) in your report. Never read production or customer data for this;
12. extension points and constraints future changes must preserve.

The project tree defines the scope. A document may declare exclusions in
`Purpose and scope`; a change inside an exclusion is reported, not documented.

Prefer semantic code intelligence and symbols where available. Use tests to
confirm behavior, not as the sole proof that runtime code implements it.

## Fact and evidence rules

1. Back every substantive claim with repository evidence, cited in one form:
   a relative link to the file, followed by the backticked symbol when the
   claim is about one, for example
   [admission.py](../../src/pkg/admission.py) `admit`. Cite a test by its
   backticked name with a link to its file; a group label such as "outcome
   tests" is not evidence. Never use line anchors (`#L42`): they go stale on
   the next edit, and the checker rejects them.

   Only repository content is evidence of what the project does; knowledge
   from chat, memory, or outside the repository is not. Documented semantics
   of the language, its standard library and standard tools (for example the
   Python version a syntax needs, `argparse`'s exit code for usage errors, or
   what `git cat-file` returns) may be stated as background without a link.
   Never use background knowledge to infer project behavior the code does
   not show.
2. Distinguish current, planned, deprecated, and unknown architecture.
3. Never infer current behavior from a plan, issue, stale README, or test that
   has no matching implementation.
4. When sources conflict, describe the conflict and mark the affected area
   unknown or stale. When the code settles it (for example a README that
   overstates capabilities), document what the code does and list the stale
   source in `Known gaps and decisions needed`.
5. Use exact names for interfaces, fields, statuses, configuration, and
   artifacts. Do not copy sensitive values or private sample content.
6. Do not claim guarantees stronger than the code provides. Explicitly state
   process, platform, deployment, and data assumptions.
7. Give every architecture item exactly one status from this list; there are
   no other values:
   - **current**: implemented at the documented revision and verified in code;
   - **planned**: absent from the code and proposed in a repository plan or
     design document, which you cite. A folder or stub without the behavior is
     still planned;
   - **deprecated**: present in the code and marked for removal by a cited
     source;
   - **unknown**: neither the code nor the repository's documents settle it.
     When the code shows a feature is absent and a plan proposes it, it is
     planned, not unknown. A negative claim ("no writer exists") needs a
     search you can name, across the whole repository.

   Status says whether something exists, not who owns it or whether it is
   correct. Keep those apart:
   - **Scope** is a separate column with the values `internal` (inside the
     project tree) and `external` (another project, a tool, a service). Use
     it in tables that mix both.
   - **Contradictions** keep the status of what the code does. Current code
     that disagrees with its producer, consumer or a document stays
     `current`; put the disagreement in `Known gaps and decisions needed`
     and link to it from the row.

   Where the status goes:
   - **Tables.** Every table that lists components, interfaces, artifacts,
     configuration, failure modes or cross-project dependencies has a
     `Status` column holding one value, and an `Evidence` column where every
     row links at least one file. The column names `Status`, `Scope` and
     `Evidence` are reserved for these meanings: name a documented field
     differently (for example `Result status`). The checker validates the
     values of these columns wherever they appear; it does not check that a
     table has them. Qualifiers ("CI artifact only", "folder
     with `.gitkeep`") go in another column, not in `Status`.
   - **Prose and lists.** Prefix an item with its bold status only when it
     is not current; an unlabelled item in prose is current.
   - **Diagrams.** Use the Mermaid classes `current`, `planned`,
     `deprecated`, `unknown` and `external`. A node outside the project takes
     `external`, whatever its status.
8. Put validation results in your final report, not in the document. The
   document states verified facts, statuses and gaps. It does not contain run
   logs, checker output, or the result of comparing with the executive
   document. It also leaves out numbers that go stale: test counts, and
   counts of repository content that grows, such as the number of committed
   reports. State the fact without the number ("committed reports with
   `assessment: null` are rejected"); give the number in your report.

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
   `git log -1 --format=%H -G'^source_revision:' -- <package>/docs/architecture/engineering.md`,
   then `<that commit>^`. Documentation is committed together with the code it
   describes, so that commit survives squashing; taking its parent reports
   too much rather than too little, and step 3 dismisses changes the document
   already describes. A typo fix to the document does not move either
   baseline. If there is still no baseline, say so first and run a full regeneration against the current
   revision, recording `regenerated` as the only impact category.
2. **Triage from the diff.** Run
   `git diff --stat <baseline> -- <package> ':(exclude)<package>/docs/architecture'`
   and `git ls-files --others --exclude-standard -- <package> ':(exclude)<package>/docs/architecture'`,
    The first compares against the working
   tree, so uncommitted changes count; the second lists new files git does
   not track yet. If both list nothing, the run is a no-op (step 4). Otherwise read the diff of the listed files, not the whole
   project, and classify it.
3. **Classify** the changes in these impact categories. A category applies
   only when the document does not already describe the change. Each one
   names the sections it may change:

   | Impact category | Sections |
   |---|---|
   | system boundary and dependencies | Purpose and scope; Architecture boundaries and assumptions; Complete architecture; Cross-project dependencies |
   | components and module responsibilities | Component model |
   | interfaces and data contracts | Interfaces, contracts, and data model; Cross-project dependencies |
   | runtime/data flow and state | End-to-end runtime flows |
   | configuration and deployment | Configuration and precedence; Packaging, deployment, and environments |
   | security and privacy | Security and privacy |
   | failure handling and recovery | Failure modes, recovery, and idempotency |
   | observability and operations | Observability and operations |
   | testing and quality gates | Testing and quality gates |
   | extension points and constraints | Extension points and architectural constraints |

4. **No-op.** If no category applies, do not modify the document, not even
   its provenance; the file stays byte-identical. Start your report with
   this exact line: `no engineering architecture update required`; then give
   the baseline, the compared revision, the changed paths, and why no
   category applies.
5. **Edit in place.** If impact exists, read further only as far as the
   affected categories need. Edit only the sections their rows name, plus
   `Known gaps and decisions needed` and `Glossary` where the change affects
   them; every other section stays byte-identical. Never rewrite the whole
   file during synchronization. Then check what links to the changed
   material, such as diagrams and other sections, for contradictions. A
   section found contradicting the change becomes affected: edit it, and
   name it in your report.
6. Preserve the block from `<!-- BEGIN HUMAN NOTES -->` through
   `<!-- END HUMAN NOTES -->` byte-for-byte. A document has exactly one; treat
   missing, repeated or malformed markers as an error.
7. Refresh provenance after validation: `source_revision` is `HEAD`
   (commit the document together with the code it describes, so the next
   run's baseline already contains that code),
   `base_revision` the baseline, `impact_categories` the categories that
   applied, and `inspected_paths` gains any path the edit relies on. If
   validation fails, follow the failure rule at the end of Validation.

Run synchronization after each completed architecture-affecting subtask and
again before MR readiness. Documentation changes belong on the implementation
branch and in that subtask's final squashed commit.

## Required document structure

Use this order:

1. `# <Project> engineering architecture`
2. provenance block
3. `## Purpose and scope`
4. `## Architecture boundaries and assumptions`
5. `## Complete architecture`
6. `## Component model`
7. `## End-to-end runtime flows`
8. `## Interfaces, contracts, and data model`
9. `## Configuration and precedence`
10. `## Security and privacy`
11. `## Failure modes, recovery, and idempotency`
12. `## Observability and operations`
13. `## Packaging, deployment, and environments`
14. `## Testing and quality gates`
15. `## Extension points and architectural constraints`
16. `## Cross-project dependencies`
17. `## Known gaps and decisions needed`
18. `## Glossary`
19. human-note block

Use tables for contracts, configuration, components, failure modes, artifacts,
and test coverage when that is clearer than prose. Do not fill unknown sections
with generic recommendations.

State each fact once, in the section that owns it, and link to it from
elsewhere. Evidence sits inline with the claim it supports; there is no
separate evidence index.

## Provenance block

Place this directly below the title:

```markdown
<!-- ARCHITECTURE-DOC
schema: 1
audience: engineering
project: <package>
status: current|stale
source_revision: <commit>
base_revision: <baseline commit, or none>
generated_at: <YYYY-MM-DDTHH:MM:SSZ>
owners: <verified owners or unknown>
inspected_paths:
  - <repository-relative path>
impact_categories:
  - <category, initial or regenerated>
-->
```

`source_revision` is the `HEAD` commit the run documented. For an initial
generation or a full regeneration without a baseline, set `base_revision` to
`none`. For an initial generation, record `initial` as the only impact
category.

`inspected_paths` lists every repository path a fact in the document rests
on, whether the document links it or not. Use a directory for a tree you read
broadly and a file for a single file. Every repository path the document
links must lie under an entry, except files in the package's own `<package>/docs/architecture/` folder; the checker enforces this, and reports entries
that are absolute, leave the repository, or do not exist. Write
`generated_at` as `YYYY-MM-DDTHH:MM:SSZ`.

Provenance describes the document as delivered, not its first draft. Whenever
you change the document after writing its provenance, in the same run or a
later one, refresh `generated_at` and add the paths the change relies on to
`inspected_paths` in the same edit. Set `status: current` only when
every validation step you could run passed; record steps you could not run
(for example Mermaid rendering without tooling) as gaps in your report, not as
failures. Use `stale` when the document is known not to match
`source_revision`.

## Required visual illustrations

Use Mermaid embedded in Markdown and follow every diagram with an accessible
prose description.

### 1. Complete architecture

Use a C4-inspired context/container view showing:

- actors and external systems;
- process/deployment boundaries;
- stores and durable artifacts;
- major protocols or file contracts;
- verified connections to other repository projects;
- trust boundaries where relevant.

### 2. Component model

Show major runtime components and important internal modules grouped
hierarchically. Include dependency direction and label the main interface or
artifact crossing each boundary. Do not draw every source file, class, or
function.

Accompany the diagram with a component table. The table may sit between the
diagram and its prose description:

| Component | Responsibility | Inputs | Outputs | Depends on | Status | Evidence |
|---|---|---|---|---|---|---|

### 3. End-to-end runtime flows

Show the primary successful flow and material alternate/error paths. Use
sequence diagrams for interactions and flowcharts for transformations. Add
more than one flow only when distinct entry points or lifecycle phases cannot
be understood accurately in one diagram.

Diagram rules:

- use stable Mermaid identifiers and short labels;
- style nodes with the status classes of fact rule 7, and include a legend
  that lists only the classes the diagram uses;
- match direction and cardinality to verified implementation;
- avoid secrets and sensitive examples;
- keep diagrams readable; split by flow rather than shrinking text;
- link diagram concepts to the component or evidence tables.

## Human notes

End the document with:

```markdown
## Human notes

<!-- BEGIN HUMAN NOTES -->
<!-- Add manually maintained context here. This block is preserved verbatim. -->
<!-- END HUMAN NOTES -->
```

Human notes are context, not automatically verified architecture.

## Validation

First run the structural checker from the repository root:

```bash
uv run python .github/skills/document-engineering-architecture/scripts/check_architecture_doc.py \
  <package>/docs/architecture/engineering.md
```

Exit 0 prints `no issues`; exit 1 prints one `FAIL` line per structural
issue, each naming what to fix; exit 2 means the document could not be
checked (message on stderr). The checker's docstring lists what it checks. It
does not check that content is accurate.

A no-op synchronization (step 4) ends after step 4; the steps below apply
when you write or change the document.

Before finishing:

1. verify links, symbols, schemas, interface names, statuses, commands, and
   configuration against current implementation;
2. verify all substantive claims have evidence or an explicit status;
3. verify all three diagram types exist, parse when Mermaid tooling is
   available, and agree with prose and tables;
4. run the smallest relevant documentation, schema, CLI-help, or test checks
   needed to confirm documented behavior;
5. when the repository commits real inputs the project reads (for example files another program writes), run the current entry point
   over all of them. If that is too slow, use a sample and name how you
   chose it. Do this only when the entry point is read-only and needs no
   network access or credentials; otherwise record it as a step you could
   not run. Report aggregate counts per outcome or error only. Never print,
   quote or copy the inputs' content. Any outcome the document does not
   explain becomes a fact or an entry in `Known gaps and decisions needed`,
   without the count (fact rule 8);
6. compare with the executive document at
   `<package>/docs/architecture/executive.md` in the same working tree when
   it exists, and resolve contradictions without leaking unnecessary
   implementation detail into it. It is a peer document, not evidence: do not
   cite it as a source or list it in `inspected_paths`. If it does not exist,
   do not link to it; say so in your report;
7. verify the human-note block is unchanged;
8. report changed sections, impact categories, validations, gaps, and
   decisions needed.

Fix every checker issue (exit 1); they are structural and always fixable. If
another validation step fails and you cannot fix its cause, write the document
with `status: stale` and list the failures in your report. Never mark a
failing document current.
