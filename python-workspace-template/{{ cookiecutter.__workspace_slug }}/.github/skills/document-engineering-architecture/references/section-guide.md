# Section guide

What each technical section of `engineering.md` must cover. Read a section's
part before you write or rebuild that section. Every item below is documented
only when verified; call out missing behavior rather than inventing it.

## Interfaces, contracts, and data model

For each important boundary, document:

- producer and consumer;
- transport or artifact;
- schema and version;
- validation point;
- compatibility and failure behavior;
- evidence.

Also document the schemas, models, file formats and durable artifacts the
project reads or writes, with the fields that matter to a consumer.

## Configuration and precedence

Document sources and precedence, defaults, required values, validation, and
where secrets enter. Use placeholders, never real values.

## Failure modes, recovery, and idempotency

Cover expected failure classes, surfaced errors, partial output, retries,
resumption, cleanup, concurrency, locking, idempotency, and operator recovery.

## Security and privacy

Document data classification, trust boundaries, redaction and minimization,
credential handling, external processing, retention, and human review. Link
unresolved security decisions rather than resolving them speculatively.

## Testing and quality gates

State what unit, contract, integration, golden, property, evaluation, and
manual tests protect, and which CI gates run them. Name tests; do not count
them.

## Packaging, deployment, and environments

Document actual packaging and deployment environments, platform assumptions,
and unsupported scenarios.
