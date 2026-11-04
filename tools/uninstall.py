#!/usr/bin/env python3
"""Remove shared rules and skills from a workspace."""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import sys

# Ensure tools directory is in sys.path for direct execution
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.agents_file import (
    classify_managed_block,
    diff_content,
    removed_content,
    validate_markers,
)
from common.filesystem import remove_empty_directory, write_atomically
from common.identity import CANONICAL_IDENTITY, LEGACY_IDENTITY, InstallationIdentity
from common.skill_files import (
    inspect_target_skill,
    is_proven_current_checkout_link,
)
from common.skill_manifest import (
    ManifestEntry,
    SkillManifest,
    SkillManifestEntry,
    compare_skill_inventory,
    create_manifest,
    inspect_workspace_manifests,
    serialize_manifest,
)

REPOSITORY_ROOT = TOOLS_DIR.parent


@dataclass(frozen=True)
class PlannedSkillUninstall:
    name: str
    target_path: Path
    action: str  # "remove_copy", "remove_legacy_link", "clean_stale_manifest"
    raw_symlink: str | None = None
    expected_entries: tuple[ManifestEntry, ...] = ()


@dataclass(frozen=True)
class UninstallPlan:
    workspace: Path
    agents_path: Path
    agents_action: str  # "keep", "rewrite", "remove"
    before_content: str
    after_content: str
    manifest_action: str  # "keep", "update", "remove"
    manifest_path: Path | None
    manifest_identity: InstallationIdentity | None
    before_manifest_raw: str | None
    after_manifest: SkillManifest | None
    skill_actions: tuple[PlannedSkillUninstall, ...]
    warnings: tuple[str, ...] = ()

    @property
    def has_changes(self) -> bool:
        return (
            self.agents_action != "keep"
            or self.manifest_action != "keep"
            or len(self.skill_actions) > 0
        )


def validate_workspace_boundaries(workspace: Path) -> tuple[Path, Path]:
    agents_dir = workspace / ".agents"
    skills_dir = agents_dir / "skills"

    if agents_dir.is_symlink() or skills_dir.is_symlink():
        raise ValueError("refusing to uninstall through a symlinked .agents directory")
    if agents_dir.exists() and not agents_dir.is_dir():
        raise ValueError(f"agents path is not a directory: {agents_dir}")
    if skills_dir.exists() and not skills_dir.is_dir():
        raise ValueError(f"skills path is not a directory: {skills_dir}")

    return agents_dir, skills_dir


def create_uninstall_plan(repository_root: Path, workspace: Path) -> UninstallPlan:
    target = workspace / "AGENTS.md"
    if target.is_symlink():
        raise ValueError(f"refusing to operate on symlink: {target}")

    agents_dir, skills_dir = validate_workspace_boundaries(workspace)
    self_uninstall = workspace.resolve() == repository_root.resolve()

    before = target.read_text(encoding="utf-8") if target.exists() else ""
    validate_markers(before)

    block_class = classify_managed_block(before)

    if self_uninstall:
        agents_action = "keep"
        after = before
    elif not target.exists() or block_class.kind == "none":
        agents_action = "keep"
        after = before
    else:
        after = removed_content(before)
        if not after.strip():
            agents_action = "remove"
        else:
            agents_action = "rewrite"

    manifest_class = inspect_workspace_manifests(workspace)
    manifest = manifest_class.manifest
    before_manifest_raw = manifest_class.raw_text
    manifest_path = manifest_class.manifest_path
    manifest_identity = manifest_class.identity

    skill_actions: list[PlannedSkillUninstall] = []
    warnings: list[str] = []
    retained_manifest_skills: dict[str, SkillManifestEntry] = {}

    processed_names: set[str] = set()

    # Process manifest skills first
    if manifest is not None:
        for name, m_skill in manifest.skills.items():
            processed_names.add(name)
            target_path = skills_dir / name
            snap = (
                inspect_target_skill(target_path)
                if target_path.exists() or target_path.is_symlink()
                else None
            )

            if snap is None or not snap.exists:
                skill_actions.append(
                    PlannedSkillUninstall(
                        name=name,
                        target_path=target_path,
                        action="clean_stale_manifest",
                    )
                )
            elif snap.is_dir:
                if compare_skill_inventory(m_skill.entries, snap.entries):
                    skill_actions.append(
                        PlannedSkillUninstall(
                            name=name,
                            target_path=target_path,
                            action="remove_copy",
                            expected_entries=snap.entries,
                        )
                    )
                else:
                    retained_manifest_skills[name] = m_skill
                    warnings.append(f"preserving modified managed skill copy: {target_path}")
            else:
                retained_manifest_skills[name] = m_skill
                warnings.append(
                    f"preserving modified managed skill (unexpected type): {target_path}"
                )

    # Check remaining entries in skills_dir for legacy links or unmanaged files
    if skills_dir.is_dir():
        for entry in sorted(skills_dir.iterdir()):
            if entry.name in processed_names:
                continue

            if entry.is_symlink():
                try:
                    raw_target = os.readlink(entry)
                except OSError:
                    raw_target = ""

                if is_proven_current_checkout_link(
                    entry, raw_target, repository_root, entry.name
                ):
                    skill_actions.append(
                        PlannedSkillUninstall(
                            name=entry.name,
                            target_path=entry,
                            action="remove_legacy_link",
                            raw_symlink=raw_target,
                        )
                    )
                else:
                    if not entry.exists():
                        warnings.append(
                            f"preserving unproven dangling skill link: {entry} -> {raw_target}"
                        )
                    else:
                        warnings.append(f"preserving unproven or foreign skill link: {entry}")
            else:
                # Unmanaged directory or file: preserve silently without warnings
                pass

    if manifest is not None and manifest_identity is not None:
        if not retained_manifest_skills:
            manifest_action = "remove"
            after_manifest = None
        else:
            manifest_action = "update"
            after_manifest = create_manifest(retained_manifest_skills, identity=manifest_identity)
    else:
        manifest_action = "keep"
        after_manifest = None

    return UninstallPlan(
        workspace=workspace,
        agents_path=target,
        agents_action=agents_action,
        before_content=before,
        after_content=after,
        manifest_action=manifest_action,
        manifest_path=manifest_path,
        manifest_identity=manifest_identity,
        before_manifest_raw=before_manifest_raw,
        after_manifest=after_manifest,
        skill_actions=tuple(skill_actions),
        warnings=tuple(warnings),
    )


def validate_uninstall_preconditions(plan: UninstallPlan, repository_root: Path) -> None:
    validate_workspace_boundaries(plan.workspace)

    current_agents = plan.agents_path.read_text(encoding="utf-8") if plan.agents_path.exists() else ""
    if current_agents != plan.before_content:
        raise ValueError("workspace changed since preview; rerun the uninstaller")

    manifest_class = inspect_workspace_manifests(plan.workspace)
    if plan.manifest_path is not None:
        if manifest_class.manifest_path != plan.manifest_path or manifest_class.raw_text != plan.before_manifest_raw:
            raise ValueError("workspace manifest changed since preview; rerun the uninstaller")
    else:
        if manifest_class.kind != "none":
            raise ValueError("workspace manifest was created since preview; rerun the uninstaller")

    for action in plan.skill_actions:
        if action.action == "remove_copy":
            snap = inspect_target_skill(action.target_path)
            if not snap.exists or not snap.is_dir or snap.entries != action.expected_entries:
                raise ValueError(
                    f"workspace changed before removing {action.target_path}; rerun the uninstaller"
                )
        elif action.action == "remove_legacy_link":
            if not action.target_path.is_symlink():
                raise ValueError(
                    f"workspace changed before removing {action.target_path}; rerun the uninstaller"
                )
            try:
                raw = os.readlink(action.target_path)
            except OSError as err:
                raise ValueError(
                    f"workspace changed before removing {action.target_path}; rerun the uninstaller"
                ) from err
            if raw != action.raw_symlink:
                raise ValueError(
                    f"workspace changed before removing {action.target_path}; rerun the uninstaller"
                )


def apply_uninstall_plan(plan: UninstallPlan, repository_root: Path) -> None:
    validate_uninstall_preconditions(plan, repository_root)

    agents_dir = plan.workspace / ".agents"
    skills_dir = agents_dir / "skills"

    backup_dir = agents_dir / ".uninstall_backup_tmp"
    backup_dir.mkdir(parents=True, exist_ok=True)

    backups: list[tuple[Path, Path, str]] = []

    try:
        # Move targets to backup
        for action in plan.skill_actions:
            if action.action == "remove_copy":
                bk = backup_dir / f"{action.name}.bak"
                action.target_path.rename(bk)
                backups.append((action.target_path, bk, "dir"))
            elif action.action == "remove_legacy_link":
                bk = backup_dir / f"{action.name}.bak"
                bk.symlink_to(action.raw_symlink)
                action.target_path.unlink()
                backups.append((action.target_path, bk, "symlink"))

        # Update or remove AGENTS.md
        if plan.agents_action == "rewrite":
            write_atomically(plan.agents_path, plan.after_content)
        elif plan.agents_action == "remove":
            plan.agents_path.unlink()

        # Update or remove manifest
        if plan.manifest_path is not None:
            if plan.manifest_action == "remove":
                plan.manifest_path.unlink(missing_ok=True)
            elif plan.manifest_action == "update" and plan.after_manifest is not None:
                manifest_content = serialize_manifest(plan.after_manifest)
                write_atomically(plan.manifest_path, manifest_content)

    except Exception as error:
        # Rollback
        for target, bk, kind in reversed(backups):
            if bk.exists() or bk.is_symlink():
                if target.exists() or target.is_symlink():
                    if target.is_dir() and not target.is_symlink():
                        shutil.rmtree(target, ignore_errors=True)
                    else:
                        target.unlink(missing_ok=True)
                bk.rename(target)

        if plan.agents_action in ("rewrite", "remove"):
            if plan.before_content:
                write_atomically(plan.agents_path, plan.before_content)
            else:
                plan.agents_path.unlink(missing_ok=True)

        if plan.manifest_path is not None and plan.before_manifest_raw is not None:
            write_atomically(plan.manifest_path, plan.before_manifest_raw)

        shutil.rmtree(backup_dir, ignore_errors=True)
        raise RuntimeError(f"uninstallation failed and was rolled back: {error}") from error

    shutil.rmtree(backup_dir, ignore_errors=True)

    try:
        remove_empty_directory(skills_dir)
        remove_empty_directory(agents_dir)
    except OSError as error:
        sys.stderr.write(f"Warning: directory cleanup failed: {error}\n")


def preview_plan(plan: UninstallPlan) -> None:
    for warning in plan.warnings:
        print(f"Warning: {warning}")

    if plan.agents_action == "rewrite":
        diff = diff_content(plan.before_content, plan.after_content, plan.agents_path)
        sys.stdout.writelines(diff)
    elif plan.agents_action == "remove":
        print(f"Remove {plan.agents_path} (managed block was only content)")

    for action in plan.skill_actions:
        if action.action == "remove_copy":
            print(f"Remove copied skill: {action.target_path}")
        elif action.action == "remove_legacy_link":
            print(f"Remove legacy skill link: {action.target_path}")
        elif action.action == "clean_stale_manifest":
            print(f"Clean stale manifest entry for missing skill: {action.name}")

    if plan.manifest_path is not None:
        if plan.manifest_action == "remove":
            print(f"Remove manifest: {plan.manifest_path}")
        elif plan.manifest_action == "update" and plan.after_manifest is not None:
            before = plan.before_manifest_raw or ""
            after = serialize_manifest(plan.after_manifest)
            diff = diff_content(before, after, plan.manifest_path)
            sys.stdout.writelines(diff)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace", type=Path, help="Workspace root (default: repository parent)"
    )
    parser.add_argument("--yes", action="store_true", help="Apply without prompting")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    workspace_input = args.workspace
    if workspace_input is None and not args.yes and not args.dry_run:
        try:
            answer = input(f"Workspace directory [{REPOSITORY_ROOT.parent}]: ").strip()
        except EOFError:
            answer = ""
        workspace_input = Path(answer) if answer else REPOSITORY_ROOT.parent
    workspace = (workspace_input or REPOSITORY_ROOT.parent).expanduser().resolve()
    if not workspace.is_dir():
        parser.error(f"workspace is not a directory: {workspace}")

    try:
        plan = create_uninstall_plan(REPOSITORY_ROOT, workspace)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))

    if not plan.has_changes:
        for warning in plan.warnings:
            print(f"Warning: {warning}")
        print(f"Already uninstalled: {workspace}")
        return 0

    preview_plan(plan)
    if args.dry_run:
        return 0

    if not args.yes:
        try:
            answer = input("\nApply this change? [y/N] ").strip().lower()
        except EOFError:
            answer = ""
        if answer not in {"y", "yes"}:
            print("No changes made.")
            return 0

    try:
        apply_uninstall_plan(plan, REPOSITORY_ROOT)
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))

    print(f"Uninstalled skills from {workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
