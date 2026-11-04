"""Shared marker, block, and content operations for AGENTS.md."""

from dataclasses import dataclass
import difflib
from pathlib import Path

from common.identity import (
    CANONICAL_IDENTITY,
    LEGACY_IDENTITY,
    InstallationIdentity,
)

BEGIN = CANONICAL_IDENTITY.begin_marker
END = CANONICAL_IDENTITY.end_marker


@dataclass(frozen=True)
class ManagedBlockClassification:
    kind: str  # "none", "canonical", "legacy"
    identity: InstallationIdentity | None
    begin_index: int
    end_index: int  # exclusive end index in existing string


def _find_markers(content: str, identity: InstallationIdentity) -> tuple[int, int]:
    """Return (start, end) indices of identity's managed block.

    Raises ValueError on malformed markers for this identity.
    Returns (-1, -1) if identity's markers are absent.
    """
    begin_str = identity.begin_marker
    end_str = identity.end_marker
    begin_count = content.count(begin_str)
    end_count = content.count(end_str)

    if begin_count == 0 and end_count == 0:
        return -1, -1

    if begin_count != end_count or begin_count > 1 or (
        begin_count == 1 and content.index(end_str) < content.index(begin_str)
    ):
        raise ValueError(f"AGENTS.md has incomplete or duplicate {identity.marker_slug} markers")

    start = content.index(begin_str)
    end = content.index(end_str, start) + len(end_str)
    return start, end


def classify_managed_block(content: str) -> ManagedBlockClassification:
    """Classify the managed block in content across canonical and legacy identities.

    Raises ValueError if markers are malformed, or if both canonical and legacy blocks exist,
    or if markers are nested/overlapping.
    """
    canon_start, canon_end = _find_markers(content, CANONICAL_IDENTITY)
    legacy_start, legacy_end = _find_markers(content, LEGACY_IDENTITY)

    if canon_start != -1 and legacy_start != -1:
        raise ValueError(
            "AGENTS.md contains both canonical (jolly-roger-skills) and legacy (agent-toolkit) markers"
        )

    if canon_start != -1:
        return ManagedBlockClassification(
            kind="canonical",
            identity=CANONICAL_IDENTITY,
            begin_index=canon_start,
            end_index=canon_end,
        )

    if legacy_start != -1:
        return ManagedBlockClassification(
            kind="legacy",
            identity=LEGACY_IDENTITY,
            begin_index=legacy_start,
            end_index=legacy_end,
        )

    return ManagedBlockClassification(
        kind="none",
        identity=None,
        begin_index=-1,
        end_index=-1,
    )


def validate_markers(existing: str) -> None:
    """Validate that existing AGENTS.md has well-formed markers for both identities."""
    classify_managed_block(existing)


def managed_block(repository_root: Path, identity: InstallationIdentity = CANONICAL_IDENTITY) -> str:
    """Return the managed block with content from repository_root / AGENTS.md."""
    source = (repository_root / "AGENTS.md").read_text(encoding="utf-8").strip()
    return f"{identity.begin_marker}\n{source}\n{identity.end_marker}\n"


def updated_content(
    existing: str,
    block: str,
    target_identity: InstallationIdentity = CANONICAL_IDENTITY,
) -> str:
    """Return AGENTS.md content with the managed block inserted or replaced.

    Ensures block is a complete well-formed managed block for target_identity,
    with no nested, duplicate, opposite-identity, or dual-identity markers.
    """
    block_class = classify_managed_block(block)
    expected_kind = "canonical" if target_identity == CANONICAL_IDENTITY else "legacy"
    if block_class.kind != expected_kind or block_class.identity != target_identity:
        raise ValueError(
            f"supplied block must be a valid {target_identity.marker_slug} managed block"
        )
    # Ensure block contains no trailing/leading content outside its markers
    if block[:block_class.begin_index].strip() or block[block_class.end_index:].strip():
        raise ValueError(
            f"supplied block contains content outside {target_identity.marker_slug} markers"
        )

    classification = classify_managed_block(existing)

    if classification.kind == "none":
        return f"{existing.rstrip()}\n\n{block}" if existing.strip() else block

    # Replace existing managed block (whether canonical or legacy) with block
    start = classification.begin_index
    end = classification.end_index
    return existing[:start] + block.rstrip("\n") + existing[end:]


def strip_boundary_blank_lines(prefix: str, suffix: str) -> str:
    """Combine retained prefix and suffix around a removed managed block.

    Preserves spaces and tabs on project-authored nonblank lines.
    """
    prefix_lines = prefix.splitlines(keepends=True)
    while prefix_lines and not prefix_lines[-1].strip():
        prefix_lines.pop()

    suffix_lines = suffix.splitlines(keepends=True)
    while suffix_lines and not suffix_lines[0].strip():
        suffix_lines.pop(0)

    if not prefix_lines and not suffix_lines:
        return ""

    if prefix_lines and not suffix_lines:
        prefix_clean = "".join(prefix_lines[:-1]) + prefix_lines[-1].rstrip("\r\n")
        return prefix_clean + "\n"

    if not prefix_lines and suffix_lines:
        return "".join(suffix_lines)

    prefix_clean = "".join(prefix_lines[:-1]) + prefix_lines[-1].rstrip("\r\n")
    suffix_clean = "".join(suffix_lines)
    return f"{prefix_clean}\n\n{suffix_clean}"


def removed_content(existing: str) -> str:
    """Return AGENTS.md content without the validated managed block (canonical or legacy)."""
    classification = classify_managed_block(existing)
    if classification.kind == "none":
        return existing

    prefix = existing[: classification.begin_index]
    suffix = existing[classification.end_index :]
    return strip_boundary_blank_lines(prefix, suffix)


def diff_content(before: str, after: str, target: Path) -> list[str]:
    """Return unified diff lines comparing before and after content for target."""
    return list(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{target} (current)",
            tofile=f"{target} (proposed)",
        )
    )
