"""Exports preserve source files and remain readable XML after real prose escaping."""
from pathlib import Path
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile

import pytest
from runner.export import export_project
from runner.filesystem import scaffold_project
from runner.review import render_markdown


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "livro"
    scaffold_project(root, idea="uma biblioteca", adapter="fake", model_name="fake", language="pt-BR")
    (root / "manuscript/chapters/chapter-01.md").write_text(
        '# A devolução\n\n“Ela voltou & esperou.”\nOutra linha <script>alert(1)</script>.\n', encoding="utf-8")
    return root


def test_epub_documents_are_xml_and_have_metadata_and_partial_coverage(project):
    path = export_project(project, "epub")
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.endswith((".xml", ".opf", ".xhtml")):
                doc = ET.fromstring(archive.read(name))
                if name.endswith(".xhtml"):
                    assert doc.find("{http://www.w3.org/1999/xhtml}head/{http://www.w3.org/1999/xhtml}title") is not None
        package = ET.fromstring(archive.read("OEBPS/package.opf"))
        ns = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
        assert package.find("opf:metadata/dc:language", ns).text == "pt-BR"
        assert package.find("opf:metadata/opf:meta[@property='dcterms:modified']", ns).text.endswith("Z")
        assert "parcial" in package.find("opf:metadata/dc:description", ns).text
        assert b"&lt;script&gt;" in archive.read("OEBPS/chapter-01.xhtml")
        assert "Exportação parcial" in archive.read("OEBPS/coverage.xhtml").decode()


def test_emphasis_and_quotes_render_as_safe_xhtml():
    markup = render_markdown('**Forte** e *itálico*.\n\n> *<script>alert(1)</script>*\n\n---')
    root = ET.fromstring('<body>' + markup + '</body>')
    assert root.find('p/strong').text == 'Forte'
    assert root.find('p/em').text == 'itálico'
    assert root.find('blockquote/p/em').text == '<script>alert(1)</script>'
    assert root.find('hr') is not None


def test_identifier_belongs_to_project_not_export_path(project, tmp_path):
    first = export_project(project, "epub")
    second = export_project(project, "epub", tmp_path / "different-location.epub")
    def identifier(path):
        with zipfile.ZipFile(path) as archive:
            return ET.fromstring(archive.read("OEBPS/package.opf")).find(".//{http://purl.org/dc/elements/1.1/}identifier").text
    assert identifier(first) == identifier(second)


def test_only_export_can_be_overwritten_and_failure_preserves_it(project):
    path = export_project(project, "markdown")
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        export_project(project, "markdown")
    with patch("runner.export.os.replace", side_effect=OSError("disk unavailable")):
        with pytest.raises(OSError):
            export_project(project, "markdown", overwrite=True)
    assert path.read_bytes() == original
    assert not list(path.parent.glob(".book-genesis-export-*"))
    assert export_project(project, "markdown", overwrite=True) == path
    for relative in ("PROJECT_STATE.yaml", "ASSUMPTIONS.md", "artifacts/00-brief.md", "manuscript/chapters/chapter-01.md"):
        source = project / relative
        before = source.read_bytes()
        with pytest.raises(ValueError):
            export_project(project, "markdown", source, overwrite=True)
        assert source.read_bytes() == before


def test_empty_or_duplicate_chapters_are_not_exported(project):
    canonical = project / "manuscript/chapters/chapter-01.md"
    duplicate = canonical.with_name("chapter-1.md")
    duplicate.write_bytes(canonical.read_bytes())
    with pytest.raises(ValueError, match="Duplicate"):
        export_project(project, "epub")
    duplicate.unlink()
    canonical.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        export_project(project, "epub")


def test_symlink_cannot_redirect_export_into_inputs(project):
    target = project / "ASSUMPTIONS.md"
    before = target.read_bytes()
    link = project / "exports"
    try:
        link.symlink_to(project, target_is_directory=True)
    except OSError:
        pytest.skip("Platform does not allow unprivileged symlinks")
    with pytest.raises(ValueError):
        export_project(project, "markdown", link / target.name, overwrite=True)
    assert target.read_bytes() == before
