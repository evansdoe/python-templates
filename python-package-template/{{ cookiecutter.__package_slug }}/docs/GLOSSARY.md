# Glossary

The words this project uses, each explained in plain language. People and
coding agents use these words in code names, tests, plans, checkpoints and
pull requests, so that one thing always has one name.

Add a term the first time a plan, checkpoint or pull request needs it. Explain
it in one sentence that someone new to the project understands, give an
example from this project, and say where it appears in the code.

## Project terms

<!-- One row per term, in alphabetical order. -->

| Term | In plain words | Example from this project | Where in the code |
| --- | --- | --- | --- |

## Workflow terms

How changes are made here; `.github/skills/dev-workflow/SKILL.md` has the
details.

| Term | In plain words |
| --- | --- |
| Checkpoint | A short report after a step, after which the agent waits for the developer if the pace says so. |
| Concern | One separate piece of work, done on its own branch. |
| Example map | The concrete inputs and the exact results everyone agrees on before any code is written. |
| Gate | The checks (formatting, lint, types, tests) that must pass before every commit. |
| Green | The smallest change that makes the new failing test pass. |
| Import contract | An automatic check that each part of the package uses only the parts the package map allows. |
| Pace | How often the agent stops so the developer can follow, from after every step to not at all. |
| Package map | The list of the package's parts: what each is for and what each may use. The project owner approves changes to it. |
| Prediction | Saying what a test run will show before running it, so that a misunderstanding shows up at once. |
| Red | A new test that fails because the program cannot do that yet: the expected starting point of each step. |
| Refactor | Tidying the code without changing what it does, while every test still passes. |
| Squash | Combining the small save points of a piece of work into one tidy commit before review. |
| Test list | The tests written first and switched off, simplest first; each is switched on in turn. |
| Walkthrough | The plain-language story of a branch, one entry per step, kept in `.walkthrough/<branch>.md` and never committed. |
| WIP commit | A small local save point after each step; never pushed. |
