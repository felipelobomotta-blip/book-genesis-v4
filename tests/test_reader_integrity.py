"""Integrity checks for the offline manuscript reader."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from runner.filesystem import scaffold_project, update_state_value
from runner.review import _unified_diff, build_review, chapters


class ReaderIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp())
        self.root = self.temp / "book"
        scaffold_project(self.root, idea="test", adapter="fake", model_name="fake", language="pt-BR")
        self.chapter = self.root / "manuscript" / "chapters" / "chapter-01.md"
        self.chapter.write_text("# Um\n\nTexto canônico", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.temp, ignore_errors=True)

    def test_reader_has_mobile_css_localized_controls_and_safe_xss_data(self) -> None:
        self.chapter.write_text("# <script>x</script>\n\n</script><img src=x onerror=1>", encoding="utf-8")
        page = build_review(self.root).read_text(encoding="utf-8")
        self.assertIn('name="viewport"', page)
        self.assertIn("@media (max-width: 40rem)", page)
        self.assertIn("Versão exibida", page)
        self.assertIn("Comparar com", page)
        self.assertIn("Diferenças entre versões", page)
        self.assertIn("&lt;script&gt;x&lt;/script&gt;", page)
        self.assertIn("\\u003ch1>", page)
        self.assertNotIn("</script><img src=x", page)
        self.assertNotIn('src="https://', page)
        self.assertIn("script-src 'sha256-", page)

    def test_editorial_rejection_is_visible_above_the_manuscript(self) -> None:
        update_state_value(self.root / "PROJECT_STATE.yaml", "status", "awaiting_revision")
        (self.root / "artifacts/08-adversarial-audit.md").write_text("# Auditoria\n\naudit_status: major_rewrite\n\nO desfecho não fecha o conflito.", encoding="utf-8")
        page = build_review(self.root).read_text(encoding="utf-8")
        self.assertIn("Revisão editorial pendente", page)
        self.assertIn('href="#editorial-audit"', page)
        self.assertIn("O desfecho não fecha o conflito", page)
        self.assertLess(page.index("Revisão editorial pendente"), page.index('<main id="manuscript">'))

    def test_history_uses_verified_accepted_attempt_and_precomputed_unified_diff(self) -> None:
        history_dir = self.root / "manuscript" / "chapters" / "history" / "chapter-01"
        history_dir.mkdir(parents=True)
        draft = history_dir / "draft.md"
        draft.write_text("# Um\n\nTexto anterior", encoding="utf-8")
        digest = hashlib.sha256(self.chapter.read_bytes()).hexdigest()
        draft.write_bytes(self.chapter.read_bytes())
        manifest = {
            "schema_version": "book-genesis.chapter-history/v1",
            "chapter": 1,
            "accepted": {"attempt_id": "a2", "draft_path": "manuscript/chapters/history/chapter-01/draft.md", "sha256": digest},
            "attempts": [
                {"attempt_id": "a10", "sequence": 10, "status": "failed", "draft_path": "manuscript/chapters/history/chapter-01/draft.md"},
                {"attempt_id": "a2", "sequence": 2, "status": "accepted", "draft_path": "manuscript/chapters/history/chapter-01/draft.md"},
            ],
        }
        (history_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = chapters(self.root, pt=True)[0]
        self.assertEqual(["Tentativa 2 — aceita (hash verificado)", "Tentativa 10 — falhou"], [version.label for version in result.versions])
        page = build_review(self.root).read_text(encoding="utf-8")
        self.assertIn("baseline", page)
        self.assertIn("--- baseline", _unified_diff("um\n", "dois\n"))
        self.assertIn("+++ displayed", _unified_diff("um\n", "dois\n"))
        self.assertIn("As versões são idênticas.", page)

    def test_tampered_canonical_never_claims_accepted_history(self) -> None:
        history_dir = self.root / "manuscript" / "chapters" / "history" / "chapter-01"
        history_dir.mkdir(parents=True)
        draft = history_dir / "draft.md"
        draft.write_text("# Um\n\nAntigo", encoding="utf-8")
        manifest = {
            "schema_version": "book-genesis.chapter-history/v1",
            "chapter": 1,
            "accepted": {"attempt_id": "a1", "draft_path": "manuscript/chapters/history/chapter-01/draft.md", "sha256": hashlib.sha256(draft.read_bytes()).hexdigest()},
            "attempts": [{"attempt_id": "a1", "sequence": 1, "status": "accepted", "draft_path": "manuscript/chapters/history/chapter-01/draft.md"}],
        }
        (history_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        result = chapters(self.root, pt=True)[0]
        self.assertNotIn("aceita (hash verificado)", result.versions[0].label)
        self.assertTrue(result.warnings)

    def test_malformed_history_and_unsafe_output_are_refused(self) -> None:
        history_dir = self.root / "manuscript" / "chapters" / "history" / "chapter-01"
        history_dir.mkdir(parents=True)
        (history_dir / "manifest.json").write_text("{broken", encoding="utf-8")
        self.assertTrue(chapters(self.root, pt=True)[0].warnings)
        with self.assertRaises(ValueError):
            build_review(self.root, self.root / "outside.html")

    def test_symlinked_report_is_not_read_when_supported(self) -> None:
        outside = self.temp / "outside.md"
        outside.write_text("# outside", encoding="utf-8")
        report = self.root / "RUN_REPORT.md"
        report.unlink()
        try:
            report.symlink_to(outside)
        except (NotImplementedError, OSError):
            self.skipTest("symlink creation is unavailable on this platform")
        page = build_review(self.root).read_text(encoding="utf-8")
        self.assertIn("não é seguro", page)
        self.assertNotIn("# outside", page)
