import sys
import tempfile
import unittest
from pathlib import Path

# Add tools directory to sys.path
TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from common.agents_file import (
    BEGIN,
    END,
    diff_content,
    managed_block,
    removed_content,
    updated_content,
    validate_markers,
)


class AgentsFileTests(unittest.TestCase):
    def test_validate_markers_valid(self):
        validate_markers("No markers")
        validate_markers(f"{BEGIN}\nManaged block\n{END}\n")

    def test_reject_lone_begin_marker(self):
        with self.assertRaises(ValueError) as ctx:
            validate_markers(f"# Rules\n{BEGIN}\nContent\n")
        self.assertIn("incomplete or duplicate", str(ctx.exception))

    def test_reject_lone_end_marker(self):
        with self.assertRaises(ValueError) as ctx:
            validate_markers(f"# Rules\nContent\n{END}\n")
        self.assertIn("incomplete or duplicate", str(ctx.exception))

    def test_reject_reversed_markers(self):
        with self.assertRaises(ValueError) as ctx:
            validate_markers(f"# Rules\n{END}\nContent\n{BEGIN}\n")
        self.assertIn("incomplete or duplicate", str(ctx.exception))

    def test_reject_duplicate_markers(self):
        with self.assertRaises(ValueError) as ctx:
            validate_markers(f"{BEGIN}\nBlock 1\n{END}\n{BEGIN}\nBlock 2\n{END}\n")
        self.assertIn("incomplete or duplicate", str(ctx.exception))

    def test_remove_only_managed_block_returns_empty_content(self):
        content = f"{BEGIN}\n# Toolkit rules\nRule 1\n{END}\n"
        self.assertEqual(removed_content(content), "")

    def test_preserve_content_before_managed_block(self):
        content = f"# Project rules\n\nCustom rule\n\n{BEGIN}\n# Managed\n{END}\n"
        self.assertEqual(removed_content(content), "# Project rules\n\nCustom rule\n")

    def test_preserve_content_after_managed_block(self):
        content = f"{BEGIN}\n# Managed\n{END}\n\n# Project rules\n\nCustom rule\n"
        self.assertEqual(removed_content(content), "# Project rules\n\nCustom rule\n")

    def test_preserve_content_on_both_sides_with_one_blank_line(self):
        content = (
            f"# Before\n\nPre rule\n\n"
            f"{BEGIN}\n# Managed\n{END}\n\n"
            f"# After\n\nPost rule\n"
        )
        expected = "# Before\n\nPre rule\n\n# After\n\nPost rule\n"
        self.assertEqual(removed_content(content), expected)

    def test_return_unchanged_content_when_markers_absent(self):
        content = "# Custom project rules\n\nNo toolkit markers here.\n"
        self.assertEqual(removed_content(content), content)

    def test_updated_content_appends_when_no_markers(self):
        existing = "# Project rules\n"
        block = f"{BEGIN}\nManaged\n{END}\n"
        self.assertEqual(updated_content(existing, block), f"# Project rules\n\n{block}")

    def test_updated_content_replaces_existing_managed_block(self):
        existing = f"# Project\n\n{BEGIN}\nOld\n{END}\n\n# Extra\n"
        block = f"{BEGIN}\nNew\n{END}\n"
        self.assertEqual(
            updated_content(existing, block),
            f"# Project\n\n{BEGIN}\nNew\n{END}\n\n# Extra\n",
        )

    def test_managed_block_reads_toolkit_agents_md(self):
        with tempfile.TemporaryDirectory() as td:
            toolkit = Path(td)
            (toolkit / "AGENTS.md").write_text("# Master Rules\n", encoding="utf-8")
            block = managed_block(toolkit)
            self.assertEqual(block, f"{BEGIN}\n# Master Rules\n{END}\n")

    def test_diff_content_produces_unified_diff(self):
        diff = diff_content("line1\n", "line2\n", Path("AGENTS.md"))
        diff_text = "".join(diff)
        self.assertIn("--- AGENTS.md (current)", diff_text)
        self.assertIn("+++ AGENTS.md (proposed)", diff_text)
        self.assertIn("-line1", diff_text)
        self.assertIn("+line2", diff_text)

    # -------------------------------------------------------------------------
    # Whitespace preservation tests (P-00002)
    # -------------------------------------------------------------------------

    def test_preserve_two_trailing_spaces_markdown_hard_break(self):
        content = f"# Heading\nLine with break  \n\n{BEGIN}\n# Managed\n{END}\n"
        self.assertEqual(removed_content(content), "# Heading\nLine with break  \n")

    def test_preserve_trailing_tab_on_nonblank_project_authored_line(self):
        content = f"# Heading\nLine with tab\t\n\n{BEGIN}\n# Managed\n{END}\n"
        self.assertEqual(removed_content(content), "# Heading\nLine with tab\t\n")

    def test_preserve_indented_project_content_after_managed_block(self):
        content = f"{BEGIN}\n# Managed\n{END}\n\n    def code():\n        pass\n"
        self.assertEqual(removed_content(content), "    def code():\n        pass\n")

    def test_normalize_whitespace_only_separator_lines_without_retaining_separators(self):
        content = f"# Before\n   \n\t\n{BEGIN}\n# Managed\n{END}\n\t\n   \n# After\n"
        self.assertEqual(removed_content(content), "# Before\n\n# After\n")

    def test_return_empty_content_when_only_whitespace_and_managed_block_exist(self):
        content = f"   \n\t\n{BEGIN}\n# Managed\n{END}\n\t\n   \n"
        self.assertEqual(removed_content(content), "")


if __name__ == "__main__":
    unittest.main()
