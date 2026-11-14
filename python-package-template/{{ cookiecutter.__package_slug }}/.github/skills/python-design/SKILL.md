---
name: python-design
description: Where Python code lives and what shape it takes - an owner-approved package map enforced by an import contract, design stubs before tests, tests/unit mirroring the package, and triggers for sub-packages, classes, patterns and metaprogramming. Use when planning a subtask, adding a module or class, at TDD Refactor, and when an architecture test fails.
---

# Python design

Tests decide behavior. This skill decides where code lives and what shape it
takes. It rests on three ideas:
1. Design decisions are made before the test list and approved by the project
   owner, because a design that grows from one small Green step after another
   is rarely revisited.
2. Sub-package names come from the package's subject and are agreed in a
   package map. Their import direction is checked by a test. Classes,
   interfaces and patterns are added later, only on an observed trigger.
3. A failing architecture check is a question for the owner. It is never
   fixed by shuffling lines, renaming a module or loosening the check.

## 1. The files this skill works with
| File (per package) | Holds |
|---|---|
| `docs/design/package-map.md` | The approved sub-packages: name, role, what belongs there, what it may import |
| `[tool.importlinter]` in `pyproject.toml` | The same map as an enforced `layers` contract with `exhaustive = true` |
| `tests/test_architecture.py` | Runs the contract; checks that map and contract name the same sub-packages and that `tests/unit/` mirrors the package |
| `docs/PLAN.md` | Concerns, decisions log, open questions. Designs do not go here |

If one of these is missing, say so and propose adding it. Do not work around it.

## 2. The package map
Propose the map before the first module is written, and again before any
sub-package is added, renamed, split or removed. Wait for approval. Then change
the map and the `layers` list in the same commit and record the decision in
`docs/PLAN.md`. When nobody can approve (an unattended run), follow the
provisional rule in `.github/skills/dev-workflow/references/pace.md`.

**Roles.** Names differ per package; roles do not. Every sub-package has one:

| Role | Meaning | May import |
|---|---|---|
| entry | Command line and other entry points: parse input, build outside-world objects, call use cases | everything below |
| use case | One thing the package does for its user | subject logic, settings; outside world only through parameters |
| outside world | Talks to one external system: files, a database, an API, a model | subject logic, settings |
| subject logic | Data types and pure rules. No file, network, environment or SDK access | other subject logic |
| settings | Configuration values, loaded at the entry and passed down | nothing |

Use-case and outside-world sub-packages are siblings: neither imports the
other, and the entry connects them.

**Naming.**
- Name a sub-package after a subject of the package or the external system it
  talks to (`sources`, `storage`, `powershell`). Never after a kind of code:
  `utils`, `helpers`, `common`, `misc`, `managers`, `core`.
- Its "what belongs here" sentence must not need the word "and".
- When the subject is not yet clear, start with one module per role and name
  them plainly. Revisit the map when a trigger in section 3 fires.

**How to propose.** Read the package's purpose (README, `PLAN.md`, the task).
Post the map table with one row per sub-package, highest first, and the
resulting `layers` list. State what you were unsure about.

## 3. When to split
Group by what changes together. Splitting a file without reducing what the
parts know about each other is not an improvement.
- Module to package: the module holds two groups of names that do not call
  each other, or serves two external systems or two subjects.
- New sub-package inside one: 3 or more modules serve one external system or
  concept. Its `__init__.py` exposes its API and others import from there.
- Start with one module per role. Split a module only when it passes about
  150 lines or has two reasons to change. A helper used by one module stays
  in that module; a three-part change should not need three new files.
- Never: a sub-package for one module that will not grow; nesting deeper than
  `sub-package/sub-package/module`; an import cycle (a cycle means a name is
  in the wrong place).
- Entry points live only in the entry sub-package. A module elsewhere does
  not define `main()` or parse arguments.

## 4. Design stubs (in the plan, before the test list)
For each subtask, post the design as code and get it approved with the plan:
- the data types that cross module boundaries, as frozen dataclasses with
  their fields;
- every new public function or method as a typed signature with a one-line
  docstring and no body;
- the file path of each, which must fit the package map.

After approval the stubs go into their files (bodies raise
`NotImplementedError`) together with the test list, and each test imports from
the stubbed path. If implementation shows a stub was wrong, stop, say what
changed, and get the change approved.

## 5. Shape of the code
Default: small functions and frozen dataclasses. One function does one job at
one level of detail; a function that fetches, decides and writes is three
functions and a short one that calls them.
- Add a class or an interface only on an observed trigger, name the trigger
  when you do, and ask first when it adds an interface.
- A class that does work takes its data as one frozen object (dataclass
  inside, Pydantic model at the edge) and its collaborators as separate
  parameters; see `references/code-shapes.md`, section 3.
- Dependencies arrive as parameters. No module-level clients or singletons; no
  environment reads outside the entry and settings.
- Metaprogramming is off by default.

Before adding a class, an interface (`Protocol` or `ABC`), a named pattern or
anything beyond a simple decorator, read `references/code-shapes.md` and follow
its tables.

## 6. Boundaries
- **Input:** convert raw input (JSON, rows, environment values) into typed
  objects once, where it enters. Only typed objects travel inward; no
  `dict[str, Any]` between sub-packages.
- **SDKs:** each third-party SDK is imported in exactly one outside-world
  sub-package, and a `forbidden` import contract says so.
- **Errors:** the package has one base exception. Subject logic raises the
  package's own errors; outside-world code turns third-party errors into
  them; only the entry catches broadly. Never catch an error just to continue.
- **Public surface:** a sub-package's `__init__.py` re-exports its public
  names and lists them in `__all__`. Other sub-packages import from there.
  Modules meant to stay internal start with `_`.

Examples for each are in `references/boundaries.md`; read it before adding an
exception class, an SDK import or a sub-package `__init__.py`.

## 7. Tests
- Unit tests live in `tests/unit/<same path as in src>`. When code moves, its
  tests move in the same commit.
- Other kinds of test get their own folder beside `unit/` (for example
  `e2e/`), with a marker.
- Test files never import each other. Share helpers through fixtures in
  `tests/conftest.py`, or a `testing` module inside the package if other
  packages need them.
- Unit tests of subject logic and use cases use fakes passed as parameters.
  Only outside-world tests touch real files or services.

## 8. In the TDD cycle
- **Plan:** package-map change (if any) and design stubs, approved.
- **Green:** smallest change, inside the stub. No new modules, classes or
  patterns here.
- **Refactor:** after the usual review, check sections 3, 5 and 6 against the code
  just written and add one checkpoint line: `Structure:` plus the move and its
  trigger, or `no trigger`. A structural move is its own refactoring: green
  before, no behavior change, imports and mirrored tests updated, green after.
- **End of subtask:** print the package tree next to the approved map and
  stubs, and explain every difference.

## 9. When a check fails
| Failure | Do |
|---|---|
| Import contract broken | The import points the wrong way. Move the code, or pass the dependency in as a parameter |
| Module "not listed as layers" | A new top-level name. Propose its package-map row; do not add it to the contract unapproved, except provisionally in an unattended run (section 2) |
| Map and contract disagree | Bring both in line with what was approved; if nothing was approved, ask |
| `tests/unit` folder has no sub-package | Move the tests to the mirrored path |
| Forbidden-import contract broken | An SDK is used outside its sub-package. Move the call there and pass the result or the object in |
| Linter flags a broad or silent `except` | Catch the specific error, or let it rise to the entry. No `noqa` without approval |
| Linter size limit (function length, branches, arguments) | Stop and propose a split by responsibility (section 5). No `noqa`, no raised limit, no mechanical split, without approval |

## 10. Further references
Read these only when the situation applies:
- `references/code-shapes.md`: before adding a class, interface, pattern or
  metaprogramming.
- `references/boundaries.md`: before adding an exception class, an SDK
  import or a sub-package `__init__.py`.
- `references/existing-packages.md`: when the package is already flat or has
  no package map.
- `references/quality-checks.md`: when asked whether code is modular,
  reusable, maintainable, efficient or production-ready.
