# agent-toolkit

A centralized toolkit for distributing shared coding-agent rules, safety policies, and reusable workflow skills across Codex and Antigravity workspaces.

## Purpose

- Maintain shared engineering conventions, safety boundaries, and agent instructions in one version-controlled location.
- Provide reusable skills for code review, branch integration, and pragmatic functional programming.
- Install shared instructions without replacing project-specific rules.
- Link skills into workspaces so this repository remains their authoritative source.

## Repository contents

- [`AGENTS.md`](./AGENTS.md) — authoritative shared development conventions, safety boundaries, and documentation guidance:
  - [Pragmatic Functional Programming Rules](./AGENTS.md#pragmatic-functional-programming-rules)
  - [TypeScript Rules](./AGENTS.md#typescript-rules)
  - [Git Safety](./AGENTS.md#git-safety)
  - [Jira Safety](./AGENTS.md#jira-safety)
  - [MongoDB Safety](./AGENTS.md#mongodb-safety)
  - [SCSS Rules](./AGENTS.md#scss-rules)
  - [JSX Rules](./AGENTS.md#jsx-rules)
  - [README Guidance](./AGENTS.md#readme-guidance)
- [`skills/`](./skills/README.md) — reusable agent workflows:
  - [`merge-master`](./skills/merge-master/SKILL.md)
  - [`pragmatic-functional-programming`](./skills/pragmatic-functional-programming/SKILL.md)
  - [`review`](./skills/review/SKILL.md)
  - [`review-diff`](./skills/review-diff/SKILL.md)
- [`tools/install.py`](./tools/install.py) — updates the managed section of a workspace’s `AGENTS.md` and links skills into `.agents/skills/` while preserving project-specific instructions.
- [`tools/uninstall.py`](./tools/uninstall.py) — removes managed instructions and skill links from a workspace.
- [`tests/`](./tests/) — test suite verifying installer and uninstaller updates, repeatability, conflict handling, and preservation of existing workspace content.

## Install shared rules

Run the interactive installer from any directory:

```bash
python3 /path/to/agent-toolkit/tools/install.py --workspace /path/to/workspace
```

When the toolkit is inside the workspace, `--workspace` can be omitted; the installer defaults to the toolkit's parent directory. It previews the root `AGENTS.md` change and the skill links, then asks before applying either. Project-specific instructions outside the `agent-toolkit` markers are preserved. Run the installer again after changing shared rules; it replaces only its marked section. A repeated install with no source changes does nothing.

To use the toolkit while developing it, install it into its own repository:

```bash
python3 tools/install.py --workspace .
```

Self-installation leaves the authoritative `AGENTS.md` unchanged and creates only the skill links under `.agents/skills/`. Those generated links are ignored by Git in this repository.

Each skill in `skills/` gets a relative directory symlink at `<workspace>/.agents/skills/<name>`. Codex and Antigravity both discover workspace skills there. Existing local skills are never replaced; a name conflict stops installation so it can be resolved first. The links keep the toolkit as the single source for skill updates.

## Uninstall shared rules

To remove agent-toolkit-managed rules and skill links from a workspace:

```bash
python3 /path/to/agent-toolkit/tools/uninstall.py --workspace /path/to/workspace
```

The uninstaller removes the managed block from the workspace `AGENTS.md` while preserving project-owned rules. If the managed block was the only content, `AGENTS.md` is removed. It removes skill symlinks owned by this toolkit checkout as well as links installed from another existing `agent-toolkit` checkout (legacy or current layout). Unproven dangling links whose source checkouts are missing or unrecognizable are preserved with a warning. Clean up removes empty `.agents/skills` and `.agents` directories. Project-owned skills and foreign symlinks are preserved. Self-uninstallation preserves the repository's authoritative `AGENTS.md`.

Both `tools/install.py` and `tools/uninstall.py` support `--dry-run` to preview changes and `--yes` for unattended execution; see `--help` on each tool for option details.

## Testing

Run the test suite:

```bash
python3 -m unittest discover tests
```

## Notes

- This repository contains agent instructions, reusable skills, and installation tooling rather than application code.
- Only the section between the `agent-toolkit` markers in a workspace’s `AGENTS.md` is managed by `tools/install.py`.
