# D-00001: Project Tooling Layout

## Status

Accepted

## Date

2026-10-27

## Context

Agent-toolkit is a collection of utilities and shared guidance for coding agents. It is not a standalone application and does not need an application-oriented source layout or an installed command-line package.

The installer and planned uninstaller need reusable marker, file, and skill-link behavior. Importing one executable script from the other would couple their workflows and make shared behavior harder to test independently.

## Decision

Store executable project utilities and their reusable implementation under `tools/`:

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

The command modules are thin orchestration boundaries. Deterministic content transformations belong in shared modules, while filesystem effects remain explicit and narrowly scoped.

`tools/install.py` and `tools/uninstall.py` may import from `tools/common/`, but they must not import from one another. Dependencies such as the toolkit root are derived by the command and passed explicitly to shared operations that need them.

Do not introduce an application-style `src/` layout, Python packaging metadata, or an installed CLI unless a later requirement justifies that change.

## Alternatives considered

### Keep scripts at the repository root

This keeps current paths short but mixes executable code with repository content and provides no clear home for future utilities.

### Import shared functions from the installer

This avoids an immediate extraction but makes the uninstaller depend on another executable command and blurs shared logic with installation workflow.

### Use `src/` and package the project

This is conventional for a distributable application or library, but adds packaging and installation concepts that the repository does not currently need.

### Name the shared directory `toolkit_shared`

The name is explicit but unnecessarily verbose inside the already scoped `tools/` directory. `common/` communicates its role without suggesting a separately distributed package.

## Consequences

### Positive

- All executable project utilities have one predictable location.
- Installer and uninstaller logic can reuse independently testable modules.
- Pure transformations can be tested separately from filesystem actions.
- The structure can accommodate future coding-agent utilities without presenting the repository as an application.

### Negative

- The existing installer path and its tests must move.
- Documentation and automation that invoke the root `install.py` path must be updated.
- Direct script execution requires imports to remain valid when invoked by absolute path from outside the repository.

## Related documents

- [P-00001: Agent Toolkit Uninstaller](../plans/P-00001-uninstaller.md)

## Supersedes

None

## Superseded by

None
