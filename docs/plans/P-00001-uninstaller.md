# P-00001: Agent Toolkit Uninstaller

## Status

Implemented

## Date

2026-10-27

## Objective

Add a safe, repeatable command that removes agent-toolkit-managed rules and skill links from a workspace without deleting project-owned content.

The command should mirror the existing installer experience:

```bash
python3 /path/to/agent-toolkit/tools/uninstall.py --workspace /path/to/workspace
```

## Scope

The implementation will:

- Create a `tools/` directory for the project's executable utilities and their shared implementation code.
- Move the existing installer to `tools/install.py` without changing its behavior.
- Add a standalone `tools/uninstall.py` command.
- Store reusable installer and uninstaller behavior under `tools/common/` so neither command imports the other.
- Remove the managed block delimited by `<!-- agent-toolkit:begin -->` and `<!-- agent-toolkit:end -->` from the workspace root `AGENTS.md`.
- Preserve project-owned content outside the managed block.
- Remove only skill symlinks owned by the current agent-toolkit checkout.
- Remove generated container directories only when they are empty after uninstalling.
- Support interactive confirmation, unattended execution, and dry-run previews.
- Add automated tests for content preservation, ownership checks, idempotency, failures, and rollback.
- Add concise uninstall usage to `README.md`.

## Non-goals

- Removing the agent-toolkit source checkout.
- Removing regular files or directories from `.agents/skills`.
- Removing symlinks that point outside the current toolkit's `skills` directory.
- Restoring whitespace that the existing installer normalized before this feature existed.
- Introducing an installation manifest or third-party dependency.
- Refactoring unrelated installer behavior.
- Turning agent-toolkit into an installable Python package or standalone application.
- Keeping executable wrappers at the repository root; documentation will point directly to the commands under `tools/`.

## User interface

`tools/uninstall.py` will accept the same workspace and execution controls as `tools/install.py`:

| Option | Behavior |
| --- | --- |
| `--workspace PATH` | Select the workspace root. Defaults to the toolkit parent using the installer's current rules. |
| `--dry-run` | Print the complete proposed change without writing. |
| `--yes` | Apply without prompting. |

With neither `--yes` nor `--dry-run`, the command will prompt for the workspace when omitted, show the proposed changes, and ask for confirmation. EOF or any response other than `y` or `yes` will decline the operation.

Expected terminal outcomes:

- `Uninstalled agent-toolkit from <workspace>` after a successful change.
- `Already uninstalled: <workspace>` when no managed artifacts are found.
- `No changes made.` when interactive confirmation is declined.
- A nonzero exit with an actionable error when validation or an operation fails.

## Safety invariants

1. Complete validation and planning before mutating the workspace.
2. Never follow a symlinked `.agents` or `.agents/skills` directory.
3. Never replace or unlink a symlinked workspace `AGENTS.md`.
4. Reject incomplete, reversed, or duplicate agent-toolkit markers.
5. Remove a skill entry only when it is a symlink resolving to a direct child of this checkout's `skills` directory.
6. Preserve regular files, directories, and foreign symlinks, including entries whose names match toolkit skills.
7. Preserve the source repository's authoritative `AGENTS.md` during self-uninstallation.
8. Do not leave a partially applied uninstall when a recoverable filesystem operation fails.

## Design

### Project code layout

Store all executable scripts and reusable implementation code under `tools/`:

```text
tools/
├── install.py
├── uninstall.py
└── common/
    ├── __init__.py
    ├── agents_file.py
    ├── filesystem.py
    └── skill_links.py

tests/
├── test_install.py
├── test_uninstall.py
├── test_agents_file.py
└── test_skill_links.py
```

`tools/` is repository tooling rather than application source. Do not introduce `src/`, application packaging metadata, or a separately installed CLI.

Responsibilities:

- `tools/install.py` parses installer arguments, obtains confirmation, and orchestrates installation effects.
- `tools/uninstall.py` parses uninstaller arguments, obtains confirmation, and orchestrates uninstallation effects.
- `tools/common/agents_file.py` owns marker constants, marker validation, managed-block creation, insertion, removal, and diff calculation.
- `tools/common/filesystem.py` owns atomic text replacement and narrowly scoped filesystem helpers.
- `tools/common/skill_links.py` owns skill discovery, link ownership checks, link creation, removal, and restoration.

Both commands import from `common`; they must not import from each other. Keep command-specific output and workflow decisions in their respective command modules.

Each command derives the toolkit root from its own file location and passes that path explicitly into shared operations that need it. The default workspace remains the toolkit root's parent, preserving the current installer behavior after the move. Shared modules must not infer the active toolkit from process working directory or hidden mutable state.

The existing root `install.py` and `test_install.py` will move to the new structure. Update imports and documentation as part of the same change while preserving all existing installer behavior and test coverage.

### Separate calculations from filesystem actions

Add a pure calculation to `tools/common/agents_file.py` for managed-block removal:

```python
def removed_content(existing: str) -> str:
    """Return AGENTS.md content without the validated managed block."""
```

The function will:

1. Count and validate the begin and end markers using the installer's current rules.
2. Return the original content unchanged when neither marker exists.
3. Remove exactly one complete managed block.
4. Normalize only newline separation at the removal boundary:
   - Join preserved content on both sides with one blank line.
   - Keep a single terminal newline when only preceding content remains.
   - Return an empty string when no project-owned content remains.

Filesystem inspection will produce an immutable uninstall plan containing:

- The workspace and `AGENTS.md` paths.
- Original and proposed `AGENTS.md` content.
- Whether `AGENTS.md` should be rewritten, removed, or left unchanged.
- The exact skill symlinks to unlink.
- Each link's raw target for rollback.

A small frozen dataclass is appropriate if it makes the states clearer; otherwise, use simple immutable tuples and local values. Avoid an abstraction that merely forwards calls.

### Identify owned skill links

Inspect direct entries under `<workspace>/.agents/skills` only after validating that `.agents` and `.agents/skills` are real directories rather than symlinks.

For each symlink:

1. Read and retain its raw target with `os.readlink` or `Path.readlink`.
2. Resolve the target without requiring the destination to exist.
3. Verify that the resolved destination's parent is exactly `<toolkit-root>/skills`.
4. Schedule only matching links for removal.

Checking the destination parent rather than enumerating current source skills also discovers dangling links for skills removed from the toolkit after installation. It deliberately does not remove nested links or links into other toolkits.

### Handle `AGENTS.md`

For a normal workspace:

- Rewrite the file atomically when project-owned content remains.
- Remove the file when the managed block was its only meaningful content.
- Leave it untouched when no managed block exists.

For self-uninstallation, where the resolved workspace equals the toolkit root, leave the root `AGENTS.md` unchanged because it is the source document rather than an installed copy. Skill links remain eligible for removal.

The legacy installer does not record whether an empty `AGENTS.md` existed before installation. The defined compatibility behavior is therefore to remove the file when only the managed block remains.

### Preview and confirmation

Before confirmation:

- Print a unified diff when `AGENTS.md` will change.
- Clearly state when `AGENTS.md` will be deleted.
- Print one `Remove skill link:` line per owned symlink, including its raw target.
- Do not list preserved foreign entries as removals.

`--dry-run` exits successfully after the preview. Interactive decline exits successfully without mutation.

### Apply and rollback

Apply the plan in an order that keeps rollback practical:

1. Unlink planned skill links, recording which removals succeeded.
2. Atomically rewrite or unlink `AGENTS.md`.
3. Remove `.agents/skills` and then `.agents` only when each is empty.

If link removal or the `AGENTS.md` operation fails:

- Recreate successfully removed links from their recorded raw targets.
- Leave non-owned entries untouched.
- Report the original failure.
- If rollback itself fails, report both the original and rollback failures so the result cannot appear successful.

Directory cleanup occurs only after the principal changes succeed. A non-empty directory is an expected condition and remains in place. Other cleanup errors should be reported without disguising the completed principal uninstall.

## Implementation steps

1. Create `tools/common/` and extract shared marker, content, filesystem, and skill-link behavior from the existing installer.
2. Move `install.py` to `tools/install.py`, adapt it to the shared modules, and confirm its observable behavior remains unchanged.
3. Move installer tests under `tests/` and update their imports and command paths.
4. Add `tools/uninstall.py` with argument parsing aligned to `tools/install.py`.
5. Implement and unit-test marker validation and `removed_content` in `tools/common/agents_file.py`.
6. Implement workspace validation and owned-link discovery using the shared filesystem and skill-link modules.
7. Represent the complete uninstall plan before any mutation.
8. Implement preview, confirmation, application, and rollback.
9. Add best-effort empty-directory cleanup with explicit error handling.
10. Add end-to-end uninstaller tests under `tests/`.
11. Update `README.md` with the new installer path and a concise uninstall command and behavior summary, referring users to each command's `--help` output for option details.
12. Run the complete test suite and manually inspect dry-run output for both normal and self-installed workspaces.

## Test plan

### Pure content tests

- Remove the only managed block and return empty content.
- Preserve content before the managed block.
- Preserve content after the managed block.
- Preserve content on both sides with one blank line between sections.
- Return unchanged content when markers are absent.
- Reject a lone begin marker.
- Reject a lone end marker.
- Reject reversed markers.
- Reject duplicate marker pairs.

### Command integration tests

- Install into a workspace and uninstall it, preserving canonical project content.
- Remove an installer-created `AGENTS.md` when it contains only managed content.
- Preserve the toolkit's authoritative `AGENTS.md` during self-uninstallation.
- Remove all owned skill symlinks.
- Remove a dangling owned symlink whose destination remains lexically inside the toolkit skills directory.
- Preserve a regular skill directory with a colliding name.
- Preserve a symlink to another location with a colliding name.
- Preserve unrelated entries under `.agents` and leave non-empty parent directories in place.
- Remove `.agents/skills` and `.agents` when they become empty.
- Make no changes in dry-run mode.
- Make no changes after interactive decline.
- Report `Already uninstalled` on a repeated run.
- Reject a nonexistent workspace.
- Reject symlinked `AGENTS.md`, `.agents`, and `.agents/skills` paths.
- Reject malformed markers before removing any skill links.
- Restore already-removed links after a simulated later failure.

### Regression tests

- Preserve all assertions from the existing installer tests after moving them under `tests/`.
- Confirm installation remains idempotent.
- Confirm install followed by uninstall followed by install succeeds.
- Confirm both commands run by absolute script path from a working directory outside the repository.

## Acceptance criteria

- The documented command removes all artifacts demonstrably owned by the current toolkit checkout.
- Project-authored `AGENTS.md` content and local skills are preserved.
- Dry-run output accurately represents every proposed mutation.
- Declining confirmation produces no filesystem changes.
- Malformed marker state produces no filesystem changes.
- A second uninstall is successful and reports that the workspace is already uninstalled.
- Self-uninstallation never modifies the repository's authoritative `AGENTS.md`.
- Recoverable mid-operation failures restore previously removed skill links.
- Installer and uninstaller command modules do not import one another.
- Shared behavior is located under `tools/common/`, with explicit toolkit-root dependencies where needed.
- The existing installer retains its behavior after moving to `tools/install.py`.
- All installer and uninstaller tests pass using only the Python standard library.

## Known limitation and follow-up trigger

Ownership is inferred from managed markers and symlink destinations because current installations have no manifest. If the toolkit checkout is moved after installation, old relative skill links may no longer resolve inside its new path and will be conservatively preserved.

Introduce an installation manifest only if supporting moved checkouts or exact restoration of pre-install file existence becomes a requirement. A manifest should not be added merely to avoid the current conservative behavior.
