#!/usr/bin/env python3
"""Remove shared rules and skills from a workspace."""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys

# Ensure tools directory is in sys.path for direct execution
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.agents_file import BEGIN, diff_content, removed_content, validate_markers
from common.filesystem import remove_empty_directory, write_atomically
from common.skill_links import OwnedSkillLink, find_owned_skill_links, restore_skill_links


TOOLKIT = TOOLS_DIR.parent


@dataclass(frozen=True)
class UninstallPlan:
    workspace: Path
    agents_path: Path
    agents_action: str  # "keep", "rewrite", "remove"
    before_content: str
    after_content: str
    links: tuple[OwnedSkillLink, ...]
    warnings: tuple[str, ...] = ()

    @property
    def has_changes(self) -> bool:
        return self.agents_action != "keep" or len(self.links) > 0


def create_uninstall_plan(toolkit_root: Path, workspace: Path) -> UninstallPlan:
    target = workspace / "AGENTS.md"
    if target.is_symlink():
        raise ValueError(f"refusing to operate on symlink: {target}")

    self_uninstall = workspace.resolve() == toolkit_root.resolve()
    before = target.read_text(encoding="utf-8") if target.exists() else ""
    validate_markers(before)

    if self_uninstall:
        agents_action = "keep"
        after = before
    elif not target.exists() or BEGIN not in before:
        agents_action = "keep"
        after = before
    else:
        after = removed_content(before)
        if not after.strip():
            agents_action = "remove"
        else:
            agents_action = "rewrite"

    links, warnings = find_owned_skill_links(toolkit_root, workspace)
    return UninstallPlan(
        workspace=workspace,
        agents_path=target,
        agents_action=agents_action,
        before_content=before,
        after_content=after,
        links=tuple(links),
        warnings=tuple(warnings),
    )


def validate_uninstall_preconditions(plan: UninstallPlan) -> None:
    """Validate all workspace state preconditions before applying the plan."""
    agents_dir = plan.workspace / ".agents"
    skills_dir = agents_dir / "skills"

    if agents_dir.is_symlink() or skills_dir.is_symlink():
        raise ValueError("workspace changed since preview; rerun the uninstaller")

    if plan.links:
        if not agents_dir.is_dir() or not skills_dir.is_dir():
            raise ValueError("workspace changed since preview; rerun the uninstaller")
    else:
        if agents_dir.exists() and not agents_dir.is_dir():
            raise ValueError("workspace changed since preview; rerun the uninstaller")
        if skills_dir.exists() and not skills_dir.is_dir():
            raise ValueError("workspace changed since preview; rerun the uninstaller")

    for link in plan.links:
        if not link.path.is_symlink():
            raise ValueError("workspace changed since preview; rerun the uninstaller")
        try:
            raw = os.readlink(link.path)
        except OSError:
            raise ValueError("workspace changed since preview; rerun the uninstaller")
        if raw != link.raw_target:
            raise ValueError("workspace changed since preview; rerun the uninstaller")

    if plan.agents_path.is_symlink():
        raise ValueError("workspace changed since preview; rerun the uninstaller")

    if plan.agents_action in ("rewrite", "remove"):
        if not plan.agents_path.is_file() or plan.agents_path.is_symlink():
            raise ValueError("workspace changed since preview; rerun the uninstaller")
        try:
            current_content = plan.agents_path.read_text(encoding="utf-8")
        except OSError:
            raise ValueError("workspace changed since preview; rerun the uninstaller")
        if current_content != plan.before_content:
            raise ValueError("workspace changed since preview; rerun the uninstaller")


def apply_uninstall_plan(plan: UninstallPlan) -> None:
    """Apply plan mutations with whole-plan validation, step checks, and rollback."""
    validate_uninstall_preconditions(plan)

    agents_dir = plan.workspace / ".agents"
    skills_dir = agents_dir / "skills"

    removed_links: list[OwnedSkillLink] = []
    try:
        for link in plan.links:
            if not link.path.is_symlink():
                raise ValueError(f"workspace changed before removing {link.path}; rerun the uninstaller")
            try:
                raw = os.readlink(link.path)
            except OSError as err:
                raise ValueError(f"workspace changed before removing {link.path}; rerun the uninstaller") from err
            if raw != link.raw_target:
                raise ValueError(f"workspace changed before removing {link.path}; rerun the uninstaller")

            link.path.unlink()
            removed_links.append(link)

        if plan.agents_action in ("rewrite", "remove"):
            if agents_dir.is_symlink() or skills_dir.is_symlink():
                raise ValueError("workspace changed before modifying AGENTS.md; rerun the uninstaller")
            if plan.agents_path.is_symlink() or not plan.agents_path.is_file():
                raise ValueError("workspace changed before modifying AGENTS.md; rerun the uninstaller")
            try:
                current_content = plan.agents_path.read_text(encoding="utf-8")
            except OSError as err:
                raise ValueError("workspace changed before modifying AGENTS.md; rerun the uninstaller") from err
            if current_content != plan.before_content:
                raise ValueError("workspace changed before modifying AGENTS.md; rerun the uninstaller")

            if plan.agents_action == "rewrite":
                write_atomically(plan.agents_path, plan.after_content)
            elif plan.agents_action == "remove":
                plan.agents_path.unlink()
    except (OSError, ValueError) as error:
        rollback_failures = restore_skill_links(removed_links)
        if rollback_failures:
            details = "\n".join(f"  {item.path}: {err}" for item, err in rollback_failures)
            raise RuntimeError(f"{error}\nFailed to roll back some skill links:\n{details}") from error
        raise

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

    for link in plan.links:
        print(f"Remove skill link: {link.path}")
        print(f"  source: {link.source_root}")
        print(f"  recognition: {link.recognition_kind}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, help="Workspace root (default: toolkit parent)")
    parser.add_argument("--yes", action="store_true", help="Apply without prompting")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    workspace_input = args.workspace
    if workspace_input is None and not args.yes and not args.dry_run:
        try:
            answer = input(f"Workspace directory [{TOOLKIT.parent}]: ").strip()
        except EOFError:
            answer = ""
        workspace_input = Path(answer) if answer else TOOLKIT.parent
    workspace = (workspace_input or TOOLKIT.parent).expanduser().resolve()
    if not workspace.is_dir():
        parser.error(f"workspace is not a directory: {workspace}")

    try:
        plan = create_uninstall_plan(TOOLKIT, workspace)
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
        apply_uninstall_plan(plan)
    except (OSError, ValueError, RuntimeError) as error:
        parser.error(str(error))

    print(f"Uninstalled agent-toolkit from {workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
