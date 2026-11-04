# D-00005: Repository and Installation Identity

## Status

Accepted

## Date

2026-11-04

## Context

The repository has been renamed from `jolly-roger/agent-toolkit` to `jolly-roger/skills`. The old name is also embedded in workspace-managed markers, manifest names and formats, command output, documentation, and implementation terminology.

Keeping `agent-toolkit` as the permanent installation namespace would leave the public and internal identities inconsistent. Using the unqualified name `skills` internally would be ambiguous because many repositories and agent systems use that generic term. Existing workspaces may still contain artifacts written with the old identity, so changing identifiers without migration support could strand managed rules or copied skills.

## Decision

Adopt the following canonical identity:

| Purpose | Canonical value |
| --- | --- |
| GitHub repository | `jolly-roger/skills` |
| Display name | `Jolly Roger's Skills` |
| Internal namespace | `jolly-roger.skills` |
| Filesystem and marker slug | `jolly-roger-skills` |
| Managed block begin marker | `<!-- jolly-roger-skills:begin -->` |
| Managed block end marker | `<!-- jolly-roger-skills:end -->` |
| Manifest filename | `.agents/jolly-roger-skills-manifest.json` |
| Manifest format | `jolly-roger.skills` |

Adopt the following presentation values without changing the technical identity:

| Purpose | Value |
| --- | --- |
| README title | `🏴‍☠️ Jolly Roger's Skills` |
| Tagline | `Code by the rules. Sail with the agents.` |
| GitHub description | `A pirate's toolkit for better coding agents` |

All newly written workspace artifacts, command output, active documentation, and implementation terminology will use the canonical identity. Repository-root concepts in code should use names such as `repository_root` or `skills_root` rather than `toolkit_root` where they refer specifically to this repository.

Treat the previous identity as legacy migration input only:

| Purpose | Legacy value |
| --- | --- |
| Repository name | `agent-toolkit` |
| Managed block markers | `<!-- agent-toolkit:begin -->` and `<!-- agent-toolkit:end -->` |
| Manifest filename | `.agents/agent-toolkit-manifest.json` |
| Manifest format | `agent-toolkit.skills` |

The installer will recognize a valid legacy installation and migrate it to the canonical identity as part of a previewed, recoverable transaction. The uninstaller will recognize valid canonical or legacy artifacts so users can remove an installation without first migrating it.

Legacy compatibility must be isolated from canonical behavior:

- Never write new legacy markers, manifests, formats, or user-facing identity strings.
- Validate legacy artifacts with the same boundary and ownership protections as canonical artifacts.
- Reject malformed artifacts and ambiguous states containing both canonical and legacy forms of the same managed artifact.
- Do not infer ownership from a repository name, checkout directory name, Git remote, or generic repository structure.
- Preserve project-authored content and unproven artifacts.
- Remove legacy compatibility only through a later explicit decision after migration is no longer required.

Historical implemented decisions and plans remain unchanged where they accurately describe the identity used by the implementation at that time. Current documentation should use the canonical identity and link to historical records when details are needed.

## Alternatives considered

### Keep `agent-toolkit` as the internal namespace

This avoids workspace migration but leaves permanent disagreement between the repository name and installed artifacts. It was rejected because the old name is no longer the intended project identity.

### Use `skills` as the internal namespace

This matches the repository name but is too generic for markers and manifests shared with other agent tooling. The owner-qualified namespace reduces collision risk.

### Change identifiers without legacy compatibility

This is simpler to implement but can leave existing managed blocks and manifests undiscoverable. It would require manual cleanup and could create duplicate managed sections.

### Rewrite historical decisions and plans

This would make old documents appear consistent with the new name but would erase the terminology and constraints under which earlier behavior was designed and implemented.

## Consequences

### Positive

- Public branding, workspace artifacts, and active implementation terminology share one identity.
- The display name and tagline give the repository a recognizable presentation while technical identifiers remain stable and unambiguous.
- The owner-qualified namespace is distinct from other repositories named `skills`.
- Existing workspaces can migrate or uninstall without manual artifact editing.
- Canonical writes no longer perpetuate the retired name.
- Historical records preserve an accurate account of previous behavior.

### Negative

- Installer and uninstaller logic must temporarily understand two identities.
- Migration adds marker, manifest, conflict, preview, rollback, and regression cases.
- Existing workspace diffs will include marker and manifest renames even when skill content is unchanged.
- Legacy compatibility cannot be removed safely without a later explicit decision.

## Related documents

- [D-00001: Project Tooling Layout](./D-00001-project-tooling-layout.md)
- [D-00004: Copy Skills into Workspaces](./D-00004-copy-skills-into-workspaces.md)
- [P-00003: Copied Skill Installation](../plans/P-00003-copied-skill-installation.md)
- [P-00004: Repository Identity Migration](../plans/P-00004-repository-identity-migration.md)

## Supersedes

None. This decision replaces identity values referenced by earlier decisions without superseding their behavioral decisions.

## Superseded by

None
