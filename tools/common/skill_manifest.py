"""Manifest domain types, validation, deterministic serialization, and inventory comparison."""

from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any

FORMAT_NAME = "agent-toolkit.skills"
CURRENT_VERSION = 1
MANIFEST_FILENAME = "agent-toolkit-manifest.json"
MANIFEST_RELATIVE_PATH = Path(".agents") / MANIFEST_FILENAME

_SHA256_HEX_REGEX = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ManifestEntry:
    path: str
    type: str  # "file" or "directory"
    sha256: str | None = None

    def to_dict(self) -> dict[str, str]:
        if self.type == "file":
            return {"path": self.path, "type": "file", "sha256": self.sha256 or ""}
        return {"path": self.path, "type": "directory"}


@dataclass(frozen=True)
class SkillManifestEntry:
    name: str
    target: str
    entries: tuple[ManifestEntry, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "entries": [entry.to_dict() for entry in self.entries],
        }


@dataclass(frozen=True)
class SkillManifest:
    format: str
    version: int
    skills: dict[str, SkillManifestEntry]

    def to_json(self) -> str:
        data = {
            "format": self.format,
            "version": self.version,
            "skills": {
                name: self.skills[name].to_dict()
                for name in sorted(self.skills.keys())
            },
        }
        return json.dumps(data, indent=2, sort_keys=True) + "\n"


def validate_skill_name(name: str) -> None:
    if not name or name in (".", "..") or "/" in name or "\\" in name:
        raise ValueError(f"invalid skill name: {name!r}")


def validate_entry_relative_path(rel_path: str) -> str:
    """Validate and return normalized POSIX relative entry path."""
    if not rel_path or rel_path.startswith("/") or "\\" in rel_path:
        raise ValueError(f"invalid entry path: {rel_path!r}")
    posix = PurePosixPath(rel_path)
    for part in posix.parts:
        if part in (".", ".."):
            raise ValueError(f"entry path cannot traverse or use relative parts: {rel_path!r}")
    normalized = str(posix)
    if normalized.startswith("/") or normalized == ".":
        raise ValueError(f"invalid entry path: {rel_path!r}")
    return normalized


def create_manifest(skills: dict[str, SkillManifestEntry]) -> SkillManifest:
    return SkillManifest(
        format=FORMAT_NAME,
        version=CURRENT_VERSION,
        skills=dict(sorted(skills.items())),
    )


def parse_manifest(raw_text: str) -> SkillManifest:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as err:
        raise ValueError(f"invalid manifest JSON: {err}") from err

    if not isinstance(data, dict):
        raise ValueError("manifest root must be a JSON object")

    manifest_format = data.get("format")
    if manifest_format != FORMAT_NAME:
        raise ValueError(f"unknown or invalid manifest format: {manifest_format!r}")

    version = data.get("version")
    if version != CURRENT_VERSION:
        raise ValueError(f"unsupported manifest version: {version!r}")

    skills_data = data.get("skills")
    if not isinstance(skills_data, dict):
        raise ValueError("manifest 'skills' must be a JSON object")

    skills: dict[str, SkillManifestEntry] = {}
    for name, skill_info in skills_data.items():
        if not isinstance(name, str):
            raise ValueError(f"skill name must be a string: {name!r}")
        validate_skill_name(name)

        if not isinstance(skill_info, dict):
            raise ValueError(f"skill manifest data for {name!r} must be an object")

        target = skill_info.get("target")
        expected_target = f"skills/{name}"
        if target != expected_target:
            raise ValueError(
                f"invalid target for skill {name!r}: expected {expected_target!r}, got {target!r}"
            )

        entries_data = skill_info.get("entries")
        if not isinstance(entries_data, list):
            raise ValueError(f"'entries' for skill {name!r} must be a list")

        entries: list[ManifestEntry] = []
        seen_paths: set[str] = set()
        prev_path: str | None = None

        for entry_raw in entries_data:
            if not isinstance(entry_raw, dict):
                raise ValueError(f"entry in skill {name!r} must be an object")

            raw_path = entry_raw.get("path")
            if not isinstance(raw_path, str):
                raise ValueError(f"entry path in skill {name!r} must be a string")
            norm_path = validate_entry_relative_path(raw_path)
            if norm_path != raw_path:
                raise ValueError(f"entry path {raw_path!r} is not normalized")

            if norm_path in seen_paths:
                raise ValueError(f"duplicate entry path {norm_path!r} in skill {name!r}")
            seen_paths.add(norm_path)

            if prev_path is not None and norm_path < prev_path:
                raise ValueError(
                    f"entries in skill {name!r} are not sorted: {prev_path!r} before {norm_path!r}"
                )
            prev_path = norm_path

            entry_type = entry_raw.get("type")
            if entry_type not in ("file", "directory"):
                raise ValueError(
                    f"invalid entry type {entry_type!r} for path {norm_path!r} in skill {name!r}"
                )

            if entry_type == "file":
                sha256 = entry_raw.get("sha256")
                if not isinstance(sha256, str) or not _SHA256_HEX_REGEX.match(sha256):
                    raise ValueError(
                        f"invalid or missing sha256 for file entry {norm_path!r} in skill {name!r}"
                    )
                entries.append(ManifestEntry(path=norm_path, type="file", sha256=sha256))
            else:
                if "sha256" in entry_raw:
                    raise ValueError(
                        f"directory entry {norm_path!r} must not have sha256 in skill {name!r}"
                    )
                entries.append(ManifestEntry(path=norm_path, type="directory"))

        skills[name] = SkillManifestEntry(
            name=name,
            target=target,
            entries=tuple(entries),
        )

    return SkillManifest(format=manifest_format, version=version, skills=skills)


def serialize_manifest(manifest: SkillManifest) -> str:
    return manifest.to_json()


def compare_skill_inventory(
    manifest_entries: tuple[ManifestEntry, ...],
    target_entries: tuple[ManifestEntry, ...],
) -> bool:
    """Return True if target inventory matches manifest entries exactly."""
    return manifest_entries == target_entries
