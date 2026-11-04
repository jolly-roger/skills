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

INSTALLER = TOOLS_DIR / "install.py"
REPOSITORY_ROOT = TOOLS_DIR.parent


class InstallerTests(unittest.TestCase):
    def test_install_copies_skills_and_creates_canonical_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("# Project rules\n\nKeep this rule.\n", encoding="utf-8")
            command = [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"]

            first = subprocess.run(command, capture_output=True, text=True, check=True)
            installed = target.read_text(encoding="utf-8")
            manifest_file = Path(directory) / CANONICAL_IDENTITY.manifest_relative_path

            self.assertIn("Installed skills", first.stdout)
            self.assertIn("# Project rules\n\nKeep this rule.", installed)
            self.assertIn(CANONICAL_IDENTITY.begin_marker, installed)
            self.assertNotIn("agent-toolkit", installed)
            self.assertTrue(manifest_file.is_file())

            # Verify manifest content
            manifest = parse_manifest(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest.format, CANONICAL_IDENTITY.manifest_format)

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

    def test_migrate_legacy_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            target.write_text(
                f"# My project\n\n{LEGACY_IDENTITY.begin_marker}\nOld rules\n{LEGACY_IDENTITY.end_marker}\n",
                encoding="utf-8",
            )
            # Create a legacy manifest
            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            skills_dir = agents_dir / "skills"
            skills_dir.mkdir()

            # Install review skill manually under legacy manifest
            review_dir = skills_dir / "review"
            shutil.copytree(REPOSITORY_ROOT / "skills" / "review", review_dir)

            legacy_manifest_file = workspace / LEGACY_IDENTITY.manifest_relative_path
            legacy_data = {
                "format": LEGACY_IDENTITY.manifest_format,
                "version": 1,
                "skills": {
                    "review": {
                        "target": "skills/review",
                        "entries": [
                            {"path": "SKILL.md", "type": "file", "sha256": "dummy"}
                        ]
                    }
                }
            }
            # calculate actual hash for valid test
            from common.skill_files import inspect_target_skill
            snap = inspect_target_skill(review_dir)
            legacy_data["skills"]["review"]["entries"] = [e.to_dict() for e in snap.entries]
            legacy_manifest_file.write_text(json.dumps(legacy_data), encoding="utf-8")

            # Run installer to migrate
            command = [sys.executable, str(INSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(command, capture_output=True, text=True, check=True)
            self.assertIn("Installed skills", res.stdout)

            # Check legacy manifest removed, canonical created
            self.assertFalse(legacy_manifest_file.exists())
            canonical_manifest_file = workspace / CANONICAL_IDENTITY.manifest_relative_path
            self.assertTrue(canonical_manifest_file.exists())

            # Check markers migrated
            content = target.read_text(encoding="utf-8")
            self.assertIn(CANONICAL_IDENTITY.begin_marker, content)
            self.assertNotIn(LEGACY_IDENTITY.begin_marker, content)
            self.assertIn("# My project", content)

    def test_update_exact_managed_copy_when_source_changes(self):
        with tempfile.TemporaryDirectory() as fake_repo:
            src_skills = Path(fake_repo) / "skills"
            test_skill = src_skills / "test-skill"
            test_skill.mkdir(parents=True)
            (test_skill / "SKILL.md").write_text("version 1", encoding="utf-8")
            (Path(fake_repo) / "AGENTS.md").write_text("Shared rules", encoding="utf-8")
            shutil.copytree(TOOLS_DIR, Path(fake_repo) / "tools")

            installer_script = Path(fake_repo) / "tools" / "install.py"

            with tempfile.TemporaryDirectory() as workspace:
                cmd = [sys.executable, str(installer_script), "--workspace", workspace, "--yes"]
                subprocess.run(cmd, check=True, capture_output=True, text=True)

                installed_skill_md = Path(workspace) / ".agents" / "skills" / "test-skill" / "SKILL.md"
                self.assertEqual(installed_skill_md.read_text(encoding="utf-8"), "version 1")

                (test_skill / "SKILL.md").write_text("version 2", encoding="utf-8")

                res = subprocess.run(cmd, check=True, capture_output=True, text=True)
                self.assertIn("Installed skills", res.stdout)
                self.assertEqual(installed_skill_md.read_text(encoding="utf-8"), "version 2")

    def test_refuse_to_overwrite_modified_managed_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            cmd = [sys.executable, str(INSTALLER), "--workspace", directory, "--yes"]
            subprocess.run(cmd, check=True, capture_output=True, text=True)

            review_md = Path(directory) / ".agents" / "skills" / "review" / "SKILL.md"
            review_md.write_text("local modification", encoding="utf-8")

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
            target = (REPOSITORY_ROOT / "skills" / "review").resolve()
            legacy_link.symlink_to(os.path.relpath(target, legacy_link.parent))

            cmd = [sys.executable, str(INSTALLER), "--workspace", str(workspace_dir), "--yes"]
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.assertIn("Installed skills", res.stdout)

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
            self.assertIn("Installed skills", res.stdout)
            self.assertEqual((Path(fake_repo) / "AGENTS.md").read_text(encoding="utf-8"), "Authoritative rules")
            self.assertTrue((Path(fake_repo) / ".agents" / "skills" / "dummy").is_dir())

    def test_legacy_self_installation_preserves_authoritative_agents_md_and_migrates_manifest(self):
        with tempfile.TemporaryDirectory() as fake_repo:
            repo_path = Path(fake_repo)
            authoritative_agents = "# Authoritative rules for this repo\n\n- Rule 1\n- Rule 2\n"
            (repo_path / "AGENTS.md").write_text(authoritative_agents, encoding="utf-8")

            src_skills = repo_path / "skills"
            (src_skills / "dummy").mkdir(parents=True)
            (src_skills / "dummy" / "SKILL.md").write_text("dummy skill v1", encoding="utf-8")
            shutil.copytree(TOOLS_DIR, repo_path / "tools")

            # Seed pre-existing copied skill and legacy manifest
            target_skills = repo_path / ".agents" / "skills"
            (target_skills / "dummy").mkdir(parents=True)
            (target_skills / "dummy" / "SKILL.md").write_text("dummy skill v1", encoding="utf-8")

            from common.skill_files import inspect_target_skill
            snap = inspect_target_skill(target_skills / "dummy")
            legacy_manifest_file = repo_path / LEGACY_IDENTITY.manifest_relative_path
            legacy_manifest_file.write_text(
                json.dumps({
                    "format": LEGACY_IDENTITY.manifest_format,
                    "version": 1,
                    "skills": {
                        "dummy": {
                            "target": "skills/dummy",
                            "entries": [e.to_dict() for e in snap.entries],
                        }
                    },
                }),
                encoding="utf-8",
            )

            installer_script = repo_path / "tools" / "install.py"
            cmd = [sys.executable, str(installer_script), "--workspace", str(repo_path), "--yes"]
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.assertIn("Installed skills", res.stdout)

            # Authoritative AGENTS.md must NOT have managed block or be changed
            self.assertEqual((repo_path / "AGENTS.md").read_text(encoding="utf-8"), authoritative_agents)
            self.assertNotIn(CANONICAL_IDENTITY.begin_marker, (repo_path / "AGENTS.md").read_text(encoding="utf-8"))

            # Legacy manifest removed, canonical manifest created with ownership preserved
            self.assertFalse(legacy_manifest_file.exists())
            canonical_manifest_file = repo_path / CANONICAL_IDENTITY.manifest_relative_path
            self.assertTrue(canonical_manifest_file.exists())
            manifest = parse_manifest(canonical_manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest.format, CANONICAL_IDENTITY.manifest_format)
            self.assertIn("dummy", manifest.skills)
            self.assertEqual(manifest.skills["dummy"].entries, snap.entries)

    def test_stale_migration_plan_aborts_if_markers_change_after_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            target.write_text(
                f"# Project\n\n{LEGACY_IDENTITY.begin_marker}\nOld\n{LEGACY_IDENTITY.end_marker}\n",
                encoding="utf-8",
            )
            from install import create_install_plan, apply_install_plan
            plan = create_install_plan(REPOSITORY_ROOT, workspace)

            # Change markers after plan preview
            target.write_text("# Project\n\n# All custom now\n", encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                apply_install_plan(plan, REPOSITORY_ROOT)
            self.assertIn("workspace changed since preview", str(ctx.exception))

    def test_reject_dual_marker_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            target.write_text(
                f"{CANONICAL_IDENTITY.begin_marker}\nCanon\n{CANONICAL_IDENTITY.end_marker}\n"
                f"{LEGACY_IDENTITY.begin_marker}\nLegacy\n{LEGACY_IDENTITY.end_marker}\n",
                encoding="utf-8",
            )
            cmd = [sys.executable, str(INSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("both canonical", res.stderr)

    def test_migrate_partial_workspace_legacy_markers_canonical_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            target.write_text(
                f"# Project heading\n\nPreserve this rule.\n\n{LEGACY_IDENTITY.begin_marker}\nOld block\n{LEGACY_IDENTITY.end_marker}\n\n# Project footer\n",
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

            cmd = [sys.executable, str(INSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.assertIn("Installed skills", res.stdout)

            # Markers migrated to canonical
            agents_text = target.read_text(encoding="utf-8")
            self.assertIn(CANONICAL_IDENTITY.begin_marker, agents_text)
            self.assertNotIn(LEGACY_IDENTITY.begin_marker, agents_text)
            self.assertIn("# Project heading\n\nPreserve this rule.", agents_text)
            self.assertIn("# Project footer", agents_text)

            # Canonical manifest preserved and updated with remaining skills
            self.assertTrue(canonical_manifest_file.exists())
            self.assertFalse((workspace / LEGACY_IDENTITY.manifest_relative_path).exists())
            manifest = parse_manifest(canonical_manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest.format, CANONICAL_IDENTITY.manifest_format)
            self.assertIn("review", manifest.skills)
            self.assertEqual(manifest.skills["review"].entries, snap.entries)

    def test_decline_migration_leaves_legacy_files_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            legacy_text = f"# Project\n\n{LEGACY_IDENTITY.begin_marker}\nOld\n{LEGACY_IDENTITY.end_marker}\n"
            target.write_text(legacy_text, encoding="utf-8")

            # Mock decline with empty input (or 'n')
            proc = subprocess.run(
                [sys.executable, str(INSTALLER), "--workspace", str(workspace)],
                input="n\n",
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("No changes made.", proc.stdout)
            self.assertEqual(target.read_text(encoding="utf-8"), legacy_text)

    def test_dry_run_migration_previews_migration_without_writing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            legacy_text = f"# Project\n\n{LEGACY_IDENTITY.begin_marker}\nOld\n{LEGACY_IDENTITY.end_marker}\n"
            target.write_text(legacy_text, encoding="utf-8")

            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            legacy_manifest_file = workspace / LEGACY_IDENTITY.manifest_relative_path
            legacy_manifest_file.write_text(
                json.dumps({"format": LEGACY_IDENTITY.manifest_format, "version": 1, "skills": {}}),
                encoding="utf-8",
            )

            cmd = [sys.executable, str(INSTALLER), "--workspace", str(workspace), "--dry-run"]
            res = subprocess.run(cmd, check=True, capture_output=True, text=True)

            self.assertIn("Migrate managed block: agent-toolkit -> jolly-roger-skills", res.stdout)
            self.assertIn("Migrate manifest:", res.stdout)

            # Assert files unchanged
            self.assertEqual(target.read_text(encoding="utf-8"), legacy_text)
            self.assertTrue(legacy_manifest_file.exists())
            self.assertFalse((workspace / CANONICAL_IDENTITY.manifest_relative_path).exists())

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

            cmd = [sys.executable, str(INSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("both canonical", res.stderr)

    def test_migrate_partial_workspace_canonical_markers_legacy_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            target.write_text(
                f"# Project\n\n{CANONICAL_IDENTITY.begin_marker}\nCanon block\n{CANONICAL_IDENTITY.end_marker}\n",
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

            cmd = [sys.executable, str(INSTALLER), "--workspace", str(workspace), "--yes"]
            subprocess.run(cmd, check=True, capture_output=True, text=True)

            self.assertFalse(legacy_manifest_file.exists())
            canonical_manifest_file = workspace / CANONICAL_IDENTITY.manifest_relative_path
            self.assertTrue(canonical_manifest_file.exists())
            self.assertIn(CANONICAL_IDENTITY.begin_marker, target.read_text(encoding="utf-8"))

            # Verify canonical manifest preserves ownership records
            manifest = parse_manifest(canonical_manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(manifest.format, CANONICAL_IDENTITY.manifest_format)
            self.assertIn("review", manifest.skills)
            self.assertEqual(manifest.skills["review"].entries, snap.entries)

    def test_stale_migration_plan_aborts_if_manifest_modified_after_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            legacy_manifest_file = workspace / LEGACY_IDENTITY.manifest_relative_path
            legacy_manifest_file.write_text(
                json.dumps({"format": LEGACY_IDENTITY.manifest_format, "version": 1, "skills": {}}),
                encoding="utf-8",
            )

            from install import create_install_plan, apply_install_plan
            plan = create_install_plan(REPOSITORY_ROOT, workspace)

            # Modify manifest after preview
            legacy_manifest_file.write_text(
                json.dumps({"format": LEGACY_IDENTITY.manifest_format, "version": 1, "skills": {}, "comment": "stale"}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError) as ctx:
                apply_install_plan(plan, REPOSITORY_ROOT)
            self.assertIn("workspace manifest changed since preview", str(ctx.exception))

    def test_reject_malformed_legacy_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            legacy_manifest_file = workspace / LEGACY_IDENTITY.manifest_relative_path
            legacy_manifest_file.write_text("{invalid json", encoding="utf-8")

            cmd = [sys.executable, str(INSTALLER), "--workspace", str(workspace), "--yes"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.assertNotEqual(res.returncode, 0)
            self.assertIn("JSON", res.stderr)

    def test_rollback_restores_legacy_manifest_and_markers_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            target = workspace / "AGENTS.md"
            legacy_agents_text = f"# Project\n\n{LEGACY_IDENTITY.begin_marker}\nOld\n{LEGACY_IDENTITY.end_marker}\n"
            target.write_text(legacy_agents_text, encoding="utf-8")

            agents_dir = workspace / ".agents"
            agents_dir.mkdir()
            legacy_manifest_file = workspace / LEGACY_IDENTITY.manifest_relative_path
            legacy_manifest_raw = json.dumps(
                {"format": LEGACY_IDENTITY.manifest_format, "version": 1, "skills": {}},
                indent=2,
            )
            legacy_manifest_file.write_text(legacy_manifest_raw, encoding="utf-8")

            from install import create_install_plan, apply_install_plan
            import install

            plan = create_install_plan(REPOSITORY_ROOT, workspace)

            # Monkeypatch write_atomically during canonical manifest write to simulate a failure
            orig_write_atomically = install.write_atomically

            def faulty_write_atomically(path, content):
                if path == plan.canonical_manifest_path:
                    raise IOError("Disk full simulation")
                return orig_write_atomically(path, content)

            install.write_atomically = faulty_write_atomically
            try:
                with self.assertRaises(RuntimeError) as ctx:
                    apply_install_plan(plan, REPOSITORY_ROOT)
                self.assertIn("installation failed and was rolled back", str(ctx.exception))
            finally:
                install.write_atomically = orig_write_atomically

            # Check rollback restored legacy state
            self.assertEqual(target.read_text(encoding="utf-8"), legacy_agents_text)
            self.assertTrue(legacy_manifest_file.exists())
            self.assertEqual(legacy_manifest_file.read_text(encoding="utf-8"), legacy_manifest_raw)
            self.assertFalse((workspace / CANONICAL_IDENTITY.manifest_relative_path).exists())


if __name__ == "__main__":
    unittest.main()
