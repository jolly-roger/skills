"""Skill link discovery, validation, installation, and removal operations."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class OwnedSkillLink:
    path: Path
    raw_target: str
    source_root: Path = Path()
    recognition_kind: str = ""


@dataclass(frozen=True)
class CandidateInspection:
    root: Path
    agents_is_file: bool
    skills_is_real_dir: bool
    skill_md_is_file: bool
    tools_install_is_file: bool
    legacy_install_is_file: bool


@dataclass(frozen=True)
class SkillLinkFacts:
    path: Path
    raw_target: str
    resolved_destination: Path
    target_exists: bool
    candidate: CandidateInspection | None


@dataclass(frozen=True)
class LinkClassification:
    category: str  # "current", "recognized", "foreign", "unproven_dangling"
    owned_link: OwnedSkillLink | None = None
    warning: str | None = None


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


def inspect_skill_link(link_path: Path) -> SkillLinkFacts | None:
    """Gather filesystem facts for a single symlink. I/O boundary."""
    try:
        raw_target = os.readlink(link_path)
    except OSError:
        return None

    resolved_destination = Path(os.path.realpath(link_path))
    target_exists = link_path.exists()

    candidate = None
    if resolved_destination.parent.name == "skills":
        candidate_root = resolved_destination.parent.parent
        skills_dir = candidate_root / "skills"
        skill_md = skills_dir / link_path.name / "SKILL.md"
        candidate = CandidateInspection(
            root=candidate_root,
            agents_is_file=(candidate_root / "AGENTS.md").is_file() and not (candidate_root / "AGENTS.md").is_symlink(),
            skills_is_real_dir=skills_dir.is_dir() and not skills_dir.is_symlink(),
            skill_md_is_file=skill_md.is_file() and not skill_md.is_symlink(),
            tools_install_is_file=(candidate_root / "tools" / "install.py").is_file() and not (candidate_root / "tools" / "install.py").is_symlink(),
            legacy_install_is_file=(candidate_root / "install.py").is_file() and not (candidate_root / "install.py").is_symlink(),
        )

    return SkillLinkFacts(
        path=link_path,
        raw_target=raw_target,
        resolved_destination=resolved_destination,
        target_exists=target_exists,
        candidate=candidate,
    )


def classify_skill_link(
    facts: SkillLinkFacts,
    toolkit_skills_dir: Path,
) -> LinkClassification:
    """Classify a skill link based on gathered filesystem facts. Pure calculation."""
    # 1. Current checkout rule (active or dangling)
    if facts.resolved_destination.parent == toolkit_skills_dir:
        return LinkClassification(
            category="current",
            owned_link=OwnedSkillLink(
                path=facts.path,
                raw_target=facts.raw_target,
                source_root=toolkit_skills_dir.parent,
                recognition_kind="current agent-toolkit checkout",
            ),
        )

    # 2. Recognized checkout rule (all 6 conditions)
    if (
        facts.candidate is not None
        and facts.resolved_destination.name == facts.path.name
        and facts.candidate.agents_is_file
        and facts.candidate.skills_is_real_dir
        and facts.candidate.skill_md_is_file
        and (facts.candidate.tools_install_is_file or facts.candidate.legacy_install_is_file)
    ):
        recognition_kind = (
            "current-layout agent-toolkit checkout"
            if facts.candidate.tools_install_is_file
            else "legacy agent-toolkit checkout"
        )
        return LinkClassification(
            category="recognized",
            owned_link=OwnedSkillLink(
                path=facts.path,
                raw_target=facts.raw_target,
                source_root=facts.candidate.root,
                recognition_kind=recognition_kind,
            ),
        )

    # 3. Unproven dangling link
    if not facts.target_exists:
        return LinkClassification(
            category="unproven_dangling",
            warning=(
                f"preserving unproven dangling skill link: "
                f"{facts.path} -> {facts.raw_target}"
            ),
        )

    # 4. Foreign link
    return LinkClassification(category="foreign")


def classify_workspace_skill_links(
    facts_list: list[SkillLinkFacts],
    toolkit_skills_dir: Path,
) -> tuple[list[OwnedSkillLink], list[str]]:
    """Deterministically classify a list of inspected skill links."""
    owned: list[OwnedSkillLink] = []
    warnings: list[str] = []
    for facts in facts_list:
        classification = classify_skill_link(facts, toolkit_skills_dir)
        if classification.owned_link is not None:
            owned.append(classification.owned_link)
        if classification.warning is not None:
            warnings.append(classification.warning)
    return owned, warnings


def find_owned_skill_links(
    toolkit_root: Path,
    workspace: Path,
) -> tuple[list[OwnedSkillLink], list[str]]:
    """Find skill symlinks in workspace owned by toolkit_root or recognized checkouts."""
    _, skills_dir = validate_agents_directory(workspace, action="uninstall")
    if not skills_dir.is_dir():
        return [], []

    toolkit_skills_dir = (toolkit_root / "skills").resolve()
    facts_list = []
    for entry in sorted(skills_dir.iterdir()):
        if not entry.is_symlink():
            continue
        facts = inspect_skill_link(entry)
        if facts is not None:
            facts_list.append(facts)

    return classify_workspace_skill_links(facts_list, toolkit_skills_dir)


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
