from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from runner.export import export_project
from runner.filesystem import scaffold_project
from runner.review import build_review


class ReviewAndExportTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp()) / "book"
        scaffold_project(self.root, idea="test", adapter="fake", model_name="fake", language="en")
        chapters = self.root / "manuscript" / "chapters"
        chapters.mkdir(exist_ok=True)
        (chapters / "chapter-01.md").write_text("# One\n\n<script>alert(1)</script>", encoding="utf-8")
    def tearDown(self): shutil.rmtree(self.root.parent, ignore_errors=True)
    def test_review_escapes_manuscript_html_and_is_self_contained(self):
        page = build_review(self.root)
        text = page.read_text(encoding="utf-8")
        self.assertIn("Content-Security-Policy", text)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", text)
        self.assertNotIn("https://", text)
    def test_epub_has_required_entries_and_uncompressed_first_mimetype(self):
        path = export_project(self.root, "epub")
        with zipfile.ZipFile(path) as book:
            self.assertEqual("mimetype", book.namelist()[0])
            self.assertEqual(zipfile.ZIP_STORED, book.getinfo("mimetype").compress_type)
            self.assertIn("META-INF/container.xml", book.namelist())
            self.assertIn("OEBPS/package.opf", book.namelist())
            self.assertIn("OEBPS/nav.xhtml", book.namelist())
    def test_export_refuses_replacing_a_canonical_file(self):
        with self.assertRaises(ValueError):
            export_project(self.root, "markdown", self.root / "manuscript" / "chapters" / "chapter-01.md", True)
