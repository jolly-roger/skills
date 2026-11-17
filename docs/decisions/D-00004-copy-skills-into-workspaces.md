# D-00004: Copy Skills into Workspaces

## Status

Accepted

## Date

2026-11-04

## Context

The installer currently exposes toolkit skills to a workspace through directory symlinks under `.agents/skills/`. This keeps one live source for skill content, but it also couples every installed workspace to the location and lifetime of the toolkit checkout. Moving or deleting that checkout leaves dangling links, and uninstalling links created by another checkout requires ownership heuristics that can mistake a similarly structured repository for agent-toolkit.

Installed workspaces should remain usable when the source checkout moves or disappears. The installer and uninstaller also need durable ownership evidence that does not depend on resolving a live source path.

## Decision

Install skills as copied directories rather than symlinks:

- Copy each valid `skills/<skill-name>/` tree into `<workspace>/.agents/skills/<skill-name>/`.
- Create regular directories and files only. Refuse source skill trees containing symlinks rather than reproducing or following them.
- Record every installed skill in a versioned agent-toolkit manifest under `.agents/`. The manifest records the relative target path and a deterministic inventory and digest of the copied files.
- Treat a copied skill as agent-toolkit-owned only when the manifest is valid and the target matches its recorded file types, inventory, and digests.
- Refuse to overwrite an existing skill path that is not proven to be owned by the current manifest.
- Update a previously copied skill only after verifying that its installed content still matches the manifest. If it was changed locally, preserve it and report the conflict instead of overwriting it.
- Build installation and uninstallation plans before mutation, preview every planned change, and revalidate relevant paths immediately before applying it.

The uninstaller will:

- Remove copied skill files and directories only when their ownership and current content are proven by the manifest.
- Preserve an entire copied skill and report a warning when its files were added, removed, replaced, or modified after installation.
- Preserve project-owned skills, untracked paths, foreign files, and invalid or unproven targets.
- Remove the manifest when it no longer records any installed skills.
- Remove `.agents/skills/` and `.agents/` only when they are empty after owned artifacts are removed.
- Continue to remove only the valid agent-toolkit-managed block from a workspace `AGENTS.md`, preserving project-authored content and the authoritative `AGENTS.md` during self-uninstallation.
- Retain preview, confirmation, dry-run, stale-plan detection, rollback, and idempotent behavior.

Existing symlink installations are legacy installations. Migration may replace or remove a legacy link only when ownership can be proven without relying on generic repository structure. Unproven and foreign symlinks must be preserved.

## Alternatives considered

### Continue using symlinks

Symlinks make source changes immediately available to installed workspaces and avoid duplicated files. They were not selected because workspaces depend on the original checkout path, links become invalid when that checkout moves or disappears, and cross-checkout ownership is ambiguous.

### Copy skills without ownership metadata

This is simpler during installation, but the uninstaller cannot safely distinguish copied toolkit content from a project-owned skill with the same name.

### Remove copied skills by directory name

Matching names does not establish ownership and could delete project-authored skills or files.

### Package and install skills through a package manager

A package manager could provide versions and manifests, but it adds distribution and environment requirements that are unnecessary for the repository's file-based workspace integration.

## Consequences

### Positive

- Installed skills remain available if the toolkit checkout moves or is deleted.
- Workspace behavior is based on a stable installed snapshot rather than mutable external files.
- Manifest-backed ownership removes the need to infer ownership from another repository's structure.
- The installer and uninstaller can protect locally modified and project-owned skill content.

### Negative

- Skill files are duplicated in every installed workspace.
- Toolkit skill changes are not available to a workspace until the installer runs again.
- Installation, updates, and uninstallation require manifest maintenance and content-digest validation.
- Locally modified installed copies require manual resolution before they can be updated or removed automatically.
- Legacy symlink installations require a conservative migration path.

## Related documents

- [D-00001: Project Tooling Layout](./D-00001-project-tooling-layout.md)
- [D-00003: Uninstaller Ownership and Safety Model](./D-00003-uninstaller-safety-model.md)
- [P-00001: Agent Toolkit Uninstaller](../plans/P-00001-uninstaller.md)
- [P-00002: Cross-Installation Uninstall Compatibility](../plans/P-00002-cross-installation-uninstall.md)
- [P-00003: Copied Skill Installation](../plans/P-00003-copied-skill-installation.md)

## Supersedes

- [D-00003: Uninstaller Ownership and Safety Model](./D-00003-uninstaller-safety-model.md)

## Superseded by

None
