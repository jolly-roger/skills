"""Canonical and legacy installation identity definitions and marker generation."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstallationIdentity:
    namespace: str
    marker_slug: str
    manifest_filename: str
    manifest_format: str

    @property
    def begin_marker(self) -> str:
        return f"<!-- {self.marker_slug}:begin -->"

    @property
    def end_marker(self) -> str:
        return f"<!-- {self.marker_slug}:end -->"

    @property
    def manifest_relative_path(self) -> Path:
        return Path(".agents") / self.manifest_filename


CANONICAL_IDENTITY = InstallationIdentity(
    namespace="jolly-roger.skills",
    marker_slug="jolly-roger-skills",
    manifest_filename="jolly-roger-skills-manifest.json",
    manifest_format="jolly-roger.skills",
)

LEGACY_IDENTITY = InstallationIdentity(
    namespace="agent-toolkit",
    marker_slug="agent-toolkit",
    manifest_filename="agent-toolkit-manifest.json",
    manifest_format="agent-toolkit.skills",
)
