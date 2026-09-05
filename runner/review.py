"""Build a safe, local reader for canonical Book Genesis manuscripts.

The reader intentionally has no network dependencies. It is a reading aid, not
evidence that a manuscript is ready to publish.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import base64
import difflib
import hashlib
import html
import json
from pathlib import Path
import re
from typing import Any

from runner.filesystem import load_state_summary


CHAPTER = re.compile(r"^chapter-(\d+)\.md$")
DRAFT = re.compile(r"^draft-(\d+)\.md$")
SCHEMA = "book-genesis.chapter-history/v1"


@dataclass(frozen=True)
class Version:
    """One inspectable text version belonging to a canonical chapter."""

    label: str
    path: Path
    source: str


@dataclass(frozen=True)
class ReviewChapter:
    """A canonical chapter, its available versions, and history warnings."""

    number: int
    canonical: Path
    versions: tuple[Version, ...]
    warnings: tuple[str, ...] = field(default_factory=tuple)


def _inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def _has_symlink_component(root: Path, candidate: Path) -> bool:
    """Reject a path that crosses an existing symlink below ``root``."""

    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return True
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.exists() and cursor.is_symlink():
            return True
    return False


def _safe_file(root: Path, path: Path) -> bool:
    return (
        path.is_file()
        and not path.is_symlink()
        and not _has_symlink_component(root, path)
        and _inside(root, path)
    )


def _history_path(root: Path, value: object) -> Path | None:
    """Resolve a history path only when it is a regular, project-local file."""

    if not isinstance(value, str) or not value or "\\" in value:
        return None
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    candidate = root / relative
    return candidate if _safe_file(root, candidate) else None


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _phrase(pt: bool, english: str, portuguese: str) -> str:
    return portuguese if pt else english


def _history(root: Path, number: int, canonical: Path, pt: bool) -> tuple[list[Version], list[str]]:
    """Read a runtime history manifest without trusting it blindly."""

    manifest = root / "manuscript" / "chapters" / "history" / f"chapter-{number:02d}" / "manifest.json"
    if not manifest.exists():
        return [], []
    if not _safe_file(root, manifest):
        return [], [_phrase(pt, "History was ignored because its manifest is unsafe.", "O histórico foi ignorado porque o manifesto não é seguro.")]
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], [_phrase(pt, "History was ignored because its manifest is malformed.", "O histórico foi ignorado porque o manifesto está malformado.")]

    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA or data.get("chapter") != number:
        return [], [_phrase(pt, "History was ignored because its schema does not match this chapter.", "O histórico foi ignorado porque o esquema não corresponde a este capítulo.")]
    raw_attempts = data.get("attempts")
    if not isinstance(raw_attempts, list):
        return [], [_phrase(pt, "History was ignored because attempts are missing.", "O histórico foi ignorado porque as tentativas estão ausentes.")]

    attempts = [item for item in raw_attempts if isinstance(item, dict)]
    warnings: list[str] = []
    if len(attempts) != len(raw_attempts):
        warnings.append(_phrase(pt, "Some malformed history attempts were ignored.", "Algumas tentativas malformadas do histórico foram ignoradas."))
    attempts.sort(key=_attempt_sequence)

    accepted = data.get("accepted")
    accepted_id: object = None
    accepted_is_verified = False
    if accepted is not None:
        if not isinstance(accepted, dict):
            warnings.append(_phrase(pt, "The accepted-history entry is malformed.", "A entrada de histórico aceita está malformada."))
        else:
            accepted_id = accepted.get("attempt_id")
            draft = _history_path(root, accepted.get("draft_path"))
            expected_digest = accepted.get("sha256")
            matching = next(
                (
                    item
                    for item in attempts
                    if item.get("attempt_id") == accepted_id and item.get("status") == "accepted"
                ),
                None,
            )
            if (
                draft is not None
                and matching is not None
                and isinstance(expected_digest, str)
                and expected_digest == _digest(draft)
                and expected_digest == _digest(canonical)
            ):
                accepted_is_verified = True
            else:
                warnings.append(
                    _phrase(
                        pt,
                        "The accepted-history entry does not match the canonical chapter and is not labelled accepted.",
                        "A entrada aceita do histórico não corresponde ao capítulo canônico e não é rotulada como aceita.",
                    )
                )

    versions: list[Version] = []
    for item in attempts:
        draft = _history_path(root, item.get("draft_path"))
        if draft is None:
            if item.get("draft_path"):
                warnings.append(_phrase(pt, "A history draft path was ignored because it is unsafe or unavailable.", "Um caminho de rascunho do histórico foi ignorado porque não é seguro ou não está disponível."))
            continue
        sequence = _attempt_sequence(item)
        status = _status_label(item.get("status"), pt)
        if accepted_is_verified and item.get("attempt_id") == accepted_id:
            label = _phrase(pt, "Attempt %s — accepted (hash verified)", "Tentativa %s — aceita (hash verificado)") % sequence
        else:
            label = _phrase(pt, "Attempt %s — %s", "Tentativa %s — %s") % (sequence, status)
        versions.append(Version(label, draft, "runtime history"))
    return versions, warnings


def _attempt_sequence(item: dict[str, Any]) -> int:
    sequence = item.get("sequence")
    return sequence if isinstance(sequence, int) and sequence >= 0 else 10**9


def _status_label(value: object, pt: bool) -> str:
    status = value if isinstance(value, str) else "unknown"
    portuguese = {
        "pending": "pendente",
        "drafted": "rascunhada",
        "judged": "avaliada",
        "accepted": "aceita",
        "rejected": "rejeitada",
        "failed": "falhou",
        "unknown": "desconhecida",
    }
    return portuguese.get(status, "desconhecida") if pt else status


def chapters(project: Path, pt: bool = False) -> list[ReviewChapter]:
    """Return canonical chapters in numeric order, with safe history when present."""

    root = project.resolve()
    folder = root / "manuscript" / "chapters"
    if not folder.is_dir() or folder.is_symlink():
        return []

    result: list[ReviewChapter] = []
    for path in folder.iterdir():
        match = CHAPTER.fullmatch(path.name)
        if match is None or not _safe_file(root, path):
            continue
        number = int(match.group(1))
        versions, warnings = _history(root, number, path, pt)
        if not versions:
            legacy_versions, legacy_warnings = _legacy_versions(root, number, pt)
            versions.extend(legacy_versions)
            warnings.extend(legacy_warnings)
        result.append(ReviewChapter(number, path, tuple(versions), tuple(dict.fromkeys(warnings))))
    return sorted(result, key=lambda chapter: chapter.number)


def _legacy_versions(root: Path, number: int, pt: bool) -> tuple[list[Version], list[str]]:
    drafts = root / "manuscript" / "drafts" / f"chapter-{number:02d}"
    if not drafts.exists() or not drafts.is_dir() or drafts.is_symlink() or _has_symlink_component(root, drafts):
        return [], []
    versions: list[Version] = []
    for draft in sorted(drafts.iterdir(), key=lambda item: item.name):
        match = DRAFT.fullmatch(draft.name)
        if match is not None and _safe_file(root, draft):
            label = _phrase(pt, "Draft %s — legacy; acceptance unknown", "Rascunho %s — legado; aceitação desconhecida") % match.group(1)
            versions.append(Version(label, draft, "legacy draft"))
    return versions, []


def render_markdown(text: str, empty: str = "No readable text.") -> str:
    """Render a deliberately small, escaped Markdown subset for prose reading."""

    blocks: list[str] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append("<p>" + "<br />".join(_inline_prose(line) for line in paragraph) + "</p>")
            paragraph.clear()

    for line in text.replace("\r\n", "\n").split("\n"):
        heading = re.match(r"^(#{1,3})\s+(.*)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            blocks.append(f"<h{level}>{_inline_prose(heading.group(2))}</h{level}>")
        elif line.startswith("> "):
            flush_paragraph()
            blocks.append(f"<blockquote><p>{_inline_prose(line[2:])}</p></blockquote>")
        elif line.strip() in {"---", "***"}:
            flush_paragraph()
            blocks.append("<hr />")
        elif line.strip():
            paragraph.append(line)
        else:
            flush_paragraph()
    flush_paragraph()
    return "\n".join(blocks) or f"<p><em>{html.escape(empty)}</em></p>"


def _inline_prose(text: str) -> str:
    """Escape HTML first, then permit only emphasis markup generated here."""
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*([^*\n]+)\*\*", r"<strong>\1</strong>", escaped)
    return re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", escaped)


def build_review(project: Path, output: Path | None = None) -> Path:
    """Write an offline reader inside ``project/review`` and return its path."""

    root = project.resolve()
    state_path = root / "PROJECT_STATE.yaml"
    if not root.is_dir() or not _safe_file(root, state_path):
        raise ValueError(f"Not a safe Book Genesis project: {project}")

    review_root = root / "review"
    target = _review_target(root, review_root, output)
    state = load_state_summary(root)
    pt = state.get("language", "").lower().startswith(("pt", "por"))
    labels = _labels(pt)
    all_chapters = chapters(root, pt)
    report = root / "RUN_REPORT.md"
    report_html = ""
    if report.exists():
        if _safe_file(root, report):
            report_html = (
                f'<section class="report" aria-labelledby="runtime-report">'
                f'<h2 id="runtime-report">{labels["report"]}</h2>'
                f'<p class="notice">{labels["notice"]}</p>'
                f'{render_markdown(report.read_text(encoding="utf-8", errors="replace"), labels["empty"])}</section>'
            )
        else:
            report_html = f'<p class="warning" role="status">{labels["unsafe_report"]}</p>'

    payload = _reader_payload(all_chapters, labels)
    audit = root / "artifacts" / "08-adversarial-audit.md"
    if _safe_file(root, audit):
        audit_text = audit.read_text(encoding="utf-8")
        if audit_text.strip() and "BOOK_GENESIS_TEMPLATE" not in audit_text:
            audit_title = _phrase(pt, "Editorial audit", "Auditoria editorial")
            report_html = f'<section class="report" id="editorial-audit"><h2>{audit_title}</h2>{render_markdown(audit_text)}</section>' + report_html
    if state.get("status") == "awaiting_revision":
        message = _phrase(pt, "Editorial revision is required. Read the audit before continuing.", "Revisão editorial pendente. Leia a auditoria antes de continuar.")
        status_notice = f'<p class="warning" role="status"><a href="#editorial-audit">{message}</a></p>'
    else:
        message = _phrase(pt, "A local reading copy. Publication still requires human editorial review.", "Cópia para leitura local. A publicação ainda depende de revisão editorial humana.")
        status_notice = f'<p class="notice">{message}</p>'
    page = _page(title=state.get("title") or root.name, labels=labels, chapters_data=all_chapters, payload=payload, report_html=report_html, status_notice=status_notice)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(page, encoding="utf-8")
    return target


def _review_target(root: Path, review_root: Path, output: Path | None) -> Path:
    review_root.mkdir(parents=True, exist_ok=True)
    if review_root.is_symlink() or not _inside(root, review_root):
        raise ValueError("Review folder must be a real folder inside the project")
    requested = output if output is not None else review_root / "index.html"
    target = requested.resolve(strict=False)
    if not _inside(review_root, target) or _has_symlink_component(root, target):
        raise ValueError("Review output must be a regular file inside the project review folder")
    if target.exists() and (not target.is_file() or target.is_symlink()):
        raise ValueError("Review output must be a regular file inside the project review folder")
    return target


def _labels(pt: bool) -> dict[str, str]:
    if pt:
        return {"chapter":"Capítulo", "version":"Versão exibida", "baseline":"Comparar com", "comparison":"Diferenças entre versões", "identical":"As versões são idênticas.", "empty":"Ainda não há texto legível.", "no_chapters":"Ainda não há capítulos canônicos para ler.", "reader":"Leitor do manuscrito", "report":"Relatório interno de modelos", "notice":"Este é um sinal interno do runtime/modelos. Não é leitura humana, memória tardia, nota literária nem prontidão para publicação.", "unsafe_report":"O relatório interno foi ignorado porque não é seguro.", "warning":"Atenção ao histórico", "skip":"Ir para o conteúdo"}
    return {"chapter":"Chapter", "version":"Displayed version", "baseline":"Compare with", "comparison":"Version differences", "identical":"Versions are identical.", "empty":"There is no readable text yet.", "no_chapters":"There are no canonical chapters to read yet.", "reader":"Manuscript reader", "report":"Internal model report", "notice":"This is a runtime/model signal. It is not human reading, later memory, a literary score, or publication readiness.", "unsafe_report":"The internal report was ignored because it is unsafe.", "warning":"History warning", "skip":"Skip to content"}


def _reader_payload(chapter_list: list[ReviewChapter], labels: dict[str, str]) -> str:
    pt = labels["chapter"] == "Capítulo"
    payload: dict[str, Any] = {"identical": labels["identical"], "chapters": {}}
    for chapter in chapter_list:
        versions = [Version(_phrase(pt, "Canonical manuscript", "Manuscrito canônico"), chapter.canonical, "canonical"), *chapter.versions]
        texts = [version.path.read_text(encoding="utf-8", errors="replace") for version in versions]
        diffs = {f"{base}:{current}": _unified_diff(texts[base], texts[current]) for base in range(len(texts)) for current in range(len(texts))}
        payload["chapters"][str(chapter.number)] = {
            "html": [render_markdown(text, labels["empty"]) for text in texts],
            "diffs": diffs,
        }
    return json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")


def _unified_diff(before: str, after: str) -> str:
    if before == after:
        return ""
    return "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(), fromfile="baseline", tofile="displayed", lineterm=""))


def _page(*, title: str, labels: dict[str, str], chapters_data: list[ReviewChapter], payload: str, report_html: str, status_notice: str = "") -> str:
    safe_title = html.escape(title)
    navigation = "".join(f'<a href="#chapter-{chapter.number}">{labels["chapter"]} {chapter.number}</a>' for chapter in chapters_data)
    content = "".join(_chapter_section(chapter, labels) for chapter in chapters_data) or f'<p class="empty">{html.escape(labels["no_chapters"])}</p>'
    script_hash = base64.b64encode(hashlib.sha256(_SCRIPT.encode("utf-8")).digest()).decode("ascii")
    csp = f"default-src 'none'; style-src 'unsafe-inline'; script-src 'sha256-{script_hash}'; base-uri 'none'; form-action 'none'"
    lang = "pt-BR" if labels["chapter"] == "Capítulo" else "en"
    return f'''<!doctype html>
<html lang="{lang}"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<meta http-equiv="Content-Security-Policy" content="{csp}" /><title>{safe_title} — {html.escape(labels["reader"])}</title><style>{_STYLE}</style></head>
<body><a class="skip" href="#manuscript">{html.escape(labels["skip"])}</a><header class="masthead"><p class="eyebrow">BOOK GENESIS</p><h1>{safe_title}</h1>{status_notice}</header>
<nav class="chapters" aria-label="{html.escape(labels["reader"])}">{navigation}</nav><main id="manuscript">{content}{report_html}</main>
<script id="reader-data" type="application/json">{payload}</script><script>{_SCRIPT}</script></body></html>'''


def _chapter_section(chapter: ReviewChapter, labels: dict[str, str]) -> str:
    pt = labels["chapter"] == "Capítulo"
    versions = [Version(_phrase(pt, "Canonical manuscript", "Manuscrito canônico"), chapter.canonical, "canonical"), *chapter.versions]
    options = "".join(f'<option value="{index}">{html.escape(version.label)}</option>' for index, version in enumerate(versions))
    warnings = "".join(f'<p class="warning" role="status"><strong>{html.escape(labels["warning"])}:</strong> {html.escape(warning)}</p>' for warning in chapter.warnings)
    return f'''<section class="chapter" id="chapter-{chapter.number}" data-chapter="{chapter.number}"><header class="chapter-heading"><p>{html.escape(labels["chapter"])} {chapter.number:02d}</p></header>{warnings}
<div class="controls"><label>{html.escape(labels["version"])}<select class="displayed-version" aria-label="{html.escape(labels["version"])}">{options}</select></label><label>{html.escape(labels["baseline"])}<select class="baseline-version" aria-label="{html.escape(labels["baseline"])}">{options}</select></label></div>
<article class="prose" tabindex="-1">{render_markdown(versions[0].path.read_text(encoding="utf-8", errors="replace"), labels["empty"])}</article><details class="comparison" open><summary>{html.escape(labels["comparison"])}</summary><pre aria-live="polite">{html.escape(labels["identical"])}</pre></details></section>'''


_STYLE = r"""
:root { color-scheme: light; --paper:#f8f1e3; --paper-deep:#ede0c9; --ink:#251d17; --muted:#6b5c4e; --accent:#8c432b; --line:#d7c6ab; }
* { box-sizing:border-box; } html { scroll-behavior:smooth; } body { margin:0; color:var(--ink); background:var(--paper); font-family:Georgia, 'Times New Roman', serif; font-size:18px; line-height:1.72; }
.skip { position:absolute; left:-10000px; top:auto; } .skip:focus { left:1rem; top:1rem; z-index:5; padding:.45rem .7rem; color:white; background:#201813; border-radius:.25rem; }
.masthead { max-width:48rem; margin:0 auto; padding:4.5rem 1.5rem 1.7rem; border-bottom:1px solid var(--line); } .eyebrow, .chapter-heading p { margin:0; color:var(--accent); font-family:ui-sans-serif,system-ui,sans-serif; font-size:.74rem; font-weight:800; letter-spacing:.13em; text-transform:uppercase; } h1 { margin:.25rem 0 0; font-size:clamp(2.2rem, 6vw, 4.5rem); line-height:1.03; letter-spacing:-.045em; }
.chapters { position:sticky; top:0; z-index:2; display:flex; gap:.3rem .85rem; overflow-x:auto; padding:.75rem max(1rem, calc((100vw - 46rem)/2)); background:rgba(248,241,227,.96); border-bottom:1px solid var(--line); font-family:ui-sans-serif,system-ui,sans-serif; font-size:.88rem; white-space:nowrap; } .chapters a { color:var(--ink); text-decoration:none; text-underline-offset:.2em; } .chapters a:hover, .chapters a:focus-visible { color:var(--accent); text-decoration:underline; }
main { max-width:48rem; margin:0 auto; padding:1.5rem 1.5rem 5rem; } .chapter { scroll-margin-top:4rem; padding:2.25rem 0 3.5rem; border-bottom:1px solid var(--line); } .controls { display:grid; grid-template-columns:1fr 1fr; gap:.8rem; margin:1.2rem 0 2rem; padding:1rem; background:var(--paper-deep); border-radius:.4rem; font-family:ui-sans-serif,system-ui,sans-serif; font-size:.78rem; font-weight:700; } label { display:grid; gap:.35rem; } select { width:100%; min-width:0; padding:.45rem; color:var(--ink); background:white; border:1px solid #9f8b72; border-radius:.25rem; font:inherit; } select:focus-visible, a:focus-visible, summary:focus-visible { outline:3px solid #276b78; outline-offset:2px; }
.prose { font-size:1.12rem; } .prose h1, .prose h2, .prose h3 { margin:2.2rem 0 .6rem; line-height:1.13; } .prose p { margin:0 0 1.25rem; } .comparison { margin-top:2.1rem; font-family:ui-sans-serif,system-ui,sans-serif; font-size:.88rem; } summary { cursor:pointer; color:var(--accent); font-weight:750; } pre { overflow:auto; min-height:3.3rem; margin:.7rem 0 0; padding:1rem; color:#262018; background:#f0e5d1; border-left:4px solid var(--accent); white-space:pre-wrap; font:.78rem/1.45 ui-monospace,SFMono-Regular,Consolas,monospace; } .warning { padding:.75rem 1rem; color:#4a2f12; background:#fff0c7; border-left:4px solid #9a5b00; font-family:ui-sans-serif,system-ui,sans-serif; font-size:.86rem; line-height:1.45; } .notice { color:var(--muted); font-family:ui-sans-serif,system-ui,sans-serif; font-size:.9rem; } .report { margin-top:3rem; padding:1.5rem; background:#f1e7d4; border-radius:.4rem; } .empty { color:var(--muted); }
.prose h1 { font-size:clamp(1.8rem, 3.5vw, 2.65rem); letter-spacing:-.025em; } .prose blockquote { margin:1.5rem 0; padding:.3rem 1.3rem; border-left:3px solid var(--line); color:var(--muted); } .report h1 { font-size:1.65rem; letter-spacing:-.02em; } .prose hr { border:0; border-top:1px solid var(--line); margin:2rem auto; width:30%; }
@media (max-width: 40rem) { body { font-size:17px; } .masthead { padding-top:2.8rem; } main { padding-inline:1rem; } .controls { grid-template-columns:1fr; } .prose { font-size:1.06rem; } } @media (prefers-contrast: more) { :root { --paper:#fff; --paper-deep:#eee; --ink:#000; --muted:#222; --line:#444; } }
""".strip()


_SCRIPT = r"""(() => {
  const dataNode = document.getElementById('reader-data');
  const data = JSON.parse(dataNode.textContent);
  const render = (section) => {
    const chapter = data.chapters[section.dataset.chapter];
    const displayed = section.querySelector('.displayed-version');
    const baseline = section.querySelector('.baseline-version');
    // HTML in this payload is emitted by render_markdown, which escapes every
    // manuscript line before it is serialized. No manuscript HTML is trusted.
    section.querySelector('.prose').innerHTML = chapter.html[Number(displayed.value)];
    const result = chapter.diffs[`${baseline.value}:${displayed.value}`];
    section.querySelector('pre').textContent = result || data.identical;
  };
  document.querySelectorAll('[data-chapter]').forEach((section) => {
    section.querySelectorAll('select').forEach((select) => select.addEventListener('change', () => render(section)));
    render(section);
  });
})();""".strip()
