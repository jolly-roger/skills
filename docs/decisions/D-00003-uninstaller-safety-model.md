# D-00003: Uninstaller Ownership and Safety Model

## Status

Proposed

## Date

2026-10-27

## Context

The planned uninstaller must remove agent-toolkit artifacts without deleting project-authored instructions, local skills, or similarly named resources owned by another toolkit. Existing installations do not have a manifest recording which files and directories were created by the installer.

The implementation therefore needs a conservative ownership model, a complete preview, and deliberate handling of partial filesystem failures.

## Decision

Treat only the following artifacts as owned by the current toolkit checkout:

- Content inside one valid `<!-- agent-toolkit:begin -->` and `<!-- agent-toolkit:end -->` block in the workspace root `AGENTS.md`.
- Direct skill symlinks under `.agents/skills/` whose resolved destination belongs directly to the current toolkit's `skills/` directory.
- `.agents/skills` and `.agents` directories only when they are empty after owned artifacts are removed.

The uninstaller will:

- Validate the complete workspace state and calculate an immutable uninstall plan before mutation.
- Reject incomplete, reversed, or duplicate managed markers.
- Refuse to operate through symlinked `AGENTS.md`, `.agents`, or `.agents/skills` paths.
- Preserve regular files, directories, foreign symlinks, and all `AGENTS.md` content outside the managed block.
- Preserve the toolkit repository's authoritative `AGENTS.md` during self-uninstallation.
- Preview the `AGENTS.md` diff and every skill link scheduled for removal.
- Support interactive confirmation, `--dry-run`, and `--yes`.
- Record raw symlink targets and restore removed links if a later principal operation fails.
- Be idempotent and report when a workspace is already uninstalled.

Do not add an installation manifest initially. If the toolkit checkout moved after installation, links that can no longer be proven to belong to the current checkout will be preserved.

## Alternatives considered

### Remove skills by filename

Matching names is insufficient proof of ownership and could delete project-local skills or links installed from another toolkit.

### Remove the complete `.agents` directory

The directory can contain unrelated agent configuration and must not be treated as wholly owned by this toolkit.

### Add an installation manifest immediately

A manifest would improve exact historical ownership, especially after moving the toolkit checkout, but would also require migration and transactional changes to the existing installer. Current markers and symlink destinations provide a sufficient conservative model for the first implementation.

### Apply removals without rollback

This is simpler but can leave managed rules and skill links in an inconsistent partially removed state after a filesystem failure.

## Consequences

### Positive

- Project-authored instructions and local skills remain protected.
- Users can inspect every mutation before applying it.
- Repeated uninstall operations are safe.
- Recoverable mid-operation failures do not normally leave partial link removal.

### Negative

- A moved toolkit checkout can leave old dangling skill links that require manual cleanup.
- The implementation needs explicit planning and rollback logic.
- The legacy installer cannot reveal whether an empty `AGENTS.md` existed before installation.

## Related documents

- [P-00001: Agent Toolkit Uninstaller](../plans/P-00001-uninstaller.md)
- [D-00001: Project Tooling Layout](./D-00001-project-tooling-layout.md)

## Supersedes

None

## Superseded by

None
