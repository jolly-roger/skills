import os
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.skill_files import (
    discover_toolkit_skills,
    hash_file_sha256,
    inspect_source_skill,
    inspect_target_skill,
    is_proven_current_checkout_link,
    stage_skill_copy,
)


class SkillFilesTests(unittest.TestCase):
    def test_inspect_valid_source_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "my-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("info", encoding="utf-8")
            ref_dir = skill_dir / "references"
            ref_dir.mkdir()
            (ref_dir / "guide.md").write_text("guide", encoding="utf-8")

            snapshot = inspect_source_skill(skill_dir)
            self.assertEqual(snapshot.name, "my-skill")
            paths = [e.path for e in snapshot.entries]
            self.assertEqual(paths, ["SKILL.md", "references", "references/guide.md"])

    def test_reject_symlink_in_source_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "link-skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("info", encoding="utf-8")
            target_file = Path(tmpdir) / "target.txt"
            target_file.write_text("secret", encoding="utf-8")
            (skill_dir / "sym.txt").symlink_to(target_file)

            with self.assertRaises(ValueError) as ctx:
                inspect_source_skill(skill_dir)
            self.assertIn("symlinks are not permitted", str(ctx.exception))

    def test_reject_source_missing_skill_md(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir) / "no-skill-md"
            skill_dir.mkdir()
            (skill_dir / "other.txt").write_text("other", encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                inspect_source_skill(skill_dir)
            self.assertIn("must contain a regular SKILL.md file", str(ctx.exception))

    def test_inspect_target_skill(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            target_dir = Path(tmpdir) / "sample"
            target_dir.mkdir()
            (target_dir / "SKILL.md").write_text("data", encoding="utf-8")

            snap = inspect_target_skill(target_dir)
            self.assertTrue(snap.exists)
            self.assertTrue(snap.is_dir)
            self.assertFalse(snap.is_symlink)
            self.assertEqual(len(snap.entries), 1)
            self.assertEqual(snap.entries[0].path, "SKILL.md")

    def test_is_proven_current_checkout_link(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            toolkit_root = Path(tmpdir) / "toolkit"
            skills_dir = toolkit_root / "skills"
            (skills_dir / "test-skill").mkdir(parents=True)

            workspace = Path(tmpdir) / "workspace"
            link = workspace / ".agents" / "skills" / "test-skill"
            link.parent.mkdir(parents=True)
            rel_path = os.path.relpath(skills_dir / "test-skill", link.parent)
            link.symlink_to(rel_path)

            self.assertTrue(
                is_proven_current_checkout_link(link, rel_path, toolkit_root, "test-skill")
            )
            self.assertFalse(
                is_proven_current_checkout_link(link, rel_path, Path("/other/toolkit"), "test-skill")
            )


if __name__ == "__main__":
    unittest.main()
