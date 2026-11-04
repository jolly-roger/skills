#!/usr/bin/env python3
"""Install shared rules and skills into a workspace."""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import sys
import tempfile

# Ensure tools directory is in sys.path for direct execution
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.agents_file import (
    classify_managed_block,
    diff_content,
    managed_block,
    updated_content,
)
from common.filesystem import write_atomically
from common.identity import CANONICAL_IDENTITY, LEGACY_IDENTITY, InstallationIdentity
from common.skill_files import (
    SourceSkillSnapshot,
    TargetSkillSnapshot,
    discover_repository_skills,
    inspect_source_skill,
    inspect_target_skill,
    is_proven_current_checkout_link,
    stage_skill_copy,
)
from common.skill_manifest import (
    SkillManifest,
    SkillManifestEntry,
    compare_skill_inventory,
    create_manifest,
    inspect_workspace_manifests,
    serialize_manifest,
)

REPOSITORY_ROOT = TOOLS_DIR.parent


@dataclass(frozen=True)
class PlannedSkillInstall:
    name: str
    target_dir: Path
    action: str  # "create", "update", "replace_legacy_link", "retire"
    source_snapshot: SourceSkillSnapshot | None
    existing_target: TargetSkillSnapshot | None


@dataclass(frozen=True)
class InstallPlan:
    workspace: Path
    agents_path: Path
    before_agents: str
    after_agents: str
    manifest_action: str  # "create", "update", "migrate"
    legacy_manifest_path: Path | None
    canonical_manifest_path: Path
    before_manifest_raw: str | None
    after_manifest: SkillManifest
    skill_actions: tuple[PlannedSkillInstall, ...]
    marker_migration: bool = False

    @property
    def has_changes(self) -> bool:
        if self.before_agents != self.after_agents:
            return True
        if self.legacy_manifest_path is not None:
            return True
        before_manifest = self.before_manifest_raw or ""
        after_manifest_str = serialize_manifest(self.after_manifest)
        if before_manifest != after_manifest_str:
            return True
        return any(
            act.action in ("create", "update", "replace_legacy_link", "retire")
            for act in self.skill_actions
        )


def validate_workspace_boundaries(workspace: Path) -> tuple[Path, Path]:
    agents_dir = workspace / ".agents"
    skills_dir = agents_dir / "skills"

    if agents_dir.is_symlink() or skills_dir.is_symlink():
        raise ValueError("refusing to install through a symlinked .agents directory")
    if agents_dir.exists() and not agents_dir.is_dir():
        raise ValueError(f"agents path is not a directory: {agents_dir}")
    if skills_dir.exists() and not skills_dir.is_dir():
        raise ValueError(f"skills path is not a directory: {skills_dir}")

    return agents_dir, skills_dir


def create_install_plan(repository_root: Path, workspace: Path) -> InstallPlan:
    target_agents = workspace / "AGENTS.md"
    if target_agents.is_symlink():
        raise ValueError(f"refusing to replace symlink: {target_agents}")

    agents_dir, skills_dir = validate_workspace_boundaries(workspace)
    self_install = workspace.resolve() == repository_root.resolve()

    before_agents = target_agents.read_text(encoding="utf-8") if target_agents.exists() else ""
    block_class = classify_managed_block(before_agents)
    marker_migration = block_class.kind == "legacy"

    after_agents = (
        before_agents
        if self_install
        else updated_content(before_agents, managed_block(repository_root, CANONICAL_IDENTITY))
    )

    manifest_class = inspect_workspace_manifests(workspace)
    current_manifest = manifest_class.manifest
    before_manifest_raw = manifest_class.raw_text
    legacy_manifest_path = (
        manifest_class.manifest_path if manifest_class.kind == "legacy" else None
    )
    canonical_manifest_path = workspace / CANONICAL_IDENTITY.manifest_relative_path

    sources = discover_repository_skills(repository_root)
    source_map = {s.name: s for s in sources}

    planned_actions: list[PlannedSkillInstall] = []
    new_manifest_skills: dict[str, SkillManifestEntry] = {}

    known_skill_names = set(source_map.keys())
    if current_manifest:
        known_skill_names.update(current_manifest.skills.keys())
    if skills_dir.is_dir():
        for entry in skills_dir.iterdir():
            known_skill_names.add(entry.name)

    conflicts: list[str] = []

    for name in sorted(known_skill_names):
        target = skills_dir / name
        target_snap = (
            inspect_target_skill(target) if target.exists() or target.is_symlink() else None
        )
        source_snap = source_map.get(name)
        manifest_entry = current_manifest.skills.get(name) if current_manifest else None

        if source_snap is not None:
            # Skill exists in source
            if target_snap is None or not target_snap.exists:
                planned_actions.append(
                    PlannedSkillInstall(
                        name=name,
                        target_dir=target,
                        action="create",
                        source_snapshot=source_snap,
                        existing_target=target_snap,
                    )
                )
                new_manifest_skills[name] = SkillManifestEntry(
                    name=name,
                    target=f"skills/{name}",
                    entries=source_snap.entries,
                )
            elif target_snap.is_symlink:
                if is_proven_current_checkout_link(
                    target, target_snap.raw_symlink or "", repository_root, name
                ):
                    planned_actions.append(
                        PlannedSkillInstall(
                            name=name,
                            target_dir=target,
                            action="replace_legacy_link",
                            source_snapshot=source_snap,
                            existing_target=target_snap,
                        )
                    )
                    new_manifest_skills[name] = SkillManifestEntry(
                        name=name,
                        target=f"skills/{name}",
                        entries=source_snap.entries,
                    )
                else:
                    conflicts.append(f"unproven or foreign symlink at skill path: {target}")
            elif not target_snap.is_dir:
                conflicts.append(f"skill path is not a directory: {target}")
            else:
                # target is a directory
                if manifest_entry is not None:
                    if compare_skill_inventory(manifest_entry.entries, target_snap.entries):
                        if source_snap.entries == target_snap.entries:
                            pass
                        else:
                            planned_actions.append(
                                PlannedSkillInstall(
                                    name=name,
                                    target_dir=target,
                                    action="update",
                                    source_snapshot=source_snap,
                                    existing_target=target_snap,
                                )
                            )
                        new_manifest_skills[name] = SkillManifestEntry(
                            name=name,
                            target=f"skills/{name}",
                            entries=source_snap.entries,
                        )
                    else:
                        conflicts.append(f"locally modified managed skill copy: {target}")
                else:
                    conflicts.append(f"unmanaged skill directory: {target}")
        else:
            # Source no longer has this skill (retired)
            if manifest_entry is not None:
                if target_snap is not None and target_snap.exists and target_snap.is_dir:
                    if compare_skill_inventory(manifest_entry.entries, target_snap.entries):
                        planned_actions.append(
                            PlannedSkillInstall(
                                name=name,
                                target_dir=target,
                                action="retire",
                                source_snapshot=None,
                                existing_target=target_snap,
                            )
                        )
                    else:
                        conflicts.append(f"locally modified retired skill copy: {target}")

    if conflicts:
        details = "\n".join(f"  {c}" for c in conflicts)
        raise ValueError(f"installation conflict detected:\n{details}")

    after_manifest = create_manifest(new_manifest_skills, identity=CANONICAL_IDENTITY)

    if manifest_class.kind == "legacy":
        manifest_action = "migrate"
    elif manifest_class.kind == "canonical":
        manifest_action = "update"
    else:
        manifest_action = "create"

    return InstallPlan(
        workspace=workspace,
        agents_path=target_agents,
        before_agents=before_agents,
        after_agents=after_agents,
        manifest_action=manifest_action,
        legacy_manifest_path=legacy_manifest_path,
        canonical_manifest_path=canonical_manifest_path,
        before_manifest_raw=before_manifest_raw,
        after_manifest=after_manifest,
        skill_actions=tuple(planned_actions),
        marker_migration=marker_migration,
    )


def preview_install_plan(plan: InstallPlan) -> None:
    if plan.marker_migration:
        print("Migrate managed block: agent-toolkit -> jolly-roger-skills")

    if plan.before_agents != plan.after_agents:
        diff = diff_content(plan.before_agents, plan.after_agents, plan.agents_path)
        sys.stdout.writelines(diff)

    for action in plan.skill_actions:
        if action.action == "create":
            print(f"Install copied skill: {action.target_dir}")
        elif action.action == "update":
            print(f"Update copied skill: {action.target_dir}")
        elif action.action == "replace_legacy_link":
            print(f"Replace legacy skill link with copy: {action.target_dir}")
        elif action.action == "retire":
            print(f"Remove retired skill copy: {action.target_dir}")

    if plan.manifest_action == "migrate":
        print(f"Migrate manifest: {plan.legacy_manifest_path} -> {plan.canonical_manifest_path}")
    elif plan.manifest_action in ("create", "update"):
        before = plan.before_manifest_raw or ""
        after = serialize_manifest(plan.after_manifest)
        if before != after:
            diff = diff_content(before, after, plan.canonical_manifest_path)
            sys.stdout.writelines(diff)


def validate_install_preconditions(plan: InstallPlan, repository_root: Path) -> None:
    validate_workspace_boundaries(plan.workspace)

    current_agents = plan.agents_path.read_text(encoding="utf-8") if plan.agents_path.exists() else ""
    if current_agents != plan.before_agents:
        raise ValueError("workspace changed since preview; rerun the installer")

    manifest_class = inspect_workspace_manifests(plan.workspace)
    current_block = classify_managed_block(current_agents)
    if plan.marker_migration and current_block.kind != "legacy":
        raise ValueError("workspace markers changed since preview; rerun the installer")
    if plan.legacy_manifest_path is not None:
        if manifest_class.kind != "legacy" or manifest_class.raw_text != plan.before_manifest_raw:
            raise ValueError("workspace manifest changed since preview; rerun the installer")
    elif plan.before_manifest_raw is not None:
        if manifest_class.kind != "canonical" or manifest_class.raw_text != plan.before_manifest_raw:
            raise ValueError("workspace manifest changed since preview; rerun the installer")
    else:
        if manifest_class.kind != "none":
            raise ValueError("workspace manifest was created since preview; rerun the installer")

    for action in plan.skill_actions:
        if action.source_snapshot is not None:
            source_current = inspect_source_skill(action.source_snapshot.source_dir)
            if source_current.entries != action.source_snapshot.entries:
                raise ValueError(
                    f"source skill {action.name} changed since preview; rerun the installer"
                )

        target_current = (
            inspect_target_skill(action.target_dir)
            if action.target_dir.exists() or action.target_dir.is_symlink()
            else None
        )
        if action.action in ("update", "retire"):
            if not target_current or target_current.entries != action.existing_target.entries:
                raise ValueError(
                    f"target skill {action.name} changed since preview; rerun the installer"
                )
        elif action.action == "replace_legacy_link":
            if (
                not target_current
                or not target_current.is_symlink
                or target_current.raw_symlink != action.existing_target.raw_symlink
            ):
                raise ValueError(
                    f"legacy link {action.name} changed since preview; rerun the installer"
                )
        elif action.action == "create":
            if target_current and target_current.exists:
                raise ValueError(
                    f"target skill {action.name} was created since preview; rerun the installer"
                )


def apply_install_plan(plan: InstallPlan, repository_root: Path) -> None:
    validate_install_preconditions(plan, repository_root)

    agents_dir = plan.workspace / ".agents"
    skills_dir = agents_dir / "skills"

    skills_dir.mkdir(parents=True, exist_ok=True)

    staging_temp_parent = agents_dir / ".staging_tmp"
    staging_temp_parent.mkdir(parents=True, exist_ok=True)

    backups: list[tuple[Path, Path, str]] = []
    staged_copies: list[tuple[Path, Path]] = []

    legacy_manifest_backup: Path | None = None

    try:
        # Step 1: Stage all new copies
        for action in plan.skill_actions:
            if action.action in ("create", "update", "replace_legacy_link"):
                staged = stage_skill_copy(action.source_snapshot, staging_temp_parent)
                staged_copies.append((staged, action.target_dir))

        # Step 2: Backup old targets
        backup_dir = agents_dir / ".backup_tmp"
        backup_dir.mkdir(parents=True, exist_ok=True)

        for action in plan.skill_actions:
            if action.action in ("update", "replace_legacy_link", "retire"):
                bk = backup_dir / f"{action.name}.bak"
                if action.target_dir.is_symlink():
                    raw = os.readlink(action.target_dir)
                    bk.symlink_to(raw)
                    action.target_dir.unlink()
                    backups.append((action.target_dir, bk, "symlink"))
                else:
                    action.target_dir.rename(bk)
                    backups.append((action.target_dir, bk, "dir"))

        # Step 3: Move staged copies into targets
        for staged, target in staged_copies:
            staged.rename(target)

        # Step 4: Write AGENTS.md if changed
        if plan.before_agents != plan.after_agents:
            write_atomically(plan.agents_path, plan.after_agents)

        # Step 5: Backup & remove legacy manifest if migrating
        if plan.legacy_manifest_path is not None and plan.legacy_manifest_path.exists():
            legacy_manifest_backup = backup_dir / "legacy_manifest.bak"
            plan.legacy_manifest_path.rename(legacy_manifest_backup)

        # Step 6: Write canonical manifest atomically
        manifest_content = serialize_manifest(plan.after_manifest)
        write_atomically(plan.canonical_manifest_path, manifest_content)

    except Exception as error:
        # Rollback
        for _, target in staged_copies:
            if target.exists() and not any(b[0] == target for b in backups):
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target, ignore_errors=True)
                else:
                    target.unlink(missing_ok=True)

        for target, bk, kind in reversed(backups):
            if bk.exists() or bk.is_symlink():
                if target.exists() or target.is_symlink():
                    if target.is_dir() and not target.is_symlink():
                        shutil.rmtree(target, ignore_errors=True)
                    else:
                        target.unlink(missing_ok=True)
                bk.rename(target)

        if plan.before_agents != plan.after_agents:
            if plan.before_agents:
                write_atomically(plan.agents_path, plan.before_agents)
            else:
                plan.agents_path.unlink(missing_ok=True)

        # Restore canonical manifest
        if plan.legacy_manifest_path is None and plan.before_manifest_raw is not None:
            write_atomically(plan.canonical_manifest_path, plan.before_manifest_raw)
        else:
            plan.canonical_manifest_path.unlink(missing_ok=True)

        # Restore legacy manifest if it was backed up
        if legacy_manifest_backup and legacy_manifest_backup.exists():
            if plan.legacy_manifest_path:
                legacy_manifest_backup.rename(plan.legacy_manifest_path)

        shutil.rmtree(staging_temp_parent, ignore_errors=True)
        shutil.rmtree(backup_dir, ignore_errors=True)
        raise RuntimeError(f"installation failed and was rolled back: {error}") from error

    shutil.rmtree(staging_temp_parent, ignore_errors=True)
    shutil.rmtree(backup_dir, ignore_errors=True)


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
        plan = create_install_plan(REPOSITORY_ROOT, workspace)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))

    if not plan.has_changes:
        print(f"Already up to date: {workspace}")
        return 0

    preview_install_plan(plan)
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
        apply_install_plan(plan, REPOSITORY_ROOT)
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))

    print(f"Installed skills in {workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
