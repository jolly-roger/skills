import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add tools to sys.path for direct imports
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.agents_file import BEGIN, END, updated_content


INSTALLER = TOOLS_DIR / "install.py"
TOOLKIT_ROOT = TOOLS_DIR.parent


class InstallerTests(unittest.TestCase):
    def test_install_preserves_project_rules_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Project rules\n\nKeep this rule.\n", encoding="utf-8")
            command = [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"]

            first = subprocess.run(command, capture_output=True, text=True, check=True)
            installed = target.read_text(encoding="utf-8")
            second = subprocess.run(command, capture_output=True, text=True, check=True)

            self.assertIn("Installed agent-toolkit", first.stdout)
            self.assertIn("# Project rules\n\nKeep this rule.", installed)
            self.assertIn("<!-- agent-toolkit:begin -->", installed)
            self.assertIn("## Git Safety", installed)
            for name in (
                "review", "review-diff", "merge-master",
                "pragmatic-functional-programming",
            ):
                link = Path(directory) / ".agents" / "skills" / name
                self.assertTrue(link.is_symlink())
                self.assertEqual(link.resolve(), (TOOLKIT_ROOT / "skills" / name).resolve())
                self.assertTrue((link / "SKILL.md").is_file())
            self.assertEqual(installed, target.read_text(encoding="utf-8"))
            self.assertIn("Already up to date", second.stdout)

    def test_refuses_malformed_existing_markers(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            original = "# Project rules\n\n<!-- agent-toolkit:begin -->\n"
            target.write_text(original, encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"],
                capture_output=True, text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("incomplete or duplicate", result.stderr)
            self.assertEqual(original, target.read_text(encoding="utf-8"))

    def test_reinstall_replaces_only_managed_section(self):
        existing = f"# Project\n\n{BEGIN}\nOld rules\n{END}\n\n# Local\n"
        replacement = f"{BEGIN}\nNew rules\n{END}\n"

        self.assertEqual(
            updated_content(existing, replacement),
            f"# Project\n\n{BEGIN}\nNew rules\n{END}\n\n# Local\n",
        )

    def test_interactive_decline_leaves_file_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Project\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", directory],
                input="n\n", capture_output=True, text=True, check=True,
            )

            self.assertIn("No changes made", result.stdout)
            self.assertEqual("# Project\n", target.read_text(encoding="utf-8"))
            self.assertFalse((Path(directory) / ".agents").exists())

    def test_existing_skill_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / ".agents" / "skills" / "review"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("Local skill\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"],
                capture_output=True, text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("skill path already exists", result.stderr)
            self.assertFalse((Path(directory) / "AGENTS.md").exists())
            self.assertEqual((skill / "SKILL.md").read_text(), "Local skill\n")

    def test_self_install_preserves_source_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            toolkit = Path(directory) / "agent-toolkit"
            toolkit.mkdir()
            tools_dir = toolkit / "tools"
            tools_dir.mkdir()
            shutil.copy2(INSTALLER, tools_dir / "install.py")
            shutil.copytree(TOOLS_DIR / "common", tools_dir / "common")
            shutil.copy2(TOOLKIT_ROOT / "AGENTS.md", toolkit / "AGENTS.md")
            shutil.copytree(TOOLKIT_ROOT / "skills", toolkit / "skills")
            original = (toolkit / "AGENTS.md").read_bytes()
            command = [
                sys.executable, str(tools_dir / "install.py"),
                "--workspace", str(toolkit), "--yes",
            ]

            first = subprocess.run(command, capture_output=True, text=True, check=True)
            second = subprocess.run(command, capture_output=True, text=True, check=True)

            self.assertIn("Installed agent-toolkit", first.stdout)
            self.assertIn("Already up to date", second.stdout)
            self.assertEqual(original, (toolkit / "AGENTS.md").read_bytes())
            for source in (toolkit / "skills").iterdir():
                if source.is_dir() and (source / "SKILL.md").is_file():
                    link = toolkit / ".agents" / "skills" / source.name
                    self.assertTrue(link.is_symlink())
                    self.assertEqual(source.resolve(), link.resolve())


if __name__ == "__main__":
    unittest.main()
