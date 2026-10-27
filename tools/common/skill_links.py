"""Skill link discovery, validation, installation, and removal operations."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class OwnedSkillLink:
    path: Path
    raw_target: str


def discover_toolkit_skills(toolkit_root: Path) -> list[Path]:
    """Return all valid skill directories in toolkit_root / 'skills'."""
    skills_dir = toolkit_root / "skills"
    if not skills_dir.is_dir():
        return []
    return [
        source
        for source in sorted(skills_dir.iterdir())
        if source.is_dir() and (source / "SKILL.md").is_file()
    ]


def validate_agents_directory(workspace: Path, action: str = "operate") -> tuple[Path, Path]:
    """Validate that workspace has valid (non-symlinked) .agents directories.

    Returns (agents_dir, skills_dir).
    Raises ValueError if .agents or .agents/skills is a symlink or not a directory.
    """
    agents_dir = workspace / ".agents"
    skills_dir = agents_dir / "skills"
    if agents_dir.is_symlink() or skills_dir.is_symlink():
        raise ValueError(f"refusing to {action} through a symlinked .agents directory")
    if agents_dir.exists() and not agents_dir.is_dir():
        raise ValueError(f"agents path is not a directory: {agents_dir}")
    if skills_dir.exists() and not skills_dir.is_dir():
        raise ValueError(f"skills path is not a directory: {skills_dir}")
    return agents_dir, skills_dir


def planned_install_links(toolkit_root: Path, workspace: Path) -> list[tuple[Path, Path]]:
    """Determine skill links to create during installation."""
    _, skills_dir = validate_agents_directory(workspace, action="install")
    links = []
    for source in discover_toolkit_skills(toolkit_root):
        target = skills_dir / source.name
        if target.is_symlink():
            if target.resolve() == source.resolve():
                continue
            raise ValueError(f"skill link already points elsewhere: {target}")
        if target.exists():
            raise ValueError(f"skill path already exists: {target}")
        links.append((source, target))
    return links


def install_links(links: list[tuple[Path, Path]]) -> list[Path]:
    """Create symlinks for skills, cleaning up on any failure."""
    created = []
    try:
        for source, target in links:
            target.parent.mkdir(parents=True, exist_ok=True)
            relative_source = os.path.relpath(source, target.parent)
            target.symlink_to(relative_source, target_is_directory=True)
            created.append(target)
    except OSError:
        for link in created:
            link.unlink(missing_ok=True)
        raise
    return created


def find_owned_skill_links(toolkit_root: Path, workspace: Path) -> list[OwnedSkillLink]:
    """Find skill symlinks in workspace owned by toolkit_root."""
    _, skills_dir = validate_agents_directory(workspace, action="uninstall")
    if not skills_dir.is_dir():
        return []

    toolkit_skills_dir = (toolkit_root / "skills").resolve()
    owned = []
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_symlink():
            continue
        try:
            raw_target = os.readlink(entry)
        except OSError:
            continue
        resolved_destination = Path(os.path.realpath(entry))
        if resolved_destination.parent == toolkit_skills_dir:
            owned.append(OwnedSkillLink(path=entry, raw_target=raw_target))
    return owned


def restore_skill_links(removed_links: list[OwnedSkillLink]) -> list[tuple[OwnedSkillLink, OSError]]:
    """Restore previously removed symlinks.

    Returns a list of any (link, exception) pairs where restoration failed.
    """
    failures = []
    for item in reversed(removed_links):
        try:
            item.path.symlink_to(item.raw_target, target_is_directory=True)
        except OSError as error:
            failures.append((item, error))
    return failures
