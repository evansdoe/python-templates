# Section guide

Read the part for a section before you write or rebuild that section.

## Executive summary

At most 20 non-empty lines, readable on its own. Answer, in this order: what
the project enables and for whom; where it stands; the next milestone; the top
risks; what the reader must decide or provide. Link to the sections below
rather than repeating them.

## What changed

The latest synchronization only, rewritten each time: the date, then up to
five bullets in business terms. An initial generation writes `First version.`
Git keeps the history.

## Capabilities and status

`| Capability | Business value | Status | Source |`, then any dated
measurement of what the capabilities achieve on real inputs.

## How it works

The context diagram, who is involved, the system boundary, the value-flow
diagram, and how the project is run and supported.

## Controls and risks

One row per risk:
`| Risk | Control | Enforcement | Residual risk | State | Source |`. Give a
likelihood or impact rating only when a repository source rates it.

## Dependencies

`| Dependency | What flows | Status | Source |`. Name every program that writes
or reads a shared artifact, not only the documented producer.

## Roadmap and resourcing

`| Step | Delivers | Target date | Progress | Source |`, then effort and cost.
Target dates and cost come only from the project status file.

## Decisions and gaps

`### Decisions` as
`| Decision | Who decides | What it blocks | If undecided | Source |`, then
`### Evidence conflicts`, then `### Missing management inputs`.

## Glossary

Only terms a reader of this audience would not know.

## Sources

`| Marker | Source | Supports |`, one row per marker. The Marker cell holds
the plain marker (`S1`), not a link; the Source cell holds the link.
