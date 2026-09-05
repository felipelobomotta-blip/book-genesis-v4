"""Atomic, local Markdown and EPUB 3 exports of canonical chapters."""
from __future__ import annotations

from datetime import datetime, timezone
import html
import os
from pathlib import Path
import tempfile
import uuid
import zipfile

from runner.book import count_chapters
from runner.filesystem import load_state_summary
from runner.review import CHAPTER, render_markdown


def _chapters(project: Path) -> list[tuple[int, str]]:
    folder = project / "manuscript" / "chapters"
    found = []
    if folder.is_dir():
        for path in folder.iterdir():
            match = CHAPTER.fullmatch(path.name)
            if not match or not path.is_file():
                continue
            if not path.resolve().is_relative_to(project):
                raise ValueError(f"Chapter path leaves the project: {path.name}")
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                raise ValueError(f"Chapter is empty: {path.name}")
            found.append((int(match.group(1)), text))
    found.sort()
    if not found:
        raise ValueError("No canonical chapters are available for export.")
    if len({number for number, _ in found}) != len(found):
        raise ValueError("Duplicate chapter numbers; resolve them before exporting.")
    return found


def _destination(project: Path, output: Path) -> Path:
    raw = Path(os.path.abspath(output))
    if raw.is_symlink():
        raise ValueError("Export output must not be a symlink.")
    resolved = raw.resolve()
    exports = project / "exports"
    if raw.is_relative_to(project) or resolved.is_relative_to(project):
        if exports.is_symlink() or not raw.is_relative_to(exports) or not resolved.is_relative_to(exports):
            raise ValueError("Inside a project, export output must be in exports/; project inputs are protected.")
    if resolved.exists() and not resolved.is_file():
        raise ValueError("Export output must be a regular file.")
    return resolved


def _coverage(project: Path, state: dict, found: list[tuple[int, str]], pt: bool) -> str:
    outline = project / "artifacts" / "05-outline.md"
    planned = None
    if outline.is_file() and outline.resolve().is_relative_to(project):
        try:
            planned = count_chapters(outline.read_text(encoding="utf-8"))
        except ValueError:
            pass
    complete = state.get("status") == "completed" and planned is not None and [n for n, _ in found] == list(range(1, planned + 1))
    numbers = ", ".join(str(number) for number, _ in found)
    if pt:
        status = "Todas as etapas do projeto foram concluídas." if complete else "Exportação parcial; a conclusão da obra ainda não foi verificada."
        count = f"{len(found)} de {planned}" if planned else str(len(found))
        return f"Cobertura: {count} capítulo(s) canônico(s), números {numbers}. {status}"
    status = "All project stages are complete." if complete else "Partial export; completion of the work has not been verified."
    count = f"{len(found)} of {planned}" if planned else str(len(found))
    return f"Coverage: {count} canonical chapter(s), numbers {numbers}. {status}"


def export_project(project: Path, fmt: str, output: Path | None = None, overwrite: bool = False) -> Path:
    project = project.resolve()
    if fmt not in {"markdown", "epub"}:
        raise ValueError("Format must be markdown or epub.")
    state_file = project / "PROJECT_STATE.yaml"
    if not state_file.is_file() or not state_file.resolve().is_relative_to(project):
        raise ValueError(f"Not a safe Book Genesis project: {project}")
    found = _chapters(project)
    state = load_state_summary(project)
    pt = state.get("language", "").lower().startswith(("pt", "por"))
    coverage = _coverage(project, state, found, pt)
    extension = "md" if fmt == "markdown" else "epub"
    output = _destination(project, output or project / "exports" / f"manuscript.{extension}")
    if output.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite {output}; pass --overwrite to replace an export.")
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".book-genesis-export-", dir=output.parent)
    os.close(descriptor)
    staged = Path(name)
    try:
        title = state.get("title") or ("Manuscrito sem título" if pt else "Untitled manuscript")
        if fmt == "markdown":
            sections = [f"# {title}", f"> {coverage}", *(text.rstrip() for _, text in found)]
            staged.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
        else:
            _epub(staged, project, found, state, title, coverage, pt)
        os.replace(staged, output)
    finally:
        staged.unlink(missing_ok=True)
    return output


def _xhtml(title: str, language: str, body: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<html xmlns="http://www.w3.org/1999/xhtml" '
        f'xml:lang="{html.escape(language, quote=True)}" lang="{html.escape(language, quote=True)}">'
        f'<head><title>{html.escape(title)}</title></head><body>{body}</body></html>'
    )


def _epub(output: Path, project: Path, found: list[tuple[int, str]], state: dict,
          title: str, coverage: str, pt: bool) -> None:
    language = state.get("language") or "en"
    chapter_label = "Capítulo" if pt else "Chapter"
    contents_label = "Índice" if pt else "Contents"
    coverage_label = "Sobre esta exportação" if pt else "About this export"
    identifier = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, project.as_uri())}"
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entries = [(f"chapter-{number:02d}.xhtml", f"{chapter_label} {number}", text) for number, text in found]
    nav_items = [f'<li><a href="coverage.xhtml">{coverage_label}</a></li>']
    nav_items += [f'<li><a href="{name}">{label}</a></li>' for name, label, _ in entries]
    nav_body = (
        f'<nav xmlns:epub="http://www.idpf.org/2007/ops" epub:type="toc" id="toc">'
        f'<h1>{contents_label}</h1><ol>{"".join(nav_items)}</ol></nav>'
    )
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="coverage" href="coverage.xhtml" media-type="application/xhtml+xml"/>',
    ]
    manifest += [f'<item id="c{i}" href="{name}" media-type="application/xhtml+xml"/>' for i, (name, _, _) in enumerate(entries, 1)]
    spine = '<itemref idref="coverage"/>' + "".join(f'<itemref idref="c{i}"/>' for i in range(1, len(entries) + 1))
    package = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id">'
        '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
        f'<dc:identifier id="book-id">{identifier}</dc:identifier>'
        f'<dc:title>{html.escape(title)}</dc:title><dc:language>{html.escape(language)}</dc:language>'
        f'<dc:description>{html.escape(coverage)}</dc:description>'
        f'<meta property="dcterms:modified">{modified}</meta></metadata>'
        f'<manifest>{"".join(manifest)}</manifest><spine>{spine}</spine></package>'
    )
    container = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
        '<rootfiles><rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>'
        '</rootfiles></container>'
    )
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container)
        archive.writestr("OEBPS/package.opf", package)
        archive.writestr("OEBPS/nav.xhtml", _xhtml(contents_label, language, nav_body))
        archive.writestr("OEBPS/coverage.xhtml", _xhtml(coverage_label, language, f"<h1>{html.escape(title)}</h1><p>{html.escape(coverage)}</p>"))
        for name, label, prose in entries:
            archive.writestr("OEBPS/" + name, _xhtml(label, language, render_markdown(prose)))
