import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

INSTALLER = TOOLS_DIR / "install.py"
UNINSTALLER = TOOLS_DIR / "uninstall.py"
TOOLKIT_ROOT = TOOLS_DIR.parent

from uninstall import apply_uninstall_plan, create_uninstall_plan, validate_uninstall_preconditions


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

    # -------------------------------------------------------------------------
    # Cross-installation integration tests (P-00002)
    # -------------------------------------------------------------------------

    def _create_mock_checkout(self, root: Path, layout: str = "current", skills: tuple[str, ...] = ("merge-master",)) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        (root / "AGENTS.md").write_text("# Authoritative AGENTS.md\n", encoding="utf-8")
        if layout == "current":
            tools_dir = root / "tools"
            tools_dir.mkdir(parents=True, exist_ok=True)
            (tools_dir / "install.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        else:
            (root / "install.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")

        for skill in skills:
            skill_dir = root / "skills" / skill
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(f"# {skill}\n", encoding="utf-8")
        return root

    def test_cross_checkout_uninstall_removes_links_from_another_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td).resolve()
            checkout_a = self._create_mock_checkout(base / "checkout_a", layout="current", skills=("merge-master",))
            ws = base / "workspace"
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            link = skills_dir / "merge-master"
            link.symlink_to(
                os.path.relpath(checkout_a / "skills" / "merge-master", link.parent),
                target_is_directory=True,
            )
            agents_md = ws / "AGENTS.md"
            agents_md.write_text(
                "# Project\n<!-- agent-toolkit:begin -->\nManaged\n<!-- agent-toolkit:end -->\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("Uninstalled agent-toolkit", result.stdout)
            self.assertFalse(link.exists(follow_symlinks=False))
            self.assertFalse((ws / ".agents").exists())
            self.assertEqual(agents_md.read_text(encoding="utf-8"), "# Project\n")

    def test_legacy_embedded_checkout_scenario(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve()
            legacy_checkout = self._create_mock_checkout(
                ws / "agent-toolkit",
                layout="legacy",
                skills=("merge-master", "pragmatic-functional-programming"),
            )
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            link1 = skills_dir / "merge-master"
            link1.symlink_to(
                os.path.relpath(legacy_checkout / "skills" / "merge-master", link1.parent),
                target_is_directory=True,
            )
            link2 = skills_dir / "pragmatic-functional-programming"
            link2.symlink_to(
                os.path.relpath(legacy_checkout / "skills" / "pragmatic-functional-programming", link2.parent),
                target_is_directory=True,
            )
            agents_md = ws / "AGENTS.md"
            agents_md.write_text(
                "<!-- agent-toolkit:begin -->\nManaged\n<!-- agent-toolkit:end -->\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("Uninstalled agent-toolkit", result.stdout)
            self.assertFalse(link1.exists(follow_symlinks=False))
            self.assertFalse(link2.exists(follow_symlinks=False))
            self.assertFalse((ws / ".agents").exists())
            self.assertFalse(agents_md.exists())

    def test_cross_checkout_uninstall_followed_by_install(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td).resolve()
            checkout_a = self._create_mock_checkout(base / "checkout_a", layout="legacy", skills=("merge-master",))
            ws = base / "workspace"
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            link = skills_dir / "merge-master"
            link.symlink_to(
                os.path.relpath(checkout_a / "skills" / "merge-master", link.parent),
                target_is_directory=True,
            )
            agents_md = ws / "AGENTS.md"
            agents_md.write_text("# Project\n", encoding="utf-8")

            # 1. Uninstall with current toolkit
            un_result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("Uninstalled agent-toolkit", un_result.stdout)
            self.assertFalse(link.exists(follow_symlinks=False))

            # 2. Install with current toolkit succeeds without link collision
            in_result = subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("Installed agent-toolkit", in_result.stdout)
            installed_link = skills_dir / "merge-master"
            self.assertTrue(installed_link.is_symlink())
            self.assertEqual(installed_link.resolve(), (TOOLKIT_ROOT / "skills" / "merge-master").resolve())

    def test_preview_source_checkout_and_recognition_kind_in_dry_run(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td).resolve()
            checkout_a = self._create_mock_checkout(base / "checkout_a", layout="legacy", skills=("merge-master",))
            ws = base / "workspace"
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            link = skills_dir / "merge-master"
            link.symlink_to(
                os.path.relpath(checkout_a / "skills" / "merge-master", link.parent),
                target_is_directory=True,
            )

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", str(ws), "--dry-run"],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("Remove skill link:", result.stdout)
            self.assertIn(f"source: {checkout_a}", result.stdout)
            self.assertIn("recognition: legacy agent-toolkit checkout", result.stdout)
            self.assertTrue(link.is_symlink())

    def test_interactive_decline_makes_no_changes_cross_checkout(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td).resolve()
            checkout_a = self._create_mock_checkout(base / "checkout_a", layout="current", skills=("merge-master",))
            ws = base / "workspace"
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            link = skills_dir / "merge-master"
            link.symlink_to(
                os.path.relpath(checkout_a / "skills" / "merge-master", link.parent),
                target_is_directory=True,
            )

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", str(ws)],
                input="n\n", check=True, capture_output=True, text=True,
            )
            self.assertIn("No changes made.", result.stdout)
            self.assertTrue(link.is_symlink())

    def test_removes_links_from_multiple_recognized_checkouts_in_one_workspace(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td).resolve()
            checkout_legacy = self._create_mock_checkout(base / "legacy", layout="legacy", skills=("skill-one",))
            checkout_current = self._create_mock_checkout(base / "current", layout="current", skills=("skill-two",))
            ws = base / "workspace"
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            link1 = skills_dir / "skill-one"
            link1.symlink_to(
                os.path.relpath(checkout_legacy / "skills" / "skill-one", link1.parent),
                target_is_directory=True,
            )
            link2 = skills_dir / "skill-two"
            link2.symlink_to(
                os.path.relpath(checkout_current / "skills" / "skill-two", link2.parent),
                target_is_directory=True,
            )

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("Uninstalled agent-toolkit", result.stdout)
            self.assertFalse(link1.exists(follow_symlinks=False))
            self.assertFalse(link2.exists(follow_symlinks=False))
            self.assertFalse((ws / ".agents").exists())

    def test_preserves_unrelated_entries_under_agents_during_cross_checkout_uninstall(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td).resolve()
            checkout_a = self._create_mock_checkout(base / "checkout_a", layout="current", skills=("merge-master",))
            ws = base / "workspace"
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            link = skills_dir / "merge-master"
            link.symlink_to(
                os.path.relpath(checkout_a / "skills" / "merge-master", link.parent),
                target_is_directory=True,
            )
            custom_config = ws / ".agents" / "config.json"
            custom_config.write_text("{}", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            self.assertIn("Uninstalled agent-toolkit", result.stdout)
            self.assertFalse(link.exists(follow_symlinks=False))
            self.assertFalse(skills_dir.exists())
            self.assertTrue(custom_config.is_file())
            self.assertTrue((ws / ".agents").is_dir())

    def test_rollback_restores_cross_checkout_links_with_original_raw_targets_on_failure(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td).resolve()
            checkout_a = self._create_mock_checkout(base / "checkout_a", layout="legacy", skills=("merge-master",))
            ws = base / "workspace"
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            raw_rel = os.path.relpath(checkout_a / "skills" / "merge-master", skills_dir)
            link = skills_dir / "merge-master"
            link.symlink_to(raw_rel, target_is_directory=True)

            agents_md = ws / "AGENTS.md"
            agents_md.write_text(
                "<!-- agent-toolkit:begin -->\nManaged\n<!-- agent-toolkit:end -->\n",
                encoding="utf-8",
            )

            original_mode = ws.stat().st_mode
            ws.chmod(0o555)
            try:
                result = subprocess.run(
                    [sys.executable, str(UNINSTALLER), "--workspace", str(ws), "--yes"],
                    capture_output=True, text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(link.is_symlink())
                self.assertEqual(os.readlink(link), raw_rel)
            finally:
                ws.chmod(original_mode)

    def test_unproven_dangling_link_produces_warning_and_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve()
            skills_dir = ws / ".agents" / "skills"
            skills_dir.mkdir(parents=True)

            dangling_link = skills_dir / "ghost-skill"
            dangling_link.symlink_to("/nonexistent/deleted/checkout/skills/ghost-skill", target_is_directory=True)

            result = subprocess.run(
                [sys.executable, str(UNINSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("Warning: preserving unproven dangling skill link:", result.stdout)
            self.assertIn("Already uninstalled", result.stdout)
            self.assertTrue(dangling_link.is_symlink())
            self.assertTrue(skills_dir.is_dir())

    # -------------------------------------------------------------------------
    # Workspace change / precondition tests (P-00002)
    # -------------------------------------------------------------------------

    def test_replace_planned_symlink_with_regular_file_aborts_and_preserves_file(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve()
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            plan = create_uninstall_plan(TOOLKIT_ROOT, ws)
            link_path = ws / ".agents" / "skills" / "review"
            link_path.unlink()
            link_path.write_text("regular file", encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                apply_uninstall_plan(plan)
            self.assertIn("workspace changed since preview", str(ctx.exception))
            self.assertTrue(link_path.is_file() and not link_path.is_symlink())
            self.assertEqual(link_path.read_text(encoding="utf-8"), "regular file")
            self.assertTrue((ws / "AGENTS.md").exists())

    def test_repoint_planned_symlink_aborts_and_preserves_new_target(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve()
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            plan = create_uninstall_plan(TOOLKIT_ROOT, ws)
            link_path = ws / ".agents" / "skills" / "review"
            link_path.unlink()
            link_path.symlink_to("/opt/repointed/target", target_is_directory=True)

            with self.assertRaises(ValueError) as ctx:
                apply_uninstall_plan(plan)
            self.assertIn("workspace changed since preview", str(ctx.exception))
            self.assertTrue(link_path.is_symlink())
            self.assertEqual(os.readlink(link_path), "/opt/repointed/target")

    def test_delete_planned_symlink_aborts_cleanly(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve()
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            plan = create_uninstall_plan(TOOLKIT_ROOT, ws)
            link_path = ws / ".agents" / "skills" / "review"
            link_path.unlink()

            with self.assertRaises(ValueError) as ctx:
                apply_uninstall_plan(plan)
            self.assertIn("workspace changed since preview", str(ctx.exception))
            self.assertTrue((ws / "AGENTS.md").exists())

    def test_edit_agents_md_after_planning_aborts_and_preserves_new_content(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve()
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            plan = create_uninstall_plan(TOOLKIT_ROOT, ws)
            agents_md = ws / "AGENTS.md"
            agents_md.write_text("# Project edited after preview\n", encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                apply_uninstall_plan(plan)
            self.assertIn("workspace changed since preview", str(ctx.exception))
            self.assertEqual(agents_md.read_text(encoding="utf-8"), "# Project edited after preview\n")
            self.assertTrue((ws / ".agents" / "skills" / "review").is_symlink())

    def test_replace_agents_md_with_symlink_aborts_and_preserves_target(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td).resolve()
            ws = base / "workspace"
            ws.mkdir()
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            plan = create_uninstall_plan(TOOLKIT_ROOT, ws)
            secret_file = base / "secret.txt"
            secret_file.write_text("secret content", encoding="utf-8")
            agents_md = ws / "AGENTS.md"
            agents_md.unlink()
            agents_md.symlink_to(secret_file)

            with self.assertRaises(ValueError) as ctx:
                apply_uninstall_plan(plan)
            self.assertIn("workspace changed since preview", str(ctx.exception))
            self.assertTrue(agents_md.is_symlink())
            self.assertEqual(secret_file.read_text(encoding="utf-8"), "secret content")

    def test_repeated_precondition_failure_after_earlier_link_removal_rolls_back(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve()
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            plan = create_uninstall_plan(TOOLKIT_ROOT, ws)
            self.assertGreater(len(plan.links), 1)

            first_link = plan.links[0]
            first_raw_target = first_link.raw_target
            orig_unlink = Path.unlink

            # Simulate concurrent edit to AGENTS.md happening right after first link is unlinked
            def unlink_hook(self_path, *args, **kwargs):
                orig_unlink(self_path, *args, **kwargs)
                if self_path == first_link.path:
                    (ws / "AGENTS.md").write_text("# Concurrent edit!\n", encoding="utf-8")

            with patch.object(Path, "unlink", side_effect=unlink_hook, autospec=True):
                with self.assertRaises((ValueError, RuntimeError)):
                    apply_uninstall_plan(plan)

            # Verify rollback restored first_link
            self.assertTrue(first_link.path.is_symlink())
            self.assertEqual(os.readlink(first_link.path), first_raw_target)

    def test_initial_precondition_failure_causes_no_filesystem_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve()
            subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", str(ws), "--yes"],
                check=True, capture_output=True, text=True,
            )
            plan = create_uninstall_plan(TOOLKIT_ROOT, ws)
            first_link = plan.links[0]
            first_raw = first_link.raw_target

            # Modify another link
            last_link = plan.links[-1]
            last_link.path.unlink()
            last_link.path.symlink_to("/modified/target", target_is_directory=True)

            with self.assertRaises(ValueError):
                apply_uninstall_plan(plan)

            # Confirm first_link was never deleted or touched
            self.assertTrue(first_link.path.is_symlink())
            self.assertEqual(os.readlink(first_link.path), first_raw)

    def test_dangling_agents_symlink_aborts_and_preserves_agents_md(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve()
            agents_md = ws / "AGENTS.md"
            content = "# Project rules\n\n<!-- agent-toolkit:begin -->\nManaged\n<!-- agent-toolkit:end -->\n"
            agents_md.write_text(content, encoding="utf-8")

            plan = create_uninstall_plan(TOOLKIT_ROOT, ws)
            self.assertEqual(len(plan.links), 0)

            # Introduce dangling .agents symlink
            dangling_agents = ws / ".agents"
            dangling_agents.symlink_to("/nonexistent/target/path", target_is_directory=True)
            self.assertTrue(dangling_agents.is_symlink())
            self.assertFalse(dangling_agents.exists())

            with self.assertRaises(ValueError) as ctx:
                apply_uninstall_plan(plan)
            self.assertIn("workspace changed since preview", str(ctx.exception))
            self.assertEqual(agents_md.read_text(encoding="utf-8"), content)

    def test_dangling_agents_skills_symlink_aborts_and_preserves_agents_md(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td).resolve()
            agents_md = ws / "AGENTS.md"
            content = "# Project rules\n\n<!-- agent-toolkit:begin -->\nManaged\n<!-- agent-toolkit:end -->\n"
            agents_md.write_text(content, encoding="utf-8")

            plan = create_uninstall_plan(TOOLKIT_ROOT, ws)
            self.assertEqual(len(plan.links), 0)

            # Introduce real .agents directory and dangling .agents/skills symlink
            agents_dir = ws / ".agents"
            agents_dir.mkdir()
            dangling_skills = agents_dir / "skills"
            dangling_skills.symlink_to("/nonexistent/target/path", target_is_directory=True)
            self.assertTrue(dangling_skills.is_symlink())
            self.assertFalse(dangling_skills.exists())

            with self.assertRaises(ValueError) as ctx:
                apply_uninstall_plan(plan)
            self.assertIn("workspace changed since preview", str(ctx.exception))
            self.assertEqual(agents_md.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
