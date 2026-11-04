import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.agents_file import BEGIN, END
from common.skill_manifest import MANIFEST_RELATIVE_PATH, parse_manifest

UNINSTALLER = TOOLS_DIR / "uninstall.py"
INSTALLER = TOOLS_DIR / "install.py"
TOOLKIT_ROOT = TOOLS_DIR.parent


class UninstallTests(unittest.TestCase):
    def test_uninstall_removes_exact_copies_manifest_and_managed_block(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Project rules\n\nKeep this rule.\n", encoding="utf-8")

            # First install
            subprocess.run([sys.executable, str(INSTALLER), "--workspace", directory, "--yes"], check=True)

            # Uninstall
            cmd = [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("Uninstalled agent-toolkit", res.stdout)

            # AGENTS.md preserved without managed block
            self.assertEqual(target.read_text(encoding="utf-8").strip(), "# Project rules\n\nKeep this rule.")

            # Manifest and skills removed
            self.assertFalse((Path(directory) / MANIFEST_RELATIVE_PATH).exists())
            self.assertFalse((Path(directory) / ".agents" / "skills").exists())

            # Repeat uninstall -> already uninstalled
            second = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("Already uninstalled", second.stdout)

    def test_uninstall_removes_agents_md_if_managed_block_was_only_content(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(INSTALLER), "--workspace", directory, "--yes"], check=True)
            subprocess.run([sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"], check=True)

            self.assertFalse((Path(directory) / "AGENTS.md").exists())

    def test_preserve_modified_managed_skill_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(INSTALLER), "--workspace", directory, "--yes"], check=True)

            # Modify a skill
            review_md = Path(directory) / ".agents" / "skills" / "review" / "SKILL.md"
            review_md.write_text("local modifications", encoding="utf-8")

            res = subprocess.run([sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"], capture_output=True, text=True, check=True)
            self.assertIn("preserving modified managed skill copy", res.stdout)
            self.assertTrue(review_md.is_file())

            # Manifest should be updated, keeping review
            manifest_file = Path(directory) / MANIFEST_RELATIVE_PATH
            self.assertTrue(manifest_file.is_file())
            manifest = parse_manifest(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(list(manifest.skills.keys()), ["review"])

    def test_clean_stale_manifest_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(INSTALLER), "--workspace", directory, "--yes"], check=True)

            # Manually delete one skill directory
            shutil.rmtree(Path(directory) / ".agents" / "skills" / "review")

            res = subprocess.run([sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"], capture_output=True, text=True, check=True)
            self.assertIn("Clean stale manifest entry", res.stdout)
            self.assertFalse((Path(directory) / MANIFEST_RELATIVE_PATH).exists())

    def test_preserve_unmanaged_directories_and_foreign_links(self):
        with tempfile.TemporaryDirectory() as directory:
            unmanaged = Path(directory) / ".agents" / "skills" / "my-skill"
            unmanaged.mkdir(parents=True)
            (unmanaged / "SKILL.md").write_text("my skill", encoding="utf-8")

            foreign_link = Path(directory) / ".agents" / "skills" / "foreign"
            foreign_link.symlink_to("/tmp/nonexistent_target")

            res = subprocess.run([sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"], capture_output=True, text=True, check=True)
            self.assertTrue(unmanaged.is_dir())
            self.assertTrue(foreign_link.is_symlink())

    def test_remove_proven_current_checkout_legacy_link(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace_dir = Path(directory)
            legacy_link = workspace_dir / ".agents" / "skills" / "review"
            legacy_link.parent.mkdir(parents=True)
            target = (TOOLKIT_ROOT / "skills" / "review").resolve()
            legacy_link.symlink_to(os.path.relpath(target, legacy_link.parent))

            res = subprocess.run([sys.executable, str(UNINSTALLER), "--workspace", str(workspace_dir), "--yes"], capture_output=True, text=True, check=True)
            self.assertIn("Remove legacy skill link", res.stdout)
            self.assertFalse(legacy_link.exists())

    def test_self_uninstallation_preserves_authoritative_agents_md(self):
        with tempfile.TemporaryDirectory() as fake_repo:
            (Path(fake_repo) / "AGENTS.md").write_text("Authoritative rules", encoding="utf-8")
            src_skills = Path(fake_repo) / "skills"
            (src_skills / "dummy").mkdir(parents=True)
            (src_skills / "dummy" / "SKILL.md").write_text("data", encoding="utf-8")
            shutil.copytree(TOOLS_DIR, Path(fake_repo) / "tools")

            installer = Path(fake_repo) / "tools" / "install.py"
            uninstaller = Path(fake_repo) / "tools" / "uninstall.py"

            subprocess.run([sys.executable, str(installer), "--workspace", fake_repo, "--yes"], check=True)
            subprocess.run([sys.executable, str(uninstaller), "--workspace", fake_repo, "--yes"], check=True)

            self.assertEqual((Path(fake_repo) / "AGENTS.md").read_text(encoding="utf-8"), "Authoritative rules")
            self.assertFalse((Path(fake_repo) / ".agents" / "skills" / "dummy").exists())


if __name__ == "__main__":
    unittest.main()
