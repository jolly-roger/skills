# D-00002: Documentation Organization

## Status

Accepted

## Date

2026-10-27

## Context

The project needs a consistent place for implementation plans and durable project-wide decisions. These records serve different purposes: plans describe work and execution status, while decisions preserve selected approaches and their rationale.

Without separate indexes and naming conventions, records become difficult to discover and their current status becomes unclear.

## Decision

Store project documentation under `docs/` with category-specific directories and indexes:

```text
docs/
├── README.md
├── plans/
│   ├── README.md
│   ├── TEMPLATE.md
│   └── P-00001-short-name.md
└── decisions/
    ├── README.md
    ├── TEMPLATE.md
    └── D-00001-short-name.md
```

Implementation plans use the filename pattern `P-00001-{short-name}.md`. Project decisions use `D-00001-{short-name}.md`.

Each category's `README.md` contains a table linking to every record and showing its current status and creation date. The root documentation index links to the category indexes. A status change must update the record and its index entry in the same change.

Every plan and decision records its current status and one creation date in `YYYY-MM-DD` format. The creation date does not change when the record's status or content changes; Git history provides the detailed change timeline.

Decision statuses are:

- `Proposed` for a decision still under consideration.
- `Accepted` for a decision the project has adopted.
- `Rejected` for a considered decision that was not selected.
- `Superseded` for an accepted decision replaced by a newer record.

Accepted decisions should retain their historical rationale. Material changes require a new decision that supersedes the old one rather than rewriting the old record.

## Alternatives considered

### Keep plans and decisions in the repository root

This makes a small number of files visible but does not scale and mixes project records with operational files.

### Store decisions inside implementation plans

This reduces file count but loses durable decision history when implementation details change or a plan is completed.

### Use one combined documentation index only

This is initially simpler but makes category ownership and status maintenance less clear as records accumulate.

## Consequences

### Positive

- Plans and decisions are easy to discover and distinguish.
- Sequential identifiers provide stable references across documents and discussions.
- Decision history remains available when the implementation changes later.
- Status indexes provide a concise project overview.

### Negative

- Adding or changing a record requires maintaining its category index.
- Status duplication between a record and its index can drift if they are not updated together.

## Related documents

- [Implementation plans](../plans/README.md)
- [Project decisions](./README.md)

## Supersedes

None

## Superseded by

None
