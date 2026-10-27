import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
INSTALLER = TOOLS_DIR / "install.py"
UNINSTALLER = TOOLS_DIR / "uninstall.py"
TOOLKIT_ROOT = TOOLS_DIR.parent


class UninstallerTests(unittest.TestCase):
    def test_install_and_uninstall_preserves_project_content(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Project rules\n\nKeep this rule.\n", encoding="utf-8")

            # Install
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )

            # Uninstall
            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )

            self.assertIn("Uninstalled agent-toolkit", result.stdout)
            self.assertEqual(target.read_text(encoding="utf-8"), "# Project rules\n\nKeep this rule.\n")
            # All owned links and .agents directories removed since they became empty
            self.assertFalse((Path(directory) / ".agents").exists())

    def test_removes_agents_md_when_managed_block_was_only_content(self):
        with tempfile.TemporaryDirectory() as directory:
            # Install into empty workspace (creates AGENTS.md with only managed block)
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )
            target = Path(directory) / "AGENTS.md"
            self.assertTrue(target.exists())

            # Uninstall
            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )

            self.assertIn("Uninstalled agent-toolkit", result.stdout)
            self.assertFalse(target.exists())
            self.assertFalse((Path(directory) / ".agents").exists())

    def test_self_uninstallation_preserves_authoritative_agents_md(self):
        with tempfile.TemporaryDirectory() as directory:
            toolkit = Path(directory) / "agent-toolkit"
            toolkit.mkdir()
            tools_dir = toolkit / "tools"
            tools_dir.mkdir()
            shutil.copy2(INSTALLER, tools_dir / "install.py")
            shutil.copy2(UNINSTALLER, tools_dir / "uninstall.py")
            shutil.copytree(TOOLS_DIR / "common", tools_dir / "common")
            shutil.copy2(TOOLKIT_ROOT / "AGENTS.md", toolkit / "AGENTS.md")
            shutil.copytree(TOOLKIT_ROOT / "skills", toolkit / "skills")

            # Self-install
            subprocess.run(
                [sys.executable, str(tools_dir / "install.py"), "--workspace", str(toolkit), "--yes"],
                check=True, capture_output=True, text=True,
            )
            authoritative_content = (toolkit / "AGENTS.md").read_bytes()
            self.assertTrue((toolkit / ".agents" / "skills").exists())

            # Self-uninstall
            result = subprocess.run(
                [sys.executable, str(tools_dir / "uninstall.py"), "--workspace", str(toolkit), "--yes"],
                check=True, capture_output=True, text=True,
            )

            self.assertIn("Uninstalled agent-toolkit", result.stdout)
            # Authoritative AGENTS.md unchanged
            self.assertEqual((toolkit / "AGENTS.md").read_bytes(), authoritative_content)
            # Skill links removed
            self.assertFalse((toolkit / ".agents").exists())

    def test_removes_dangling_owned_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            ws = Path(directory).resolve()
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            # Dangling link to removed skill in toolkit_root
            dangling = skills_dir / "removed-skill"
            rel_target = os.path.relpath((TOOLKIT_ROOT / "skills" / "removed-skill").resolve(), dangling.parent)
            dangling.symlink_to(rel_target, target_is_directory=True)

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )

            self.assertIn("Uninstalled agent-toolkit", result.stdout)
            self.assertFalse(dangling.exists(follow_symlinks=False))
            self.assertFalse((ws / ".agents").exists())

    def test_preserves_regular_skill_directory_and_foreign_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            ws = Path(directory).resolve()
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            # Owned link
            owned = skills_dir / "review"
            owned.symlink_to(
                os.path.relpath((TOOLKIT_ROOT / "skills" / "review").resolve(), owned.parent),
                target_is_directory=True,
            )

            # Local regular directory colliding in name
            local_dir = skills_dir / "merge-master"
            local_dir.mkdir()
            (local_dir / "SKILL.md").write_text("Local", encoding="utf-8")

            # Foreign symlink colliding in name
            foreign_dir = ws / "foreign_skills"
            foreign_dir.mkdir()
            foreign_link = skills_dir / "pragmatic-functional-programming"
            foreign_link.symlink_to(
                os.path.relpath(foreign_dir, foreign_link.parent),
                target_is_directory=True,
            )

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )

            self.assertIn("Uninstalled agent-toolkit", result.stdout)
            self.assertFalse(owned.exists(follow_symlinks=False))
            self.assertTrue(local_dir.is_dir())
            self.assertTrue(foreign_link.is_symlink())
            self.assertTrue(skills_dir.exists())

    def test_preserves_unrelated_entries_under_agents(self):
        with tempfile.TemporaryDirectory() as directory:
            ws = Path(directory)
            # Install toolkit
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )

            # Add custom file under .agents
            custom_file = ws / ".agents" / "custom_config.json"
            custom_file.write_text("{}", encoding="utf-8")

            # Uninstall
            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )

            self.assertIn("Uninstalled agent-toolkit", result.stdout)
            self.assertTrue(custom_file.is_file())
            self.assertTrue((ws / ".agents").is_dir())
            # .agents/skills should have been removed because it was empty
            self.assertFalse((ws / ".agents" / "skills").exists())

    def test_dry_run_makes_no_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--dry-run"],
                check=True, capture_output=True, text=True,
            )

            self.assertIn("Remove", result.stdout)
            self.assertIn("Remove skill link:", result.stdout)
            self.assertTrue((Path(directory) / "AGENTS.md").exists())
            self.assertTrue((Path(directory) / ".agents" / "skills").exists())

    def test_interactive_decline_makes_no_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory],
                input="n\n", check=True, capture_output=True, text=True,
            )

            self.assertIn("No changes made.", result.stdout)
            self.assertTrue((Path(directory) / "AGENTS.md").exists())
            self.assertTrue((Path(directory) / ".agents" / "skills").exists())

    def test_repeated_run_reports_already_uninstalled(self):
        with tempfile.TemporaryDirectory() as directory:
            # Workspace with no toolkit artifacts
            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("Already uninstalled", result.stdout)

    def test_reject_nonexistent_workspace(self):
        result = subprocess.run(
            [sys.executable, str(UNINSTALLER), "--workspace", "/path/that/does/not/exist", "--yes"],
            capture_output=True, text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a directory", result.stderr)

    def test_reject_symlinked_agents_md(self):
        with tempfile.TemporaryDirectory() as directory:
            ws = Path(directory)
            outside = ws / "outside"
            outside.mkdir()
            outside_agents = outside / "AGENTS.md"
            outside_agents.write_text("outside", encoding="utf-8")

            link_agents = ws / "AGENTS.md"
            link_agents.symlink_to(outside_agents)

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to operate on symlink", result.stderr)

    def test_reject_symlinked_agents_and_skills_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            ws = Path(directory)
            other = ws / "other"
            other.mkdir()

            # Symlink .agents
            (ws / ".agents").symlink_to(other, target_is_directory=True)
            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to uninstall through a symlinked .agents directory", result.stderr)

            # Symlink .agents/skills
            (ws / ".agents").unlink()
            (ws / ".agents").mkdir()
            (ws / ".agents" / "skills").symlink_to(other, target_is_directory=True)
            result2 = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result2.returncode, 0)
            self.assertIn("refusing to uninstall through a symlinked .agents directory", result2.stderr)

    def test_reject_malformed_markers_before_removing_links(self):
        with tempfile.TemporaryDirectory() as directory:
            ws = Path(directory)
            # Create owned skill link
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)
            link = skills_dir / "review"
            link.symlink_to(os.path.relpath(TOOLKIT_ROOT / "skills" / "review", link.parent), target_is_directory=True)

            # Malformed AGENTS.md (lone begin marker)
            target = ws / "AGENTS.md"
            target.write_text("# Project\n<!-- agent-toolkit:begin -->\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("incomplete or duplicate", result.stderr)
            # Link must still exist (no mutations occurred)
            self.assertTrue(link.is_symlink())

    def test_install_uninstall_install_cycle_succeeds(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Project rules\n", encoding="utf-8")

            # 1. Install
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )
            # 2. Uninstall
            subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(target.read_text(encoding="utf-8"), "# Project rules\n")

            # 3. Re-install
            result = subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("Installed agent-toolkit", result.stdout)
            self.assertIn("<!-- agent-toolkit:begin -->", target.read_text(encoding="utf-8"))

    def test_runs_by_absolute_path_from_foreign_working_directory(self):
        with tempfile.TemporaryDirectory() as temp_cwd, tempfile.TemporaryDirectory() as ws:
            target = Path(ws) / "AGENTS.md"
            target.write_text("# Base rules\n", encoding="utf-8")

            # Run install from foreign cwd
            subprocess.run(
                [sys.executable, str(INSTALLER.resolve()), "--workspace", ws, "--yes"],
                check=True, cwd=temp_cwd, capture_output=True, text=True,
            )
            self.assertIn("<!-- agent-toolkit:begin -->", target.read_text(encoding="utf-8"))

            # Run uninstall from foreign cwd
            subprocess.run(
                [sys.executable, str(UNINSTALLER.resolve()), "--workspace", ws, "--yes"],
                check=True, cwd=temp_cwd, capture_output=True, text=True,
            )
            self.assertNotIn("<!-- agent-toolkit:begin -->", target.read_text(encoding="utf-8"))

    def test_rollback_restores_links_on_later_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            ws = Path(directory).resolve()
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            original_mode = ws.stat().st_mode
            ws.chmod(0o555)
            try:
                result = subprocess.run(
                    [sys.executable, str(UNINSTALLER), "--workspace", str(ws), "--yes"],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                link = ws / ".agents" / "skills" / "review"
                self.assertTrue(link.is_symlink())
            finally:
                ws.chmod(original_mode)


if __name__ == "__main__":
    unittest.main()
