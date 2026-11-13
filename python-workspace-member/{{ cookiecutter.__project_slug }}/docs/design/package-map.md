# Package map: `{{ cookiecutter.__module_name }}`

The agreed sub-packages of this package. Fill it in before writing the first
module, and change it before adding, renaming or removing a sub-package. The
project owner approves every change.

## Map

List sub-packages from highest to lowest: an entry may import only from
entries below it.

| Sub-package | Role | What belongs here | May import |
| --- | --- | --- | --- |
| _none yet_ | | | |

## Roles

Names come from this package's subject. Roles are the same in every package:

| Role | Meaning |
| --- | --- |
| entry | Command line and other entry points. Parses input, builds the outside-world objects, calls use cases. Nothing imports it. |
| use case | One thing the package does for its user, orchestrating subject logic and the outside world. |
| outside world | Code that talks to one external system: files, a database, an API, a model. |
| subject logic | Data types and pure rules of the subject. No file, network or SDK access. |
| settings | Configuration values, loaded at the entry and passed down. |

## Naming rules

- Name a sub-package after a subject of this package or the external system it
  talks to (`sources`, `storage`, `powershell`), never after a kind of code
  (`utils`, `helpers`, `common`, `managers`).
- The "What belongs here" sentence must not need the word "and".
- A sub-package needs at least two modules, or one that is certain to grow;
  otherwise keep it a module.

## Keeping the contract in step

The map is enforced by `[tool.importlinter]` in `pyproject.toml`. After the map
changes, update `layers` there in the same change, in the same order. Put
entries that must not import each other on one line, separated by ` | `.
`tests/test_architecture.py` fails until the two agree.
