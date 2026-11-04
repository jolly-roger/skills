"""Filesystem inspection, hashing, copying, and legacy-link detection."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import stat

from common.skill_manifest import ManifestEntry, validate_skill_name


@dataclass(frozen=True)
class SourceSkillSnapshot:
    name: str
    source_dir: Path
    entries: tuple[ManifestEntry, ...]


@dataclass(frozen=True)
class TargetSkillSnapshot:
    name: str
    target_dir: Path
    exists: bool
    is_dir: bool
    is_symlink: bool
    raw_symlink: str | None
    entries: tuple[ManifestEntry, ...] = ()


@dataclass(frozen=True)
class LegacyLinkInfo:
    name: str
    link_path: Path
    raw_target: str
    proven_current_checkout: bool


def hash_file_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def inspect_source_skill(skill_dir: Path) -> SourceSkillSnapshot:
    """Inspect and validate a source skill directory without following symlinks.

    Rejects symlinks and special files anywhere in the tree.
    """
    skill_name = skill_dir.name
    validate_skill_name(skill_name)

    # Check root itself
    lstat = skill_dir.lstat()
    if stat.S_ISLNK(lstat.st_mode):
        raise ValueError(f"source skill {skill_name!r} root cannot be a symlink")
    if not stat.S_ISDIR(lstat.st_mode):
        raise ValueError(f"source skill {skill_name!r} root must be a directory")

    entries: list[ManifestEntry] = []
    # Deterministic walk
    _walk_source_tree(skill_dir, skill_dir, entries)
    entries.sort(key=lambda e: e.path)

    # Verify regular SKILL.md file exists at root
    skill_md_found = any(e.path == "SKILL.md" and e.type == "file" for e in entries)
    if not skill_md_found:
        raise ValueError(f"source skill {skill_name!r} must contain a regular SKILL.md file")

    return SourceSkillSnapshot(
        name=skill_name,
        source_dir=skill_dir,
        entries=tuple(entries),
    )


def _walk_source_tree(root: Path, current: Path, entries: list[ManifestEntry]) -> None:
    items = sorted(os.scandir(current), key=lambda e: e.name)
    for item in items:
        entry_path = Path(item.path)
        rel_posix = entry_path.relative_to(root).as_posix()

        # lstat check
        lstat = item.stat(follow_symlinks=False)
        mode = lstat.st_mode
        if stat.S_ISLNK(mode):
            raise ValueError(f"symlinks are not permitted in source skills: {entry_path}")
        if stat.S_ISDIR(mode):
            entries.append(ManifestEntry(path=rel_posix, type="directory"))
            _walk_source_tree(root, entry_path, entries)
        elif stat.S_ISREG(mode):
            sha = hash_file_sha256(entry_path)
            entries.append(ManifestEntry(path=rel_posix, type="file", sha256=sha))
        else:
            raise ValueError(f"special files are not permitted in source skills: {entry_path}")


def inspect_target_skill(target_dir: Path) -> TargetSkillSnapshot:
    """Inspect a workspace target skill directory without following symlinks.

    Rejects traversal or symlinks inside as an invalid/modified state.
    """
    skill_name = target_dir.name
    validate_skill_name(skill_name)

    try:
        lstat = target_dir.lstat()
    except FileNotFoundError:
        return TargetSkillSnapshot(
            name=skill_name,
            target_dir=target_dir,
            exists=False,
            is_dir=False,
            is_symlink=False,
            raw_symlink=None,
        )

    mode = lstat.st_mode
    if stat.S_ISLNK(mode):
        raw = os.readlink(target_dir)
        return TargetSkillSnapshot(
            name=skill_name,
            target_dir=target_dir,
            exists=True,
            is_dir=False,
            is_symlink=True,
            raw_symlink=raw,
        )

    if not stat.S_ISDIR(mode):
        return TargetSkillSnapshot(
            name=skill_name,
            target_dir=target_dir,
            exists=True,
            is_dir=False,
            is_symlink=False,
            raw_symlink=None,
        )

    # Real directory: walk entries safely
    entries: list[ManifestEntry] = []
    has_symlink_or_special = False

    def _walk_target(root: Path, current: Path) -> None:
        nonlocal has_symlink_or_special
        try:
            items = sorted(os.scandir(current), key=lambda e: e.name)
        except OSError:
            has_symlink_or_special = True
            return

        for item in items:
            entry_path = Path(item.path)
            rel_posix = entry_path.relative_to(root).as_posix()
            try:
                st = item.stat(follow_symlinks=False)
            except OSError:
                has_symlink_or_special = True
                continue

            if stat.S_ISLNK(st.st_mode) or (not stat.S_ISDIR(st.st_mode) and not stat.S_ISREG(st.st_mode)):
                has_symlink_or_special = True
                # Record a sentinel or omit
                continue

            if stat.S_ISDIR(st.st_mode):
                entries.append(ManifestEntry(path=rel_posix, type="directory"))
                _walk_target(root, entry_path)
            elif stat.S_ISREG(st.st_mode):
                try:
                    sha = hash_file_sha256(entry_path)
                    entries.append(ManifestEntry(path=rel_posix, type="file", sha256=sha))
                except OSError:
                    has_symlink_or_special = True

    _walk_target(target_dir, target_dir)
    entries.sort(key=lambda e: e.path)

    # If it had symlinks or special files inside, we can add a sentinel entry to ensure it never matches manifest
    if has_symlink_or_special:
        entries.append(ManifestEntry(path="__symlink_or_special_file__", type="file", sha256="0" * 64))

    return TargetSkillSnapshot(
        name=skill_name,
        target_dir=target_dir,
        exists=True,
        is_dir=True,
        is_symlink=False,
        raw_symlink=None,
        entries=tuple(entries),
    )


def discover_toolkit_skills(toolkit_root: Path) -> list[SourceSkillSnapshot]:
    """Discover and snapshot all valid source skills in toolkit_root / 'skills'."""
    skills_dir = toolkit_root / "skills"
    if not skills_dir.is_dir() or skills_dir.is_symlink():
        return []

    snapshots: list[SourceSkillSnapshot] = []
    for entry in sorted(skills_dir.iterdir()):
        lstat = entry.lstat()
        if stat.S_ISLNK(lstat.st_mode):
            continue
        if stat.S_ISDIR(lstat.st_mode) and (entry / "SKILL.md").exists():
            snapshot = inspect_source_skill(entry)
            snapshots.append(snapshot)
    return snapshots


def is_proven_current_checkout_link(
    link_path: Path,
    raw_target: str,
    toolkit_root: Path,
    expected_skill_name: str,
) -> bool:
    """Return True if link targets matching skill in running checkout lexically or resolved."""
    current_target = (toolkit_root / "skills" / expected_skill_name).resolve()

    # Lexical destination
    try:
        lexical_dest = (link_path.parent / raw_target).resolve()
        if lexical_dest == current_target:
            return True
    except Exception:
        pass

    # Resolved destination (if target exists on disk)
    try:
        resolved = Path(os.path.realpath(link_path))
        if resolved == current_target:
            return True
    except OSError:
        pass

    # Check normalized raw target path
    try:
        raw_as_path = Path(raw_target)
        if raw_as_path.is_absolute():
            if raw_as_path.resolve() == current_target:
                return True
        else:
            norm_joined = Path(os.path.normpath(str(link_path.parent / raw_target)))
            if norm_joined.resolve() == current_target:
                return True
    except Exception:
        pass

    # Also handle macOS /private prefix mismatch if any
    try:
        norm_str = os.path.normpath(str(link_path.parent / raw_target))
        if norm_str.startswith("/private/"):
            norm_str = norm_str[len("/private"):]
        curr_str = str(current_target)
        if curr_str.startswith("/private/"):
            curr_str = curr_str[len("/private"):]
        if norm_str == curr_str:
            return True
    except Exception:
        pass

    return False


def stage_skill_copy(source_snapshot: SourceSkillSnapshot, staging_dir: Path) -> Path:
    """Copy source snapshot into staging_dir/<skill_name> and verify."""
    dest = staging_dir / source_snapshot.name
    if dest.exists():
        shutil.rmtree(dest)

    shutil.copytree(
        source_snapshot.source_dir,
        dest,
        symlinks=False,
        ignore_dangling_symlinks=False,
    )

    # Verify staged copy matches snapshot
    staged_snapshot = inspect_target_skill(dest)
    if staged_snapshot.entries != source_snapshot.entries:
        raise ValueError(f"staged copy for {source_snapshot.name} does not match planned source snapshot")

    return dest
