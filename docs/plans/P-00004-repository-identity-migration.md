# P-00004: Repository Identity Migration

## Status

Implemented

## Date

2026-11-04

## Objective

Implement [D-00005](../decisions/D-00005-repository-and-installation-identity.md) by making `jolly-roger/skills` and `jolly-roger.skills` the canonical public and internal identities while safely migrating or removing installations created with the legacy `agent-toolkit` identity.

The migration must not duplicate managed rules, lose manifest-backed ownership, overwrite project content, or convert ambiguous workspace state automatically.

## Scope

- Centralize canonical and legacy identity values in one shared module.
- Replace canonical `agent-toolkit` markers with `jolly-roger-skills` markers.
- Replace the canonical manifest filename with `.agents/jolly-roger-skills-manifest.json`.
- Replace the canonical manifest format with `jolly-roger.skills`.
- Migrate valid legacy managed blocks and manifests during installation.
- Allow uninstallation of either valid canonical or valid legacy installations.
- Reject malformed, conflicting, or ambiguous combinations before mutation.
- Update command output, active README content, examples, self-install ignore rules, docstrings, and current implementation terminology.
- Preserve historical implemented decisions and plans without rewriting their original identity references.
- Add unit and integration coverage for fresh canonical installations, legacy migration, direct legacy uninstall, mixed states, rollback, and idempotency.

## Non-goals

- Changing copied-skill ownership, hashing, update, retirement, or removal behavior implemented by P-00003.
- Renaming `.agents/`, `.agents/skills/`, `AGENTS.md`, or skill directories.
- Renaming a user's existing local checkout directory.
- Editing Git remotes or relying on GitHub redirects at runtime.
- Inspecting Git configuration, remotes, repository names, or network state to establish ownership.
- Rewriting historical implemented decisions, plans, or Git history to use the new name.
- Removing legacy read compatibility in this change.
- Adding aliases that permit new artifacts to be written with the retired identity.

## Related decisions

- [D-00004: Copy Skills into Workspaces](../decisions/D-00004-copy-skills-into-workspaces.md)
- [D-00005: Repository and Installation Identity](../decisions/D-00005-repository-and-installation-identity.md)

## Design

### Identity model

Add `tools/common/identity.py` with immutable identity values:

```python
@dataclass(frozen=True)
class InstallationIdentity:
    namespace: str
    marker_slug: str
    manifest_filename: str
    manifest_format: str


CANONICAL_IDENTITY = InstallationIdentity(
    namespace="jolly-roger.skills",
    marker_slug="jolly-roger-skills",
    manifest_filename="jolly-roger-skills-manifest.json",
    manifest_format="jolly-roger.skills",
)

LEGACY_IDENTITY = InstallationIdentity(
    namespace="agent-toolkit",
    marker_slug="agent-toolkit",
    manifest_filename="agent-toolkit-manifest.json",
    manifest_format="agent-toolkit.skills",
)
```

Derive begin and end markers from each identity's marker slug. Keep legacy values explicit and confined to migration and compatibility paths. Canonical installation code must not select an identity from ambient state.

Rename active repository-root variables and parameters from `TOOLKIT` or `toolkit_root` to `REPOSITORY_ROOT`, `repository_root`, or another context-accurate name. Generic prose may still use “tooling,” but active project branding and terminal output must not call the project `agent-toolkit`.

### Data, calculations, and actions

Represent marker state, manifest state, identity classification, migration actions, and conflicts as immutable values.

Keep these decisions deterministic after facts are collected:

- Classifying marker state as absent, canonical, legacy, malformed, or conflicting.
- Classifying manifest state as absent, canonical, legacy, malformed, or conflicting.
- Deciding whether a workspace requires no migration, marker migration, manifest migration, both migrations, or rejection.
- Calculating canonical `AGENTS.md` and manifest bytes.
- Calculating installer and uninstaller actions from validated identity and ownership state.

Keep filesystem reads, atomic writes, renames, removals, previews, and terminal output at command boundaries. Pass identity values explicitly to marker and manifest calculations rather than consulting mutable globals inside domain logic.

### Managed-block classification

Inspect the complete workspace `AGENTS.md` for both canonical and legacy marker pairs.

Valid states:

| State | Installer behavior | Uninstaller behavior |
| --- | --- | --- |
| No managed block | Add a canonical block when installing. | No block action. |
| One canonical block | Replace its payload when needed and retain canonical markers. | Remove it. |
| One legacy block | Replace it in place with one canonical block and current payload. | Remove it directly. |

Reject before mutation when:

- Either identity has incomplete, reversed, or duplicate markers.
- Canonical and legacy managed blocks both exist.
- Marker text is nested or ordered in a way that makes block ownership ambiguous.

Legacy-to-canonical migration preserves all project-authored content before and after the managed block. It changes only the managed markers and payload according to normal installation rules.

### Manifest classification and migration

Inspect both canonical and legacy manifest paths without following symlinks.

Valid states:

| State | Installer behavior | Uninstaller behavior |
| --- | --- | --- |
| No manifest | Create canonical metadata for installed copied skills when required. | No manifest action. |
| Canonical manifest | Validate and update using the canonical format. | Use it for ownership and update or remove it normally. |
| Legacy manifest | Validate with the legacy format, preserve its ownership records, and serialize equivalent canonical metadata. | Use it directly for ownership and remove or update it under the legacy path as part of uninstall. |

Reject before mutation when:

- Both manifest files exist, even if they appear equivalent.
- A manifest path is a symlink or non-regular filesystem entry.
- The filename and embedded format identity disagree.
- Either manifest fails its schema, normalized-path, inventory, or digest validation.

Manifest migration must preserve the schema version and all validated skill ownership records. Write the canonical manifest atomically and remove the legacy file only within the same recoverable application transaction. Never treat an invalid legacy manifest as an empty installation.

Marker and manifest identities may differ in a partially migrated workspace, such as a legacy block with a canonical manifest. This is not ambiguous when each artifact exists in only one valid form. Installation normalizes both artifacts to canonical identity; uninstallation removes each valid artifact according to its observed identity.

### Installer workflow

Extend installation planning to:

1. Inspect canonical and legacy marker and manifest facts before calculating changes.
2. Validate copied-skill ownership using whichever single valid manifest identity is present.
3. Calculate the normal P-00003 skill changes together with identity migration actions.
4. Preview marker migration, manifest migration, skill changes, and all preserved project content.
5. Abort the complete plan on identity conflicts or invalid legacy state.

After confirmation, revalidate the recorded marker, manifest, copied-skill, and source state. Apply normal skill changes and identity migration as one recoverable transaction. Write only canonical markers and a canonical manifest. Remove the legacy manifest only after the canonical replacement is safely staged, and restore its exact prior bytes and path if a later principal operation fails.

A repeated installer run after migration must be a canonical no-op when rules and skills are unchanged.

### Uninstaller workflow

Extend uninstallation planning to:

1. Classify canonical and legacy marker and manifest facts.
2. Load ownership from the one valid manifest, regardless of identity.
3. Calculate normal copied-skill removal and preservation actions.
4. Remove the one valid managed block without first requiring migration.
5. Update or remove the manifest at its observed path according to remaining ownership records.
6. Preview the artifact identity and every planned mutation.

Reject dual or malformed identity state before removing copied skills or project rules. Preserve all existing stale-plan checks, backup-based removals, rollback, modified-copy warnings, and empty-directory cleanup.

`Already uninstalled` requires the absence of canonical and legacy managed blocks, both manifest files, and every otherwise removable managed artifact.

### Active naming migration

Update active project surfaces:

- Use `🏴‍☠️ Jolly Roger's Skills` as the README title and place the tagline `Code by the rules. Sail with the agents.` directly before the technical repository description.
- Use `A pirate's toolkit for better coding agents` as the GitHub repository description. The live repository description matches this exact accepted value without trailing punctuation.
- Update README examples, clone or path placeholders, and install/uninstall terminology.
- Command success, no-op, warning, and error messages.
- Current code constants, docstrings, comments, parameter names, and test names where they describe the active identity.
- Self-installation `.gitignore` entries for the canonical manifest while retaining the legacy manifest ignore entry during migration support.
- Any badges, automation, or configuration that contains the old repository URL or active repository name.

Do not mechanically rewrite historical implemented decisions and plans. D-00005 and P-00004 explain why those records use the former identity.

### Legacy compatibility boundary

Legacy support is read-and-migrate or read-and-remove compatibility only:

- Fresh installation writes canonical artifacts exclusively.
- Reinstallation of a legacy workspace migrates it to canonical artifacts.
- Direct uninstall accepts legacy artifacts and removes them safely.
- No configuration option selects the legacy identity for new writes.
- Generic names, repository structure, Git remotes, and checkout directory names are never ownership evidence.

Removing this compatibility requires a later decision and plan. Until then, legacy behavior remains isolated behind `LEGACY_IDENTITY` rather than mixed into canonical constants.

## Implementation steps

1. Add immutable canonical and legacy identity definitions in `tools/common/identity.py`.
2. Refactor marker parsing and content transformations to accept explicit identities and classify both marker forms without mutation.
3. Refactor manifest path and format validation to accept one explicit identity while preserving all P-00003 schema and ownership checks.
4. Add pure workspace identity classification and migration-plan calculations.
5. Integrate marker and manifest migration into installer planning, preview, precondition validation, application, and rollback.
6. Integrate dual-identity removal into uninstaller planning, preview, precondition validation, application, and rollback.
7. Replace canonical active strings, constants, command output, repository-root variable names, docstrings, and comments.
8. Update README usage and self-install ignore rules without duplicating migration details documented here.
9. Add unit, integration, stale-state, rollback, and regression tests described below.
10. Audit tracked active files for unintended canonical `agent-toolkit` references, allowing only explicit legacy compatibility and historical implemented records.
11. Run the complete test suite and manually exercise fresh install, legacy migration, canonical uninstall, direct legacy uninstall, self-installation, dry-run, decline, conflict, and rollback flows.
12. When every acceptance criterion passes, mark this plan `Implemented` and update `docs/plans/README.md` in the same change.

### Implementation review notes

All implementation steps, review items, migration matrix tests, and manual workflow exercises are complete:

1. **Partial-state installer tests**: `test_migrate_partial_workspace_legacy_markers_canonical_manifest` seeds a valid canonical manifest and owned skill copies directly before invoking the installer, verifying marker migration while preserving canonical ownership records and project-authored content. `test_migrate_partial_workspace_canonical_markers_legacy_manifest` similarly seeds legacy manifest state and verifies canonical migration without ownership loss.
2. **Self-installation coverage under both identities**: `test_self_install_leaves_agents_md_unchanged` covers canonical self-installation, and `test_legacy_self_installation_preserves_authoritative_agents_md_and_migrates_manifest` verifies that self-installing from a workspace with a legacy manifest preserves the authoritative `AGENTS.md` and migrates only installable artifacts to canonical identity.
3. **Supported Python versions**: Active documentation (`README.md`) declares Python 3.13 and Python 3.14 (requiring Python 3.10+ standard-library syntax). The complete test suite runs and passes cleanly on every declared version using only the standard library.
4. **GitHub metadata reconciliation**: The live repository description matches the accepted value `A pirate's toolkit for better coding agents` (without trailing punctuation), reconciled across D-00005, P-00004, and repository documentation.
5. **Manual workflow verification**: End-to-end execution of fresh install, legacy migration, canonical uninstall, direct legacy uninstall, dry-runs, declines, and conflicts verified and preserved.

## Test plan

### Identity and marker tests

- Derive exact canonical and legacy marker strings from immutable identity values.
- Add a canonical managed block to an unmanaged file.
- Replace a canonical managed block without changing project-authored content.
- Migrate one valid legacy block to one canonical block in the same position.
- Remove either a canonical or legacy block during uninstall.
- Reject incomplete, reversed, duplicate, nested, or simultaneous canonical and legacy blocks.
- Reject a supplied replacement block whose complete classification does not match `target_identity`, including a canonical block containing nested legacy markers.
- Preserve Markdown-significant whitespace outside migrated or removed blocks.

### Manifest tests

- Resolve the exact canonical and legacy manifest paths from their identities.
- Accept matching filename and embedded format pairs.
- Reject mismatched filename and format identities.
- Migrate a valid legacy manifest to byte-deterministic canonical metadata without changing ownership records.
- Remove or update a valid legacy manifest during direct uninstall.
- Reject simultaneous canonical and legacy manifests.
- Reject symlinked, non-regular, malformed, unsupported, or unsafe manifests before mutation.
- Preserve every P-00003 inventory, digest, normalized-path, and modified-copy invariant under both identities.

### Installer integration tests

- Fresh installation writes only canonical markers and the canonical manifest.
- Reinstalling a canonical workspace remains idempotent.
- Installing into a legacy workspace migrates markers and manifest while preserving project content and copied skills.
- Normalize a valid workspace containing legacy markers and a pre-existing canonical manifest to canonical identity without losing its ownership records.
- Normalize a valid workspace containing canonical markers and a pre-existing legacy manifest to canonical identity without losing its ownership records.
- Reject dual-marker and dual-manifest workspaces without mutation.
- Reject invalid legacy state without treating it as absent.
- Preview identity migrations during `--dry-run` without writing files.
- Declining confirmation leaves exact legacy bytes and paths unchanged.
- A failure after one migration action restores legacy markers, manifest path, manifest bytes, and copied-skill state.
- Self-installation with either canonical or legacy manifest identity preserves the authoritative `AGENTS.md`; legacy self-installation migrates only installable workspace artifacts to canonical identity.

### Uninstaller integration tests

- Uninstall a canonical workspace completely.
- Uninstall a valid legacy workspace directly without first migrating it.
- Uninstall a valid partially migrated workspace.
- Preserve modified copied skills and the matching observed-identity manifest records.
- Reject conflicting or malformed identity state before removing rules or skills.
- Keep self-uninstallation from modifying the repository's authoritative `AGENTS.md` under both identities.
- Report already uninstalled only when neither identity has managed artifacts.
- Modify an otherwise removable copied skill after preview and verify stale-plan validation aborts before removing the changed directory or updating its manifest.

### Naming and regression tests

- Assert canonical constants, output, new manifests, and new markers contain no active `agent-toolkit` identity.
- Assert fresh writes never produce legacy identifiers.
- Keep explicit legacy fixtures and compatibility constants clearly named as legacy.
- Confirm repository-root renames do not change filesystem ownership behavior.
- Preserve all P-00003 copied-skill update, retirement, conflict, rollback, and safety tests.
- Import and invoke the installer and uninstaller under every supported Python version so annotation evaluation and command startup are covered, including Python 3.12.
- Declare the supported Python version range in active documentation and keep the test matrix synchronized with it.
- Run the complete suite on every supported Python version using only the standard library.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Migration creates two managed blocks. | Classify both marker identities before mutation and reject any dual-block state. |
| Manifest migration loses ownership records. | Fully validate and compare the parsed domain model before serializing canonical metadata. |
| A filename and embedded format disagree. | Require an exact identity match and abort before skill or rule mutation. |
| A failure leaves both manifest files or neither file. | Stage canonical metadata, include both paths in preconditions, and restore exact prior state on recoverable failure. |
| Legacy compatibility becomes a second permanent write path. | Keep one canonical writer and isolate legacy handling in explicit read/migrate/remove branches. |
| Generic `skills` naming collides with another tool. | Use the owner-qualified namespace and `jolly-roger-skills` artifact slug. |
| Historical documents become misleading after mechanical renaming. | Preserve implemented records and explain the identity transition in D-00005 and P-00004. |
| Old repository URLs remain in active automation. | Audit active configuration and documentation instead of relying solely on GitHub redirects. |
| Local checkout directory names differ from the repository name. | Derive behavior from script location and explicit identity constants, never the directory basename. |

## Acceptance criteria

- Fresh installation writes `jolly-roger-skills` markers and `.agents/jolly-roger-skills-manifest.json` with format `jolly-roger.skills`.
- No fresh installation artifact or canonical command output uses `agent-toolkit`.
- A valid legacy installation migrates atomically to canonical markers and manifest without changing project-authored content or losing copied-skill ownership.
- The uninstaller removes valid canonical and legacy installations safely.
- Dual, malformed, or mismatched identity states fail before mutation with actionable diagnostics.
- Dry-run and interactive decline make no filesystem changes.
- Stale migration plans abort safely, and recoverable failures restore exact prior marker, manifest, and copied-skill state.
- Repeated installation after migration is idempotent and writes no legacy identity.
- Generic repository structure, Git state, and checkout names are not used as ownership evidence.
- The README title is `🏴‍☠️ Jolly Roger's Skills`, followed by the tagline `Code by the rules. Sail with the agents.` and the technical repository description.
- Active README command examples and technical identifiers use `jolly-roger/skills` or `skills` consistently.
- The live GitHub repository description exactly matches the value accepted by D-00005, including punctuation, and active documentation accurately records its applied state.
- Historical implemented decisions and plans retain their original terminology.
- Copied-skill removal revalidates the exact previewed target inventory and aborts if the target changes before application.
- All pre-existing marker, whitespace, copied-skill safety, stale-state, and rollback regression tests remain present alongside the identity-migration tests.
- Active implementation and test terminology uses the canonical project identity except in explicit legacy compatibility paths and historical records.
- Installer and uninstaller modules import and start successfully on every supported Python version without unresolved annotations.
- Migration-plan data contains no unused identity parameters or state fields: each recorded value controls validation, preview, or application behavior.
- Managed-block replacement validates the complete supplied block and cannot emit malformed, nested, opposite-identity, or dual-identity markers.
- Installer tests construct both partial marker/manifest identity combinations before the operation under test and prove ownership preservation.
- Self-installation is covered under canonical and legacy manifest identities and preserves the authoritative `AGENTS.md` in both cases.
- Active documentation declares the supported Python versions, and the complete suite passes on every declared version.
- The complete test suite passes on every supported Python version.

## Open questions

- None. Supported Python versions are defined as Python 3.13 and Python 3.14 (requiring Python 3.10+ standard-library syntax). The test suite passes on both declared versions without external dependencies.
