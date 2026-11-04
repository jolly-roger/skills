#!/usr/bin/env python3
"""Install shared rules and skills into a workspace."""

import argparse
import os
from pathlib import Path
import sys

# Ensure tools directory is in sys.path for direct execution
TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.agents_file import diff_content, managed_block, updated_content
from common.filesystem import write_atomically
from common.skill_links import install_links, planned_install_links


TOOLKIT = TOOLS_DIR.parent


def preview(before: str, after: str, target: Path) -> None:
    diff = diff_content(before, after, target)
    sys.stdout.writelines(diff)


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
    target = workspace / "AGENTS.md"
    if target.is_symlink():
        parser.error(f"refusing to replace symlink: {target}")
    self_install = workspace == TOOLKIT

    try:
        before = target.read_text(encoding="utf-8") if target.exists() else ""
        after = before if self_install else updated_content(before, managed_block(TOOLKIT))
        links = planned_install_links(TOOLKIT, workspace)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))

    if before == after and not links:
        print(f"Already up to date: {workspace}")
        return 0

    if before != after:
        preview(before, after, target)
    for source, link in links:
        print(f"Create skill link: {link} -> {os.path.relpath(source, link.parent)}")
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

    created = []
    try:
        created = install_links(links)
        if before != after:
            write_atomically(target, after)
    except OSError as error:
        for link in created:
            link.unlink(missing_ok=True)
        parser.error(str(error))
    print(f"Installed agent-toolkit in {workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
