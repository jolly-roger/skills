import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.agents_file import BEGIN, END
from common.skill_manifest import (
    FORMAT_NAME,
    CURRENT_VERSION,
    MANIFEST_RELATIVE_PATH,
    parse_manifest,
)

INSTALLER = TOOLS_DIR / "install.py"
TOOLKIT_ROOT = TOOLS_DIR.parent


class InstallerTests(unittest.TestCase):
    def test_install_copies_skills_and_creates_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Project rules\n\nKeep this rule.\n", encoding="utf-8")
            command = [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"]

            first = subprocess.run(command, capture_output=True, text=True, check=True)
            installed = target.read_text(encoding="utf-8")
            manifest_file = Path(directory) / MANIFEST_RELATIVE_PATH

            self.assertIn("Installed agent-toolkit", first.stdout)
            self.assertIn("# Project rules\n\nKeep this rule.", installed)
            self.assertIn(BEGIN, installed)
            self.assertTrue(manifest_file.is_file())

            # Verify manifest content
            manifest = parse_manifest(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest.format, FORMAT_NAME)
            self.assertEqual(manifest.version, CURRENT_VERSION)

            for name in (
                "review", "review-diff", "merge-master",
                "pragmatic-functional-programming",
            ):
                skill_dir = Path(directory) / ".agents" / "skills" / name
                self.assertTrue(skill_dir.is_dir())
                self.assertFalse(skill_dir.is_symlink())
                self.assertTrue((skill_dir / "SKILL.md").is_file())
                self.assertIn(name, manifest.skills)

            # Test repeatability
            second = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertEqual(installed, target.read_text(encoding="utf-8"))
            self.assertIn("Already up to date", second.stdout)

    def test_update_exact_managed_copy_when_source_changes(self):
        with tempfile.TemporaryDirectory() as fake_toolkit:
            # Setup a minimal toolkit
            src_skills = Path(fake_toolkit) / "skills"
            test_skill = src_skills / "test-skill"
            test_skill.mkdir(parents=True)
            (test_skill / "SKILL.md").write_text("version 1", encoding="utf-8")
            (Path(fake_toolkit) / "AGENTS.md").write_text("Shared rules", encoding="utf-8")
            shutil.copytree(TOOLS_DIR, Path(fake_toolkit) / "tools")

            installer_script = Path(fake_toolkit) / "tools" / "install.py"

            with tempfile.TemporaryDirectory() as workspace:
                # First install
                cmd = [sys.executable, str(installer_script), "--workspace", workspace, "--yes"]
                subprocess.run(cmd, check=True, capture_output=True, text=True)

                installed_skill_md = Path(workspace) / ".agents" / "skills" / "test-skill" / "SKILL.md"
                self.assertEqual(installed_skill_md.read_text(encoding="utf-8"), "version 1")

                # Change source
                (test_skill / "SKILL.md").write_text("version 2", encoding="utf-8")

                # Re-run install
                res = subprocess.run(cmd, check=True, capture_output=True, text=True)
                self.assertIn("Installed agent-toolkit", res.stdout)
                self.assertEqual(installed_skill_md.read_text(encoding="utf-8"), "version 2")

    def test_refuse_to_overwrite_modified_managed_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            cmd = [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"]
            subprocess.run(cmd, check=True, capture_output=True, text=True)

            # Modify an installed skill
            review_md = Path(directory) / ".agents" / "skills" / "review" / "SKILL.md"
            review_md.write_text("local modification", encoding="utf-8")

            # Try to install again
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("locally modified managed skill copy", res.stderr)

    def test_refuse_unmanaged_skill_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            unmanaged = Path(directory) / ".agents" / "skills" / "review"
            unmanaged.mkdir(parents=True)
            (unmanaged / "SKILL.md").write_text("my own review", encoding="utf-8")

            cmd = [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("unmanaged skill directory", res.stderr)

    def test_replace_proven_current_checkout_legacy_link(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace_dir = Path(directory).resolve()
            legacy_link = workspace_dir / ".agents" / "skills" / "review"
            legacy_link.parent.mkdir(parents=True)
            target = (TOOLKIT_ROOT / "skills" / "review").resolve()
            legacy_link.symlink_to(os.path.relpath(target, legacy_link.parent))

            cmd = [sys.executable, str(INSTALLER), "--workspace", str(workspace_dir), "--yes"]
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.assertIn("Installed agent-toolkit", res.stdout)

            # Link should now be a real directory
            self.assertTrue(legacy_link.is_dir())
            self.assertFalse(legacy_link.is_symlink())

    def test_dry_run_makes_no_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            cmd = [sys.executable, str(INSTALLER), "--workspace", directory, "--dry-run"]
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.assertFalse((Path(directory) / ".agents").exists())
            self.assertFalse((Path(directory) / "AGENTS.md").exists())

    def test_self_install_leaves_agents_md_unchanged(self):
        with tempfile.TemporaryDirectory() as fake_repo:
            (Path(fake_repo) / "AGENTS.md").write_text("Authoritative rules", encoding="utf-8")
            src_skills = Path(fake_repo) / "skills"
            (src_skills / "dummy").mkdir(parents=True)
            (src_skills / "dummy" / "SKILL.md").write_text("data", encoding="utf-8")
            shutil.copytree(TOOLS_DIR, Path(fake_repo) / "tools")

            cmd = [sys.executable, str(Path(fake_repo) / "tools" / "install.py"), "--workspace", fake_repo, "--yes"]
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.assertIn("Installed agent-toolkit", res.stdout)
            self.assertEqual((Path(fake_repo) / "AGENTS.md").read_text(encoding="utf-8"), "Authoritative rules")
            self.assertTrue((Path(fake_repo) / ".agents" / "skills" / "dummy").is_dir())


if __name__ == "__main__":
    unittest.main()
