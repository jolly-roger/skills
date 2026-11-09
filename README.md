# 🏴‍☠️ Jolly Roger's Skills

*Code by the rules. Sail with the agents.*

A centralized repository for distributing shared coding-agent rules, safety policies, and reusable workflow skills across Codex and Antigravity workspaces.

## Purpose

- Maintain shared engineering conventions, safety boundaries, and agent instructions in one version-controlled location.
- Provide reusable skills for code review, branch integration, pragmatic functional programming, and TypeScript.
- Install shared instructions without replacing project-specific rules.
- Copy self-contained skills into workspaces with manifest-backed ownership and local modification safety.

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
  - [`pragmatic-functional-programming`](./skills/pragmatic-functional-programming/SKILL.md)
  - [`typescript`](./skills/typescript/SKILL.md) — requires `pragmatic-functional-programming`
  - [`merge-master`](./skills/merge-master/SKILL.md)
  - [`review`](./skills/review/SKILL.md)
  - [`review-diff`](./skills/review-diff/SKILL.md)
- [`tools/install.py`](./tools/install.py) — updates the managed section of a workspace’s `AGENTS.md` and copies skills into `.agents/skills/` with manifest-backed tracking while preserving project-specific instructions.
- [`tools/uninstall.py`](./tools/uninstall.py) — removes managed instructions and exact manifest-verified skill copies from a workspace.
- [`tests/`](./tests/) — test suite verifying installer and uninstaller updates, repeatability, conflict handling, and preservation of existing workspace content.

## Install shared rules

Run the interactive installer from any directory:

```bash
python3 /path/to/skills/tools/install.py --workspace /path/to/workspace
```

When the repository is inside the workspace, `--workspace` can be omitted; the installer defaults to the repository's parent directory. It previews the root `AGENTS.md` change and skill installations, then asks before applying either. Project-specific instructions outside the managed markers are preserved. Run the installer again after changing shared rules or skills; it updates only managed content. A repeated install with no source changes does nothing.

To use the repository while developing it, install it into its own directory:

```bash
python3 tools/install.py --workspace .
```

Self-installation leaves the authoritative `AGENTS.md` unchanged and copies skills under `.agents/skills/` along with the ownership manifest. Those generated artifacts are ignored by Git in this repository.

Each skill in `skills/` is copied as a self-contained directory at `<workspace>/.agents/skills/<name>`. Codex and Antigravity both discover workspace skills there. Existing unmanaged or locally modified skills are never overwritten; a conflict stops installation so it can be resolved first.

## Uninstall shared rules

To remove managed rules and copied skills from a workspace:

```bash
python3 /path/to/skills/tools/uninstall.py --workspace /path/to/workspace
```

The uninstaller removes the managed block from the workspace `AGENTS.md` while preserving project-owned rules. If the managed block was the only content, `AGENTS.md` is removed. It removes exact manifest-verified skill copies and provable legacy links from the current checkout. Locally modified skill copies, project-owned skills, and unproven symlinks are preserved with warnings. Clean up removes empty `.agents/skills` and `.agents` directories. Self-uninstallation preserves the repository's authoritative `AGENTS.md`.

Both `tools/install.py` and `tools/uninstall.py` support `--dry-run` to preview changes and `--yes` for unattended execution; see `--help` on each tool for option details.

## Requirements

- Python 3.13 or 3.14 (syntax compatible with Python 3.10+ standard library). Tooling relies strictly on the Python standard library with no third-party dependencies.

## Testing

Run the test suite:

```bash
python3 -m unittest discover tests
```

## Notes

- This repository contains agent instructions, reusable skills, and installation tooling rather than application code.
- Only the section between the managed markers in a workspace’s `AGENTS.md` is managed by `tools/install.py`.
