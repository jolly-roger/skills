"""Shared marker, block, and content operations for AGENTS.md."""

import difflib
from pathlib import Path


BEGIN = "<!-- agent-toolkit:begin -->"
END = "<!-- agent-toolkit:end -->"


def validate_markers(existing: str) -> None:
    """Validate that agent-toolkit markers in existing are well-formed.

    Raises ValueError if markers are incomplete, reversed, or duplicated.
    """
    begin_count = existing.count(BEGIN)
    end_count = existing.count(END)
    if begin_count != end_count or begin_count > 1 or (
        begin_count == 1 and existing.index(END) < existing.index(BEGIN)
    ):
        raise ValueError("AGENTS.md has incomplete or duplicate agent-toolkit markers")


def managed_block(toolkit_root: Path) -> str:
    """Return the managed block with content from the toolkit root's AGENTS.md."""
    source = (toolkit_root / "AGENTS.md").read_text(encoding="utf-8").strip()
    return f"{BEGIN}\n{source}\n{END}\n"


def updated_content(existing: str, block: str) -> str:
    """Return AGENTS.md content with the managed block inserted or replaced."""
    validate_markers(existing)
    begin_count = existing.count(BEGIN)
    if begin_count == 0:
        return f"{existing.rstrip()}\n\n{block}" if existing.strip() else block

    start = existing.index(BEGIN)
    end = existing.index(END, start) + len(END)
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
    """Return AGENTS.md content without the validated managed block."""
    validate_markers(existing)
    if BEGIN not in existing:
        return existing

    start = existing.index(BEGIN)
    end = existing.index(END, start) + len(END)
    prefix = existing[:start]
    suffix = existing[end:]

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
