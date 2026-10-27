# D-00003: Uninstaller Ownership and Safety Model

## Status

Accepted

## Date

2026-10-27

## Context

The planned uninstaller must remove agent-toolkit artifacts without deleting project-authored instructions, local skills, or similarly named resources owned by another toolkit. Existing installations do not have a manifest recording which files and directories were created by the installer.

The implementation therefore needs a conservative ownership model, a complete preview, and deliberate handling of partial filesystem failures.

## Decision

Treat only the following artifacts as owned and removable by the uninstaller:

- Content inside one valid `<!-- agent-toolkit:begin -->` and `<!-- agent-toolkit:end -->` block in the workspace root `AGENTS.md`.
- Direct skill symlinks under `.agents/skills/` whose resolved destination belongs to:
  - The current toolkit's `skills/` directory (including dangling links whose lexical target belongs directly to the current checkout), or
  - Another existing agent-toolkit checkout (legacy or current layout) verified through conservative structural recognition.
- `.agents/skills` and `.agents` directories only when they are empty after owned artifacts are removed.

The uninstaller will:

- Validate the complete workspace state and calculate an immutable uninstall plan before mutation.
- Reject incomplete, reversed, or duplicate managed markers.
- Refuse to operate through symlinked `AGENTS.md`, `.agents`, or `.agents/skills` paths.
- Preserve regular files, directories, foreign symlinks, unproven dangling links, and all `AGENTS.md` content outside the managed block.
- Warn when an unproven dangling skill link remains outside the current checkout.
- Preserve the toolkit repository's authoritative `AGENTS.md` during self-uninstallation.
- Preview the `AGENTS.md` diff and every skill link scheduled for removal, identifying its recognized source checkout and recognition kind.
- Support interactive confirmation, `--dry-run`, and `--yes`.
- After confirmation, verify that every planned link still has its recorded raw target and that `AGENTS.md` still has its recorded content before applying changes.
- Repeat the relevant artifact check immediately before each destructive action; abort or roll back if workspace state changed after planning.
- Record raw symlink targets and restore removed links if a later principal operation fails.
- Normalize only boundary blank lines when removing the managed block, preserving spaces and tabs on retained nonblank project-authored lines.
- Be idempotent and report when a workspace is already uninstalled.

Do not add an installation manifest initially. If the toolkit checkout moved or was deleted after installation, dangling links that cannot be conservatively recognized as agent-toolkit-owned will be preserved with a warning.

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
- Project changes made after preview are detected rather than overwritten or deleted by a stale plan.
- Markdown-significant trailing whitespace outside the managed block is preserved.

### Negative

- A deleted or unrecognizable toolkit checkout can leave old dangling skill links that require manual cleanup.
- The implementation needs explicit planning and rollback logic.
- Optimistic preconditions detect ordinary concurrent edits but do not provide adversarial filesystem locking.
- The legacy installer cannot reveal whether an empty `AGENTS.md` existed before installation.

## Related documents

- [P-00001: Agent Toolkit Uninstaller](../plans/P-00001-uninstaller.md)
- [P-00002: Cross-Installation Uninstall Compatibility](../plans/P-00002-cross-installation-uninstall.md)
- [D-00001: Project Tooling Layout](./D-00001-project-tooling-layout.md)

## Supersedes

None

## Superseded by

None
