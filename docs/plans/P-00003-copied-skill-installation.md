# P-00003: Copied Skill Installation

## Status

Implemented

## Date

2026-11-04

## Objective

Implement [D-00004](../decisions/D-00004-copy-skills-into-workspaces.md) by replacing workspace skill symlinks with self-contained copied skill directories and manifest-backed ownership.

The installer must safely create and update copied skills without overwriting project-owned or locally modified content. The uninstaller must remove only copies whose ownership and current content it can prove, while preserving the existing managed-`AGENTS.md`, preview, confirmation, rollback, and idempotency guarantees.

## Scope

- Replace symlink creation in `tools/install.py` with recursive skill-directory copies.
- Add a versioned `.agents/agent-toolkit-manifest.json` that records installed skill targets and deterministic content inventories.
- Validate source skill trees and reject symlinks, special files, invalid names, and paths that escape the source skill directory.
- Classify installed skill targets as absent, exact managed copies, modified managed copies, unmanaged conflicts, or provable legacy links.
- Install new skills and update unchanged managed copies without overwriting modified or unmanaged content.
- Remove exact managed copies whose source skills no longer exist, while preserving modified copies.
- Remove exact manifest-backed skill copies during uninstall.
- Preserve modified copies, unmanaged directories, foreign files, and unproven symlinks with actionable diagnostics.
- Migrate legacy links that can be proven to target the checkout running the command.
- Remove the cross-checkout structural ownership heuristic superseded by D-00004.
- Preserve managed `AGENTS.md` behavior, self-installation, self-uninstallation, dry-run, confirmation, stale-plan detection, rollback, and empty-directory cleanup.
- Update tests and concise user documentation for copied-skill behavior.

## Non-goals

- Automatically removing or replacing legacy links owned by another checkout when ownership cannot be proven without structural inference.
- Following or copying symlinks found inside source skill directories.
- Merging locally modified installed copies with newer toolkit content.
- Automatically changing a consuming workspace's `.gitignore`.
- Restoring files deleted or modified outside agent-toolkit after installation.
- Providing adversarial filesystem locking or crash-proof transactions across multiple filesystem operations.
- Introducing a package manager, database, third-party dependency, Git inspection, or network requirement.
- Changing managed-block marker semantics or unrelated agent rules.

## Related decisions

- [D-00001: Project Tooling Layout](../decisions/D-00001-project-tooling-layout.md)
- [D-00004: Copy Skills into Workspaces](../decisions/D-00004-copy-skills-into-workspaces.md)

## Design

### Installed artifact layout

Use the following workspace layout:

```text
<workspace>/
├── AGENTS.md
└── .agents/
    ├── agent-toolkit-manifest.json
    └── skills/
        ├── merge-master/
        │   └── SKILL.md
        └── pragmatic-functional-programming/
            ├── SKILL.md
            └── references/
                └── ...
```

Skill directories and their contents are regular filesystem entries owned by the workspace. No installed artifact may be a symlink.

The source repository will continue ignoring its self-installed `.agents/skills/` directory and will also ignore its self-installation manifest. The installer will not edit `.gitignore` in other workspaces; those repositories decide whether installed skills are committed or ignored.

### Manifest format

Store ownership metadata at `.agents/agent-toolkit-manifest.json` using deterministic UTF-8 JSON with a final newline. The initial schema is:

```json
{
  "format": "agent-toolkit.skills",
  "version": 1,
  "skills": {
    "review": {
      "target": "skills/review",
      "entries": [
        {
          "path": "SKILL.md",
          "type": "file",
          "sha256": "<lowercase-hex-digest>"
        }
      ]
    }
  }
}
```

Manifest rules:

- Skill names are direct child names and cannot be empty, `.`, `..`, absolute, or contain path separators.
- Targets are normalized POSIX paths relative to `.agents/` and must equal `skills/<skill-name>`.
- Entries are sorted by normalized relative path and contain no duplicates.
- Each directory, including an empty directory, is recorded with `type: "directory"`.
- Each regular file is recorded with `type: "file"` and the SHA-256 digest of its bytes.
- Entry paths must be normalized, relative, nonempty, and confined to their skill target.
- Symlinks and other filesystem types are invalid.
- Unknown manifest format names or versions are rejected before any mutation.
- The manifest path must be absent or a non-symlinked regular file; other filesystem types are rejected.
- Absolute source-checkout paths are not stored; ownership remains valid after the source checkout moves or disappears.

Serialize manifest keys and entries deterministically so equal installation state produces byte-identical metadata. Parse and validate all untrusted manifest data before constructing trusted domain values.

### Data, calculations, and actions

Represent source snapshots, manifest entries, observed target snapshots, classifications, install actions, and uninstall actions as immutable values.

Keep these calculations independent of filesystem mutation:

- Manifest parsing and schema validation after JSON decoding.
- Normalized-path validation.
- Source and target inventory comparison.
- Content classification.
- Install and uninstall plan construction.
- Manifest state transitions after planned additions, updates, preservation, or removals.

Keep these actions at explicit boundaries:

- Reading and hashing source or workspace files.
- Creating staging directories and copying bytes.
- Renaming, replacing, or removing workspace artifacts.
- Atomically writing `AGENTS.md` and the manifest.
- Printing previews, warnings, and final outcomes.

The command modules orchestrate these calculations and effects. Shared modules must receive toolkit and workspace paths explicitly rather than derive them from process state.

### Shared module responsibilities

Replace the symlink-oriented shared model with copy-oriented modules:

```text
tools/common/
├── agents_file.py
├── filesystem.py
├── skill_files.py
└── skill_manifest.py
```

- `skill_manifest.py` owns manifest domain types, schema validation, deterministic serialization, inventory comparison, and manifest state transitions.
- `skill_files.py` owns source discovery, filesystem inspection, hashing, staging, copy application, legacy-link inspection, removal, and restoration.
- `filesystem.py` retains atomic file replacement and narrowly scoped directory helpers, adding reusable safe rename or cleanup operations only where needed.
- `tools/install.py` and `tools/uninstall.py` own command-specific planning, preview, confirmation, application order, and terminal output.

Remove `skill_links.py` after all required current-checkout legacy-link behavior has moved and no caller depends on the old structural-recognition model.

### Source skill validation

Discover direct directories under the toolkit's `skills/` directory that contain a regular `SKILL.md`. Before confirmation, inspect each complete source tree without following symlinks:

1. Validate the skill name.
2. Walk entries in deterministic relative-path order.
3. Reject a symlink at any depth, including a symlinked skill root or `SKILL.md`.
4. Reject sockets, devices, FIFOs, and other non-regular entry types.
5. Record directories and hash regular-file bytes.
6. Revalidate the source snapshot before copying and verify the staged copy against the planned snapshot before installation.

A source validation failure aborts the complete install before workspace mutation.

### Installed skill classifications

Classify every relevant target into one state:

| State | Meaning | Install behavior | Uninstall behavior |
| --- | --- | --- | --- |
| Absent | No target exists and no manifest entry conflicts. | Create copied skill. | No file action. |
| Exact managed copy | Valid manifest entry and exact matching inventory. | Replace when source differs; otherwise no-op. | Remove copy. |
| Modified managed copy | Manifest entry exists but target inventory or type differs. | Preserve and abort install with a conflict. | Preserve skill and manifest entry with a warning. |
| Unmanaged conflict | Target exists without valid manifest ownership. | Preserve and abort install with a conflict. | Preserve. |
| Current-checkout legacy link | Direct link proven to target the running checkout's matching skill directory. | Replace with a copied skill after preview. | Remove after preview. |
| Foreign or unproven link | Link ownership cannot be proven without generic structural inference. | Preserve and abort install with a conflict. | Preserve, warning when dangling. |

Manifest entries whose targets are absent are stale metadata. Installation may recreate the skill from the current source after reporting the stale state. Uninstallation removes the stale manifest entry without attempting a file deletion.

When a manifest records a skill that no longer exists in the source toolkit, installation treats it as retired. An exact managed copy is removed and its manifest entry is deleted as part of the previewed transaction. A modified copy is preserved and causes the install to stop with a conflict rather than deleting local changes.

### Install planning and application

Installation planning will:

1. Validate `AGENTS.md`, `.agents/`, and `.agents/skills/` boundaries using the existing symlink protections.
2. Load and fully validate the manifest, treating absence as an empty manifest.
3. Snapshot all source skills and relevant workspace targets.
4. Calculate the proposed `AGENTS.md`, copied-skill, legacy-migration, and manifest changes.
5. Reconcile manifest entries with current source skills, planning safe retirement of exact copies whose sources were removed.
6. Abort the complete plan if any modified managed copy, unmanaged target, foreign link, invalid manifest, or invalid source tree would be overwritten or removed.
7. Preview every skill creation, update, retirement, no-op omission, legacy-link replacement, manifest change, and `AGENTS.md` change.

After confirmation, revalidate every planned source and workspace precondition before mutation. Apply the plan as a recoverable transaction:

1. Build and verify all new skill copies in temporary directories on the workspace filesystem.
2. Move existing exact managed copies or provable legacy links to temporary backups.
3. Rename verified staged copies into their final targets.
4. Atomically write the proposed `AGENTS.md` content when it changed.
5. Atomically write the manifest last as the committed ownership record.
6. Remove backups only after all principal operations succeed.

On a recoverable failure, restore the prior `AGENTS.md`, manifest bytes, managed directories, and legacy links from recorded state. Remove staging and backup artifacts. Report any rollback failure explicitly.

### Uninstall planning and application

Uninstallation planning will:

1. Validate managed markers and protected workspace boundaries before planning any mutation.
2. Load and validate the manifest. An invalid manifest prevents copied-skill removal and must not be treated as empty ownership data.
3. Snapshot each recorded target and compare it with the manifest.
4. Plan removal only for exact managed copies and provable current-checkout legacy links.
5. Preserve modified copies, unmanaged entries, and foreign or unproven links.
6. Calculate the remaining manifest after exact removals and stale-entry cleanup.
7. Preview the managed-block change, each skill removal, every preserved conflict, and the manifest update or removal.

After confirmation, revalidate all planned paths and content before the first mutation and again immediately before each destructive action. Rename removable skill directories to temporary backups instead of deleting them immediately, apply the `AGENTS.md` and manifest changes atomically, then delete backups after principal success. Restore backups and prior files when a later principal operation fails.

When modified copies remain, retain their manifest entries as ownership evidence and finish with warnings that name every preserved skill. A repeated uninstall remains safe and reports the same unresolved artifacts until the user restores the recorded content or resolves them manually.

### Legacy symlink migration

Remove the generic cross-checkout recognition rule based on the presence of `AGENTS.md`, `SKILL.md`, and an installer path. That structure is not durable proof of ownership.

Recognize a legacy link only when its lexical or resolved destination is the matching direct child of the `skills/` directory in the checkout running the command. This includes a dangling link whose lexical destination is still inside the current checkout. Record the raw link target so rollback can restore it exactly.

The installer may replace a proven current-checkout legacy link with a copied directory. The uninstaller may remove it. Links into another checkout, including structurally similar agent-toolkit checkouts, remain unproven and are preserved.

### Command outcomes

Preserve current command options and interactive behavior. Adjust terminal messages to distinguish complete success, no-op, and safe partial preservation:

- Installation conflicts exit nonzero before mutation and identify each target requiring manual resolution.
- Successful uninstall reports removed artifacts and any modified copies preserved with warnings.
- `Already up to date` requires matching `AGENTS.md`, source snapshots, installed copies, and manifest bytes.
- `Already uninstalled` requires no managed block, no removable legacy links, and no manifest entries.
- `--dry-run` performs no staging, copying, backup creation, or other filesystem mutation.

## Implementation steps

1. Define immutable manifest, inventory, classification, install-action, and uninstall-action models.
2. Implement strict manifest parsing, normalized-path validation, deterministic serialization, and SHA-256 inventory comparison in `tools/common/skill_manifest.py`.
3. Implement deterministic source and target inspection without following symlinks in `tools/common/skill_files.py`.
4. Add staging, verified recursive copying, backup renames, restoration, and cleanup helpers with explicit effect boundaries.
5. Replace installer link planning with copied-skill and manifest planning.
6. Implement installer precondition revalidation, staged application, manifest commit, and rollback.
7. Replace uninstaller structural link discovery with manifest-backed copied-skill planning and exact current-checkout legacy-link handling.
8. Implement uninstaller preservation warnings, stale-manifest cleanup, backup-based removal, manifest updates, and rollback.
9. Remove obsolete cross-checkout structural recognition and `skill_links.py` after migration coverage passes.
10. Update self-installation ignore rules for `.agents/agent-toolkit-manifest.json`.
11. Update installer and uninstaller documentation to describe copied snapshots, rerunning installation for updates, manifest ownership, modified-copy preservation, and legacy-link limitations.
12. Add and update unit and command-level tests described below.
13. Run the complete test suite and manually exercise install, update, uninstall, self-install, self-uninstall, dry-run, decline, rollback, and legacy migration flows.
14. When every acceptance criterion passes, mark this plan `Implemented` and update `docs/plans/README.md` in the same change.

## Test plan

### Manifest and inventory tests

- Parse and serialize a valid version-1 manifest deterministically.
- Reject unknown formats and versions, invalid skill names, unsafe targets, absolute paths, traversal, duplicate paths, unsorted or contradictory entries, malformed hashes, and unexpected value types.
- Record regular files, nested directories, and empty directories in stable order.
- Produce stable SHA-256 digests for identical bytes.
- Detect added, removed, modified, replaced, and type-changed entries.
- Reject source and target symlinks at the root or any nested path.
- Reject special filesystem entries.

### Installer tests

- Install all toolkit skills as real directories and regular files.
- Write a valid manifest matching the installed copies.
- Preserve existing project `AGENTS.md` content.
- Repeat installation with no changes and report already up to date.
- Update an exact managed copy after source content changes.
- Add a newly introduced source skill and update the manifest.
- Recreate a missing managed copy from a stale manifest entry.
- Remove an exact managed copy when its source skill was removed and update the manifest.
- Preserve a modified managed copy whose source skill was removed and abort with a conflict.
- Refuse to overwrite a modified managed copy.
- Refuse an unmanaged regular directory, file, or foreign symlink with a colliding skill name.
- Reject invalid or unsupported manifest content before mutation.
- Reject a symlinked or non-regular manifest path before mutation.
- Reject source trees containing symlinks or special files.
- Replace a proven current-checkout legacy link with a copied skill.
- Preserve and reject an unproven cross-checkout or dangling foreign link.
- Preserve source and workspace state on dry-run, decline, validation failure, copy failure, manifest-write failure, and `AGENTS.md` write failure.
- Run successfully by absolute script path from a foreign working directory.

### Uninstaller tests

- Remove exact manifest-backed copied skills and the managed block.
- Remove the manifest when no entries remain.
- Remove `.agents/skills/` and `.agents/` only when empty.
- Preserve modified managed copies and retain their manifest entries with warnings.
- Preserve copied skills with added, removed, replaced, or type-changed content.
- Clean a stale manifest entry whose target is absent without deleting another path.
- Preserve unmanaged directories, regular files, and foreign links.
- Reject invalid manifest content without removing copied skills or `AGENTS.md` content.
- Remove a proven current-checkout legacy link and restore its exact raw target on rollback.
- Preserve links into another checkout even when it resembles agent-toolkit.
- Preserve the source repository's authoritative `AGENTS.md` during self-uninstallation.
- Remain idempotent after complete uninstall and report unresolved modified copies consistently.
- Preserve state on dry-run, decline, stale-plan detection, removal failure, manifest-write failure, and `AGENTS.md` failure.

### Concurrency and rollback tests

- Replace or modify a planned copied skill after preview and verify application aborts without deleting the new state.
- Change the manifest after preview and verify application aborts before mutation.
- Change a source skill after preview and verify installation aborts before copying stale content.
- Change `AGENTS.md` after preview and verify the new content is preserved.
- Replace `.agents`, `.agents/skills`, a skill target, or the manifest with a symlink after preview and verify the command aborts safely.
- Fail after one or more backup renames and verify all original directories, links, manifest bytes, and `AGENTS.md` content are restored.
- Simulate a rollback collision and report the unrecovered path without overwriting the replacement artifact.

### Regression tests

- Preserve marker validation, whitespace handling, self-installation, self-uninstallation, interactive confirmation, and command exit behavior.
- Confirm the implementation uses only the Python standard library and performs no Git or network operations.
- Confirm repository self-installation does not create tracked changes for copied skills or its manifest.
- Run the complete suite on every supported Python version.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| A malformed manifest redirects removal outside `.agents/skills/`. | Strictly validate normalized relative targets and require the exact `skills/<skill-name>` shape before constructing removal actions. |
| A copied skill is edited locally and then overwritten or deleted. | Compare the complete observed inventory with the manifest and preserve any non-exact target. |
| A source tree contains a link or special file that escapes normal copying semantics. | Inspect without following links and reject every non-regular file or directory before confirmation and again before copying. |
| Workspace state changes after preview. | Snapshot and revalidate the manifest, targets, sources, and `AGENTS.md` before mutation and immediately before destructive actions. |
| A multi-artifact update fails partway through. | Stage new copies, rename old artifacts to backups, commit the manifest last, and restore recorded state on recoverable failure. |
| A similarly structured foreign checkout is mistaken for agent-toolkit. | Remove structural cross-checkout recognition and recognize legacy links only when they target the running checkout directly. |
| A source checkout moves or disappears after installation. | Store no source path in the manifest; copied skill contents and ownership remain self-contained. |
| Copied skills become stale relative to the toolkit. | Document snapshot behavior and make repeated installation detect and update exact managed copies. |
| Installation creates unwanted Git changes in consuming workspaces. | Do not modify consumer ignore rules automatically; document that each repository chooses whether to commit or ignore installed artifacts. |
| Temporary staging or backups remain after process termination. | Use recognizable workspace-local names, clean them on handled failures, and detect conflicting remnants on the next run rather than deleting unproven paths. |

## Acceptance criteria

- A fresh install creates regular skill directories and files with no symlinks under `.agents/skills/`.
- The manifest is valid, deterministic, versioned, and exactly describes every installed skill copy.
- Installed skills continue working after the source toolkit checkout is moved or deleted.
- Reinstallation updates only exact manifest-owned copies and never overwrites modified or unmanaged targets.
- Reinstallation removes exact managed copies retired from the source toolkit and preserves modified retired copies.
- Uninstallation removes only exact manifest-owned copies and proven current-checkout legacy links.
- Modified copies, foreign files, project-owned skills, and unproven links are preserved with actionable diagnostics.
- Generic repository structure is never used as proof of legacy-link ownership.
- Invalid manifests and unsafe paths cause a nonzero exit before mutation.
- Dry-run and interactive decline produce no filesystem changes.
- Stale plans abort safely, and recoverable mid-operation failures restore prior workspace state.
- Managed `AGENTS.md` behavior, self-installation, self-uninstallation, and empty-directory cleanup remain correct.
- The root README accurately summarizes copied-skill installation and uninstallation without duplicating implementation details from this plan.
- The complete test suite passes on every supported Python version using only the standard library.

## Open questions

- None.
