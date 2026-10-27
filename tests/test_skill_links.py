import os
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.skill_links import (
    OwnedSkillLink,
    discover_toolkit_skills,
    find_owned_skill_links,
    install_links,
    planned_install_links,
    restore_skill_links,
    validate_agents_directory,
)


class SkillLinksTests(unittest.TestCase):
    def test_discover_toolkit_skills(self):
        with tempfile.TemporaryDirectory() as td:
            toolkit = Path(td)
            skills = toolkit / "skills"
            skills.mkdir()
            (skills / "valid-skill").mkdir()
            (skills / "valid-skill" / "SKILL.md").write_text("desc", encoding="utf-8")
            (skills / "invalid-skill").mkdir()  # No SKILL.md
            (skills / "file-not-dir.txt").write_text("hello", encoding="utf-8")

            discovered = discover_toolkit_skills(toolkit)
            self.assertEqual([s.name for s in discovered], ["valid-skill"])

    def test_validate_agents_directory_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            target = workspace / "other_dir"
            target.mkdir()

            # Symlinked .agents
            agents_link = workspace / ".agents"
            agents_link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(ValueError) as ctx:
                validate_agents_directory(workspace)
            self.assertIn("refusing to operate through a symlinked .agents directory", str(ctx.exception))

            # Symlinked .agents/skills
            agents_link.unlink()
            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            skills_link = agents_dir / "skills"
            skills_link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(ValueError) as ctx:
                validate_agents_directory(workspace)
            self.assertIn("refusing to operate through a symlinked .agents directory", str(ctx.exception))

    def test_validate_agents_directory_rejects_non_directories(self):
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td)
            agents_file = workspace / ".agents"
            agents_file.write_text("not a dir", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                validate_agents_directory(workspace)
            self.assertIn("agents path is not a directory", str(ctx.exception))

    def test_find_owned_skill_links_identifies_owned_and_dangling_links(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            toolkit = base / "toolkit"
            toolkit_skills = toolkit / "skills"
            toolkit_skills.mkdir(parents=True)
            (toolkit_skills / "skill-a").mkdir()
            (toolkit_skills / "skill-a" / "SKILL.md").write_text("a", encoding="utf-8")

            foreign = base / "foreign" / "skills"
            foreign.mkdir(parents=True)
            (foreign / "skill-foreign").mkdir()

            workspace = base / "workspace"
            ws_skills = workspace / ".agents" / "skills"
            ws_skills.mkdir(parents=True)

            # 1. Owned active link
            link_a = ws_skills / "skill-a"
            link_a.symlink_to(os.path.relpath(toolkit_skills / "skill-a", link_a.parent), target_is_directory=True)

            # 2. Owned dangling link (target does not exist in toolkit_skills)
            link_dangling = ws_skills / "skill-removed"
            link_dangling.symlink_to(
                os.path.relpath(toolkit_skills / "skill-removed", link_dangling.parent),
                target_is_directory=True,
            )

            # 3. Foreign symlink
            link_foreign = ws_skills / "skill-foreign"
            link_foreign.symlink_to(
                os.path.relpath(foreign / "skill-foreign", link_foreign.parent),
                target_is_directory=True,
            )

            # 4. Regular directory (not a symlink)
            local_dir = ws_skills / "local-skill"
            local_dir.mkdir()

            # 5. Regular file
            local_file = ws_skills / "README.txt"
            local_file.write_text("note", encoding="utf-8")

            owned = find_owned_skill_links(toolkit, workspace)
            owned_names = [o.path.name for o in owned]
            self.assertEqual(sorted(owned_names), ["skill-a", "skill-removed"])

            # Verify raw_target is preserved
            for item in owned:
                self.assertEqual(item.raw_target, os.readlink(item.path))

    def test_restore_skill_links_recreates_symlinks(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            skills_dir = base / ".agents" / "skills"
            skills_dir.mkdir(parents=True)
            link_path = skills_dir / "my-skill"
            raw_target = "../../toolkit/skills/my-skill"

            # Create and remove link
            link_path.symlink_to(raw_target, target_is_directory=True)
            self.assertTrue(link_path.is_symlink())
            link_path.unlink()
            self.assertFalse(link_path.exists())

            # Restore
            failures = restore_skill_links([OwnedSkillLink(path=link_path, raw_target=raw_target)])
            self.assertEqual(failures, [])
            self.assertTrue(link_path.is_symlink())
            self.assertEqual(os.readlink(link_path), raw_target)


if __name__ == "__main__":
    unittest.main()
