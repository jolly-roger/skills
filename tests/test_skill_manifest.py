import json
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.identity import CANONICAL_IDENTITY, LEGACY_IDENTITY
from common.skill_manifest import (
    FORMAT_NAME,
    CURRENT_VERSION,
    ManifestEntry,
    SkillManifest,
    SkillManifestEntry,
    compare_skill_inventory,
    create_manifest,
    inspect_workspace_manifests,
    migrate_manifest_to_canonical,
    parse_manifest,
    serialize_manifest,
    validate_entry_relative_path,
    validate_skill_name,
)


class SkillManifestTests(unittest.TestCase):
    def test_validate_skill_name(self):
        validate_skill_name("valid-skill")
        validate_skill_name("review_123")
        with self.assertRaises(ValueError):
            validate_skill_name("")
        with self.assertRaises(ValueError):
            validate_skill_name(".")
        with self.assertRaises(ValueError):
            validate_skill_name("..")
        with self.assertRaises(ValueError):
            validate_skill_name("sub/dir")
        with self.assertRaises(ValueError):
            validate_skill_name("sub\\dir")

    def test_validate_entry_relative_path(self):
        self.assertEqual(validate_entry_relative_path("SKILL.md"), "SKILL.md")
        self.assertEqual(validate_entry_relative_path("ref/doc.md"), "ref/doc.md")
        with self.assertRaises(ValueError):
            validate_entry_relative_path("")
        with self.assertRaises(ValueError):
            validate_entry_relative_path("/abs/path")
        with self.assertRaises(ValueError):
            validate_entry_relative_path("../escape")
        with self.assertRaises(ValueError):
            validate_entry_relative_path("foo/../escape")
        with self.assertRaises(ValueError):
            validate_entry_relative_path("foo\\bar")

    def test_deterministic_serialization_and_parsing(self):
        entries = (
            ManifestEntry(path="SKILL.md", type="file", sha256="a" * 64),
            ManifestEntry(path="ref", type="directory"),
            ManifestEntry(path="ref/guide.md", type="file", sha256="b" * 64),
        )
        skill_entry = SkillManifestEntry(name="sample", target="skills/sample", entries=entries)
        manifest = create_manifest({"sample": skill_entry})

        serialized = serialize_manifest(manifest)
        parsed = parse_manifest(serialized)

        self.assertEqual(parsed.format, CANONICAL_IDENTITY.manifest_format)
        self.assertEqual(parsed.version, CURRENT_VERSION)
        self.assertIn("sample", parsed.skills)
        self.assertEqual(parsed.skills["sample"].entries, entries)
        self.assertEqual(serialize_manifest(parsed), serialized)

    def test_legacy_manifest_parsing_and_migration(self):
        entries = (
            ManifestEntry(path="SKILL.md", type="file", sha256="a" * 64),
        )
        skill_entry = SkillManifestEntry(name="sample", target="skills/sample", entries=entries)
        legacy_manifest = create_manifest({"sample": skill_entry}, identity=LEGACY_IDENTITY)
        self.assertEqual(legacy_manifest.format, LEGACY_IDENTITY.manifest_format)

        serialized = serialize_manifest(legacy_manifest)
        parsed = parse_manifest(serialized)
        self.assertEqual(parsed.format, LEGACY_IDENTITY.manifest_format)

        migrated = migrate_manifest_to_canonical(parsed)
        self.assertEqual(migrated.format, CANONICAL_IDENTITY.manifest_format)
        self.assertEqual(migrated.skills["sample"].entries, entries)

    def test_inspect_workspace_manifests_dual_conflict(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            agents = ws / ".agents"
            agents.mkdir()
            (agents / CANONICAL_IDENTITY.manifest_filename).write_text(
                json.dumps({"format": CANONICAL_IDENTITY.manifest_format, "version": 1, "skills": {}}),
                encoding="utf-8",
            )
            (agents / LEGACY_IDENTITY.manifest_filename).write_text(
                json.dumps({"format": LEGACY_IDENTITY.manifest_format, "version": 1, "skills": {}}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError) as ctx:
                inspect_workspace_manifests(ws)
            self.assertIn("both canonical", str(ctx.exception))

    def test_inspect_workspace_manifests_symlink_rejection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            agents = ws / ".agents"
            agents.mkdir()
            target_manifest = ws / "custom-manifest.json"
            target_manifest.write_text("{}", encoding="utf-8")
            (agents / CANONICAL_IDENTITY.manifest_filename).symlink_to(target_manifest)

            with self.assertRaises(ValueError) as ctx:
                inspect_workspace_manifests(ws)
            self.assertIn("refusing to operate through a symlinked manifest path", str(ctx.exception))

    def test_inspect_workspace_manifests_directory_rejection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            agents = ws / ".agents"
            agents.mkdir()
            (agents / CANONICAL_IDENTITY.manifest_filename).mkdir()

            with self.assertRaises(ValueError) as ctx:
                inspect_workspace_manifests(ws)
            self.assertIn("not a regular file", str(ctx.exception))

    def test_reject_mismatched_filename_and_format_identities(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            agents = ws / ".agents"
            agents.mkdir()
            # Canonical filename with legacy format
            (agents / CANONICAL_IDENTITY.manifest_filename).write_text(
                json.dumps({"format": LEGACY_IDENTITY.manifest_format, "version": 1, "skills": {}}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError) as ctx:
                inspect_workspace_manifests(ws)
            self.assertIn("manifest format mismatch", str(ctx.exception))

        with tempfile.TemporaryDirectory() as tmpdir:
            ws = Path(tmpdir)
            agents = ws / ".agents"
            agents.mkdir()
            # Legacy filename with canonical format
            (agents / LEGACY_IDENTITY.manifest_filename).write_text(
                json.dumps({"format": CANONICAL_IDENTITY.manifest_format, "version": 1, "skills": {}}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError) as ctx:
                inspect_workspace_manifests(ws)
            self.assertIn("manifest format mismatch", str(ctx.exception))

    def test_reject_invalid_manifest(self):
        with self.assertRaises(ValueError):
            parse_manifest("{not json")
        with self.assertRaises(ValueError):
            parse_manifest(json.dumps({"format": "wrong", "version": 1, "skills": {}}))
        with self.assertRaises(ValueError):
            parse_manifest(json.dumps({"format": FORMAT_NAME, "version": 2, "skills": {}}))
        with self.assertRaises(ValueError):
            parse_manifest(json.dumps({"format": FORMAT_NAME, "version": 1, "skills": []}))
        # Invalid target
        with self.assertRaises(ValueError):
            parse_manifest(json.dumps({
                "format": FORMAT_NAME,
                "version": 1,
                "skills": {"foo": {"target": "wrong/target", "entries": []}}
            }))
        # Unsorted entries
        with self.assertRaises(ValueError):
            parse_manifest(json.dumps({
                "format": FORMAT_NAME,
                "version": 1,
                "skills": {
                    "foo": {
                        "target": "skills/foo",
                        "entries": [
                            {"path": "b.txt", "type": "file", "sha256": "0" * 64},
                            {"path": "a.txt", "type": "file", "sha256": "0" * 64},
                        ]
                    }
                }
            }))
        # Malformed hash
        with self.assertRaises(ValueError):
            parse_manifest(json.dumps({
                "format": FORMAT_NAME,
                "version": 1,
                "skills": {
                    "foo": {
                        "target": "skills/foo",
                        "entries": [
                            {"path": "a.txt", "type": "file", "sha256": "bad-hash"},
                        ]
                    }
                }
            }))


if __name__ == "__main__":
    unittest.main()
