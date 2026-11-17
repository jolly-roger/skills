# P-00002: Cross-Installation Uninstall Compatibility

## Status

Implemented

## Date

2026-10-27

## Objective

Allow the uninstaller from one agent-toolkit checkout to remove skill symlinks installed from another existing agent-toolkit checkout, while ensuring that applying a previously previewed plan cannot remove changed workspace artifacts and that managed-block removal preserves project-authored whitespace.

This is a temporary compatibility solution based on conservative structural recognition. A stable repository identifier is explicitly deferred to a separate follow-up plan.

## Scope

- Broaden skill-link discovery from links owned by the current checkout to links owned by any structurally recognized agent-toolkit checkout.
- Support both repository layouts that currently exist:
  - Legacy checkout with `install.py` at its root.
  - Current checkout with `tools/install.py`.
- Preserve the current uninstaller preview, confirmation, dry-run, idempotency, and rollback behavior.
- Show the recognized source checkout in the uninstall preview.
- Preserve current support for dangling links into the checkout running the uninstaller.
- Revalidate planned `AGENTS.md` and skill-link state after confirmation and before mutation so a stale preview cannot overwrite or delete newly changed project content.
- Reject newly introduced symlinked `.agents` or `.agents/skills` paths after planning, including dangling symlinks for which `Path.exists()` is false.
- Preserve spaces and tabs on project-authored nonblank lines when removing the managed `AGENTS.md` block.
- Add regression coverage for uninstalling links created by a different checkout before reinstalling from the current checkout.
- Add regression coverage for workspace changes between planning and application and for significant Markdown trailing whitespace.
- Update the uninstaller documentation to describe the temporary recognition rules and their limitations.

## Non-goals

- Adding a repository identity file, installation identifier, or installation manifest.
- Reliably identifying links whose different source checkout has been moved or deleted.
- Removing regular files or directories under `.agents/skills`.
- Removing symlinks that cannot be conservatively recognized as agent-toolkit-owned.
- Automatically replacing conflicting skill links during installation.
- Treating arbitrary repositories with a `skills/` directory as agent-toolkit.
- Defining the permanent repository-identity mechanism; that work will have its own follow-up plan.
- Providing filesystem locking against adversarial concurrent mutation; this plan uses explicit optimistic preconditions appropriate for a local interactive command.

## Related decisions

- [D-00001: Project Tooling Layout](../decisions/D-00001-project-tooling-layout.md)
- [D-00003: Uninstaller Ownership and Safety Model](../decisions/D-00003-uninstaller-safety-model.md)

D-00003 has been revised and accepted to cover structurally recognized agent-toolkit checkouts, workspace-state revalidation, and preservation of project-authored content.

## Design

### Ownership categories

Classify every direct symlink under `<workspace>/.agents/skills/` into one of three categories:

| Category | Meaning | Uninstall action |
| --- | --- | --- |
| Current checkout | The link points directly into the checkout running the uninstaller. | Remove |
| Recognized checkout | The link points into another existing checkout that satisfies the temporary agent-toolkit structure checks. | Remove |
| Foreign or unproven | The link does not satisfy either ownership rule. | Preserve |

The uninstaller must continue to inspect only direct entries under `.agents/skills` after verifying that `.agents` and `.agents/skills` are real directories rather than symlinks.

### Temporary structural recognition

For a workspace link at `.agents/skills/<skill-name>`, derive a candidate source from its resolved destination. Recognize another checkout only when all of these conditions are true:

1. The destination has the shape `<candidate-root>/skills/<skill-name>`.
2. The destination basename exactly matches the workspace link name.
3. `<candidate-root>/AGENTS.md` is a regular file.
4. `<candidate-root>/skills` is a real directory.
5. `<candidate-root>/skills/<skill-name>/SKILL.md` is a regular file.
6. The candidate uses one recognized command layout:
   - `<candidate-root>/tools/install.py` is a regular file, or
   - `<candidate-root>/install.py` is a regular file for a legacy checkout.

These checks deliberately establish compatibility rather than permanent identity. They are sufficient for the observed case where the previous agent-toolkit checkout still exists, but they cannot safely prove ownership after that checkout disappears.

Do not inspect Git remotes or require network access. The utilities must continue to work for copied checkouts and without Git.

### Current-checkout links

Retain the existing exact current-checkout rule. A link whose destination is lexically a direct child of the current checkout's `skills/` directory remains removable even when its target no longer exists.

This rule is stronger than structural recognition because the running command already knows its own toolkit root.

### Links from another unavailable checkout

If a link points outside the current checkout and its target checkout is unavailable, preserve it because the temporary structural checks cannot prove ownership. The preview should warn that an unproven dangling skill link remains, without presenting the uninstall as a failure.

The future repository-identifier plan will define how these cases can be identified without relying on a live source checkout.

### Shared model and calculations

Extend the shared skill-link model so each removable link records:

- Workspace link path.
- Original raw symlink target for rollback.
- Recognized source root.
- Recognition kind: current or structural compatibility.

Keep the ownership classification deterministic after filesystem facts have been collected. The filesystem boundary gathers link and candidate-path facts; a calculation decides the category. The uninstaller consumes only the resulting plan and does not recompute ownership classification during mutation, but it must revalidate that each planned path still represents the same artifact.

### Preview and application

Preview every removable link with its source checkout and recognition kind, for example:

```text
Remove skill link: <workspace>/.agents/skills/merge-master
  source: <workspace>/agent-toolkit
  recognition: legacy agent-toolkit checkout
```

Application retains the existing link-removal and `AGENTS.md` ordering after all initial preconditions pass. Removed links must be recreated from their exact raw targets if a later principal operation or repeated precondition check fails.

No installer behavior changes are required. After the expanded uninstaller removes old recognized links, the existing installer can create links owned by the selected checkout.

### Workspace state preconditions

The preview and confirmation create a window in which workspace files can change. Applying a stale plan could otherwise delete a regular file that replaced a planned symlink, remove a repointed symlink, or overwrite newly edited project rules.

Extract application into a testable effect boundary:

```python
def apply_uninstall_plan(plan: UninstallPlan) -> None:
    ...
```

Add precondition validation:

```python
def validate_uninstall_preconditions(plan: UninstallPlan) -> None:
    ...
```

Immediately after confirmation and before the first mutation, validate the complete plan:

- `.agents` and `.agents/skills` are still real directories rather than symlinks. Check `is_symlink()` independently of `exists()` so dangling directory symlinks are rejected.
- Every planned link is still a symlink.
- Every planned link's raw target still equals the recorded `OwnedSkillLink.raw_target`.
- `AGENTS.md` is not a symlink.
- When `AGENTS.md` will be rewritten or removed, it still exists and its content exactly equals `UninstallPlan.before_content`.

Collect and validate all initial preconditions before unlinking anything. If validation fails, abort with an actionable error such as `workspace changed since preview; rerun the uninstaller` and make no changes.

Because state can also change after initial validation, repeat the relevant narrow check immediately before each link unlink and immediately before rewriting or removing `AGENTS.md`. A failure at this stage enters the existing rollback path so previously removed links are restored from their raw targets.

This is optimistic concurrency protection for a local command. It deliberately avoids platform-specific locking while closing the meaningful interactive-confirmation window and detecting ordinary concurrent edits.

Reuse the shared `.agents` directory validation where practical so planning and application enforce the same symlink rules. When no skill links were included in the plan, validation may allow the directories to remain absent, but any present or dangling symlink must still cause the stale plan to abort before `AGENTS.md` is changed.

### Preserve project-authored whitespace

Managed-block removal must normalize only blank separator lines adjacent to the block. It must not call unrestricted `rstrip()` on project-authored content because spaces or tabs at the end of a nonblank Markdown line can be significant.

Use a pure line-based boundary helper that:

- Removes trailing blank lines from the prefix and leading blank lines from the suffix.
- Treats a line as blank only for deciding whether it is a separator.
- Removes newline characters from the retained prefix boundary without removing spaces or tabs from its final nonblank line.
- Preserves suffix content, including indentation and trailing whitespace on nonblank lines.
- Joins retained content on both sides with one blank line.
- Keeps one terminal newline when only prefix content remains.
- Returns an empty string when the managed block and surrounding whitespace were the only content.

Keep this transformation independent of filesystem I/O and cover it with direct unit tests.

### Temporary nature and follow-up

This plan must not introduce a repository identifier. Its structural recognition is an explicit transitional mechanism.

A separate future plan will define stable agent-toolkit identity, migration behavior, and handling for dangling links from moved or deleted checkouts. That plan will decide whether identity belongs in the source repository, workspace installation metadata, or both. It will receive its own plan number when created rather than reserving an identifier here.

## Implementation steps

1. Keep the accepted D-00003 ownership and safety language synchronized with the implementation.
2. Extend the shared skill-link data model with source-root and recognition-kind information.
3. Separate candidate filesystem inspection from deterministic ownership classification.
4. Preserve the exact current-checkout rule for active and dangling links.
5. Add temporary structural recognition for active links into legacy and current-layout agent-toolkit checkouts.
6. Preserve unproven and foreign links, recording warnings for unproven dangling links.
7. Update uninstall preview output with the recognized source and recognition kind.
8. Extract application into `apply_uninstall_plan` and add whole-plan precondition validation after confirmation.
9. Ensure precondition validation rejects `.agents` and `.agents/skills` symlinks before checking existence, including dangling symlinks created after planning.
10. Repeat artifact-specific precondition checks immediately before each destructive action and route failures through rollback.
11. Replace broad prefix trimming in managed-block removal with a pure boundary-blank-line calculation that preserves nonblank-line spaces and tabs.
12. Add unit and command-level regression tests for cross-installation discovery, stale plans, dangling directory symlinks, rollback, and whitespace preservation.
13. Update the root `README.md` with concise cross-installation behavior and the temporary limitation.
14. Run the complete test suite and reproduce uninstall followed by install across two local checkouts.
15. When all expanded acceptance criteria are satisfied, mark this plan `Implemented` and update `docs/plans/README.md` in the same change.

## Test plan

### Ownership classification tests

- Classify an active link into the current checkout as removable.
- Classify a dangling link lexically targeting the current checkout as removable.
- Classify an active link into another current-layout checkout as removable.
- Classify an active link into another legacy-layout checkout as removable.
- Reject a candidate whose destination basename differs from the workspace link name.
- Reject a candidate without `AGENTS.md`.
- Reject a candidate without the referenced `SKILL.md`.
- Reject a candidate without either recognized installer path.
- Preserve a regular file or directory with the same skill name.
- Preserve an arbitrary foreign symlink.
- Preserve an unproven dangling link outside the current checkout and produce a warning.

### Command integration tests

- Install from checkout A, uninstall with checkout B, and verify all installed skill links are removed.
- Reproduce the legacy embedded-checkout scenario where links point to `<workspace>/agent-toolkit/skills/*` and uninstallation runs from a sibling checkout.
- After cross-checkout uninstall, install from checkout B without skill-link conflicts.
- Preview the source checkout and recognition kind in dry-run mode.
- Make no changes after interactive decline.
- Remove links from more than one recognized agent-toolkit checkout in one workspace.
- Preserve unrelated entries under `.agents` during cross-checkout uninstall.
- Restore cross-checkout links with their original raw targets after a simulated later failure.
- Preserve existing current-checkout uninstall and self-uninstall behavior.

### Regression tests

- Run all existing installer, uninstaller, content, and skill-link tests.
- Confirm malformed `AGENTS.md` markers prevent all mutations.
- Confirm repeated uninstall remains idempotent.
- Confirm the implementation uses only the Python standard library and does not invoke Git.

### Workspace change tests

- Replace a planned skill symlink with a regular file after planning and verify the file is preserved.
- Repoint a planned skill symlink after planning and verify the new link is preserved.
- Delete a planned skill symlink after planning and verify application aborts cleanly.
- Edit `AGENTS.md` after planning and verify the new content is preserved.
- Replace `AGENTS.md` with a symlink after planning and verify the target is untouched.
- Create a dangling `.agents` symlink after planning when no skill links were planned; verify application aborts and `AGENTS.md` remains unchanged.
- Create a real `.agents` directory with a dangling `.agents/skills` symlink after planning; verify application aborts and `AGENTS.md` remains unchanged.
- Trigger a repeated precondition failure after an earlier link removal and verify rollback restores the original raw target.
- Verify an initial precondition failure causes no filesystem mutation.

### Whitespace preservation tests

- Preserve two trailing spaces used as a Markdown hard break before the managed block.
- Preserve a trailing tab on a nonblank project-authored line.
- Preserve indented project content after the managed block.
- Normalize whitespace-only separator lines without retaining the managed block's surrounding separators.
- Return empty content when only whitespace and the managed block exist.

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Structural checks falsely recognize an unrelated repository. | Require the full direct-skill path, matching name, `AGENTS.md`, `SKILL.md`, and a recognized installer layout; preserve anything that does not satisfy every check. |
| A previous checkout has been moved or deleted. | Preserve unproven dangling links and warn; defer reliable handling to the repository-identifier follow-up. |
| Workspace state changes between preview and application. | Validate all plan preconditions after confirmation, repeat the relevant check immediately before each destructive action, and abort or roll back on mismatch. |
| A dangling directory symlink bypasses an existence-gated check. | Check `is_symlink()` before and independently of `exists()` for `.agents` and `.agents/skills`, and cover both paths with stale-plan tests. |
| Rollback recreates a link with a different target. | Store and restore the original raw symlink target rather than a recomputed path. |
| Managed-block removal alters meaningful Markdown whitespace. | Remove only boundary blank lines and test preservation of spaces and tabs on nonblank project-authored lines. |
| Temporary heuristics become treated as permanent identity. | Document them as compatibility behavior and require a separate follow-up plan for stable identity. |

## Acceptance criteria

- Running the current uninstaller removes skill links installed from another existing legacy or current-layout agent-toolkit checkout.
- The reported `aio` embedded-checkout scenario can uninstall and then reinstall from the sibling checkout without manual link removal.
- Current-checkout active and dangling links retain their existing behavior.
- Regular files, directories, foreign links, and unproven links remain untouched.
- Preview output identifies why and from which checkout each link is removable.
- Rollback restores every removed link using its original raw target.
- Applying a stale plan never deletes a replacement regular file, removes a repointed link, or overwrites changed `AGENTS.md` content.
- Dangling `.agents` and `.agents/skills` symlinks introduced after planning are detected before mutation even though their targets do not exist.
- Initial precondition failure causes no mutation, and a later precondition failure restores earlier removed links.
- Removing the managed block preserves spaces and tabs on all retained nonblank project-authored lines.
- No repository identifier, installation manifest, Git inspection, or network dependency is introduced.
- Existing installer and uninstaller behavior remains covered and all tests pass.
- Documentation explicitly states that structural recognition is temporary and that stable identity is deferred to a future plan.

## Open questions

- None. Stable repository identity is intentionally outside this plan and will be designed separately.
