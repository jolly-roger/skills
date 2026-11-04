import json
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

from common.identity import CANONICAL_IDENTITY, LEGACY_IDENTITY
from common.skill_manifest import parse_manifest

UNINSTALLER = TOOLS_DIR / "uninstall.py"
INSTALLER = TOOLS_DIR / "install.py"
REPOSITORY_ROOT = TOOLS_DIR.parent


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
            self.assertIn("Uninstalled skills", res.stdout)

            # AGENTS.md preserved without managed block
            self.assertEqual(target.read_text(encoding="utf-8").strip(), "# Project rules\n\nKeep this rule.")

            # Manifest and skills removed
            self.assertFalse((Path(directory) / CANONICAL_IDENTITY.manifest_relative_path).exists())
            self.assertFalse((Path(directory) / ".agents" / "skills").exists())

            # Repeat uninstall -> already uninstalled
            second = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("Already uninstalled", second.stdout)

    def test_uninstall_legacy_workspace_directly(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            target.write_text(
                f"# My project\n\n{LEGACY_IDENTITY.begin_marker}\nOld rules\n{LEGACY_IDENTITY.end_marker}\n",
                encoding="utf-8",
            )
            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            skills_dir = agents_dir / "skills"
            skills_dir.mkdir()

            review_dir = skills_dir / "review"
            shutil.copytree(REPOSITORY_ROOT / "skills" / "review", review_dir)

            from common.skill_files import inspect_target_skill
            snap = inspect_target_skill(review_dir)
            legacy_manifest_file = workspace / LEGACY_IDENTITY.manifest_relative_path
            legacy_data = {
                "format": LEGACY_IDENTITY.manifest_format,
                "version": 1,
                "skills": {
                    "review": {
                        "target": "skills/review",
                        "entries": [e.to_dict() for e in snap.entries],
                    }
                },
            }
            legacy_manifest_file.write_text(json.dumps(legacy_data), encoding="utf-8")

            # Direct uninstall
            cmd = [sys.executable, str(UNINSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("Uninstalled skills", res.stdout)
            self.assertFalse(legacy_manifest_file.exists())
            self.assertFalse(review_dir.exists())
            self.assertEqual(target.read_text(encoding="utf-8").strip(), "# My project")

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
            manifest_file = Path(directory) / CANONICAL_IDENTITY.manifest_relative_path
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
            self.assertFalse((Path(directory) / CANONICAL_IDENTITY.manifest_relative_path).exists())

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
            target = (REPOSITORY_ROOT / "skills" / "review").resolve()
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

    def test_stale_plan_aborts_if_copied_skill_modified_after_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(INSTALLER), "--workspace", directory, "--yes"], check=True)

            # Create plan
            from uninstall import create_uninstall_plan, apply_uninstall_plan
            plan = create_uninstall_plan(REPOSITORY_ROOT, Path(directory))

            # Modify a skill after preview
            review_md = Path(directory) / ".agents" / "skills" / "review" / "SKILL.md"
            review_md.write_text("modified after plan preview", encoding="utf-8")

            # Applying plan must raise ValueError and abort without removing
            with self.assertRaises(ValueError) as ctx:
                apply_uninstall_plan(plan, REPOSITORY_ROOT)
            self.assertIn("workspace changed before removing", str(ctx.exception))
            self.assertTrue(review_md.is_file())

    def test_uninstall_partial_workspace_legacy_markers_canonical_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            target.write_text(
                f"# My project\n\n{LEGACY_IDENTITY.begin_marker}\nOld rules\n{LEGACY_IDENTITY.end_marker}\n",
                encoding="utf-8",
            )
            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            skills_dir = agents_dir / "skills"
            skills_dir.mkdir()

            review_dir = skills_dir / "review"
            shutil.copytree(REPOSITORY_ROOT / "skills" / "review", review_dir)

            from common.skill_files import inspect_target_skill
            snap = inspect_target_skill(review_dir)
            canonical_manifest_file = workspace / CANONICAL_IDENTITY.manifest_relative_path
            canonical_manifest_file.write_text(
                json.dumps({
                    "format": CANONICAL_IDENTITY.manifest_format,
                    "version": 1,
                    "skills": {
                        "review": {
                            "target": "skills/review",
                            "entries": [e.to_dict() for e in snap.entries],
                        }
                    },
                }),
                encoding="utf-8",
            )

            cmd = [sys.executable, str(UNINSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("Uninstalled skills", res.stdout)
            self.assertFalse(canonical_manifest_file.exists())
            self.assertFalse(review_dir.exists())
            self.assertEqual(target.read_text(encoding="utf-8").strip(), "# My project")

    def test_uninstall_partial_workspace_canonical_markers_legacy_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            target.write_text(
                f"# My project\n\n{CANONICAL_IDENTITY.begin_marker}\nCanon rules\n{CANONICAL_IDENTITY.end_marker}\n",
                encoding="utf-8",
            )
            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            skills_dir = agents_dir / "skills"
            skills_dir.mkdir()

            review_dir = skills_dir / "review"
            shutil.copytree(REPOSITORY_ROOT / "skills" / "review", review_dir)

            from common.skill_files import inspect_target_skill
            snap = inspect_target_skill(review_dir)
            legacy_manifest_file = workspace / LEGACY_IDENTITY.manifest_relative_path
            legacy_manifest_file.write_text(
                json.dumps({
                    "format": LEGACY_IDENTITY.manifest_format,
                    "version": 1,
                    "skills": {
                        "review": {
                            "target": "skills/review",
                            "entries": [e.to_dict() for e in snap.entries],
                        }
                    },
                }),
                encoding="utf-8",
            )

            cmd = [sys.executable, str(UNINSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("Uninstalled skills", res.stdout)
            self.assertFalse(legacy_manifest_file.exists())
            self.assertFalse(review_dir.exists())
            self.assertEqual(target.read_text(encoding="utf-8").strip(), "# My project")

    def test_reject_dual_marker_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            target.write_text(
                f"{CANONICAL_IDENTITY.begin_marker}\nCanon\n{CANONICAL_IDENTITY.end_marker}\n"
                f"{LEGACY_IDENTITY.begin_marker}\nLegacy\n{LEGACY_IDENTITY.end_marker}\n",
                encoding="utf-8",
            )
            cmd = [sys.executable, str(UNINSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("both canonical", res.stderr)

    def test_reject_dual_manifest_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            (agents_dir / CANONICAL_IDENTITY.manifest_filename).write_text(
                json.dumps({"format": CANONICAL_IDENTITY.manifest_format, "version": 1, "skills": {}}),
                encoding="utf-8",
            )
            (agents_dir / LEGACY_IDENTITY.manifest_filename).write_text(
                json.dumps({"format": LEGACY_IDENTITY.manifest_format, "version": 1, "skills": {}}),
                encoding="utf-8",
            )

            cmd = [sys.executable, str(UNINSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("both canonical", res.stderr)

    def test_reject_malformed_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            (agents_dir / CANONICAL_IDENTITY.manifest_filename).write_text("{bad json", encoding="utf-8")

            cmd = [sys.executable, str(UNINSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("JSON", res.stderr)

    def test_already_uninstalled_across_both_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            cmd = [sys.executable, str(UNINSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("Already uninstalled", res.stdout)

            # Having project-only AGENTS.md without markers is still "Already uninstalled"
            (workspace / "AGENTS.md").write_text("# Project only\n", encoding="utf-8")
            res2 = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("Already uninstalled", res2.stdout)

            # Having legacy markers makes it NOT already uninstalled: uninstaller uninstalls them
            (workspace / "AGENTS.md").write_text(
                f"# Project only\n\n{LEGACY_IDENTITY.begin_marker}\nOld\n{LEGACY_IDENTITY.end_marker}\n",
                encoding="utf-8",
            )
            res3 = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.assertIn("Uninstalled skills", res3.stdout)
            self.assertEqual((workspace / "AGENTS.md").read_text(encoding="utf-8").strip(), "# Project only")

    def test_self_uninstallation_under_legacy_identity(self):
        with tempfile.TemporaryDirectory() as fake_repo:
            (Path(fake_repo) / "AGENTS.md").write_text("Authoritative rules", encoding="utf-8")
            agents_dir = Path(fake_repo) / ".agents"
            agents_dir.mkdir()
            skills_dir = agents_dir / "skills"
            skills_dir.mkdir()

            test_skill = skills_dir / "test-skill"
            test_skill.mkdir()
            (test_skill / "SKILL.md").write_text("dummy", encoding="utf-8")

            from common.skill_files import inspect_target_skill
            snap = inspect_target_skill(test_skill)
            legacy_manifest_file = Path(fake_repo) / LEGACY_IDENTITY.manifest_relative_path
            legacy_manifest_file.write_text(
                json.dumps({
                    "format": LEGACY_IDENTITY.manifest_format,
                    "version": 1,
                    "skills": {
                        "test-skill": {
                            "target": "skills/test-skill",
                            "entries": [e.to_dict() for e in snap.entries],
                        }
                    },
                }),
                encoding="utf-8",
            )

            shutil.copytree(TOOLS_DIR, Path(fake_repo) / "tools")
            uninstaller = Path(fake_repo) / "tools" / "uninstall.py"

            res = subprocess.run([sys.executable, str(uninstaller), "--workspace", fake_repo, "--yes"], capture_output=True, text=True, check=True)
            self.assertIn("Uninstalled skills", res.stdout)
            self.assertEqual((Path(fake_repo) / "AGENTS.md").read_text(encoding="utf-8"), "Authoritative rules")
            self.assertFalse(test_skill.exists())
            self.assertFalse(legacy_manifest_file.exists())

    def test_rollback_restores_manifest_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            legacy_manifest_file = workspace / LEGACY_IDENTITY.manifest_relative_path
            legacy_raw = json.dumps({"format": LEGACY_IDENTITY.manifest_format, "version": 1, "skills": {}}, indent=2)
            legacy_manifest_file.write_text(legacy_raw, encoding="utf-8")

            from uninstall import create_uninstall_plan, apply_uninstall_plan
            import uninstall

            plan = create_uninstall_plan(REPOSITORY_ROOT, workspace)

            orig_unlink = Path.unlink

            def faulty_unlink(p, missing_ok=False):
                if p == legacy_manifest_file:
                    raise IOError("Permission denied simulation")
                return orig_unlink(p, missing_ok=missing_ok)

            Path.unlink = faulty_unlink
            try:
                with self.assertRaises(RuntimeError) as ctx:
                    apply_uninstall_plan(plan, REPOSITORY_ROOT)
                self.assertIn("uninstallation failed and was rolled back", str(ctx.exception))
            finally:
                Path.unlink = orig_unlink

            self.assertTrue(legacy_manifest_file.exists())
            self.assertEqual(legacy_manifest_file.read_text(encoding="utf-8"), legacy_raw)


if __name__ == "__main__":
    unittest.main()
