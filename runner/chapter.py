"""The per-chapter loop.

writer -> disruptor (when the genre wants it) -> blind judge -> [editor -> judge]*
until the reader would turn the page and the new draft is not worse than the one
before it, or the genre's revision budget is spent. The runner owns every file;
the models only ever see text and return text (ADR 0001, decisions 1, 3, 4, 6, 11).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Dict, List, Optional

from runner.adapters import Adapter
from runner.brief import TAIL_WORDS, build_chapter_brief, tail_words
from runner.constants import GenreProfile, load_genre_profile
from runner.filesystem import load_state_summary
from runner.judge import Verdict, judge_chapter

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = REPO_ROOT / "agents"
FIRST_CHAPTER_SLUG = "chapter-01"

FLAG_MEANINGS = {
    "hook": "the first or last lines did not pull",
    "dialogue": "people sound alike, or say exactly what they mean",
    "pacing": "the reader skimmed",
    "ai_pattern": "it reads like a machine: balanced triplets, tidy morals, every metaphor explained",
    "exposition": "the reader was told instead of shown",
    "voice": "the narrator went generic",
    "continuity": "something contradicted what the reader had just read",
}

RUNNER_CONTRACT = (
    "# RUNNER CONTRACT (read this first)\n\n"
    "You are running inside the Book Genesis runner. You have NO tools: you cannot read, open, "
    "write, or update files, and there is no orchestrator to report to. Ignore every instruction "
    "below that asks you to do any of those things. Everything you need is in this message, and "
    "the runner saves what you return.\n\n"
)

_LEVEL_ONE_HEADING = re.compile(r"^#\s+\S")
_NOTES_HEADING = re.compile(
    r"^\s*(?:#{1,6}\s+|\*\*)(?:craft notes?|writer'?s notes?|author'?s notes?|self[- ]report|"
    r"notes? (?:for|to) the \w+|notes?)\b",
    re.IGNORECASE,
)
_OUTER_FENCE = re.compile(r"^```[a-zA-Z]*[ \t]*\r?\n(.*)\r?\n```\s*$", re.DOTALL)


class AwaitingHuman(RuntimeError):
    """Chapter 1 has to be read by a person before the runner writes chapter 2."""

    def __init__(self, chapter_path: Path, marker: Path) -> None:
        super().__init__(
            f"A human has to read {chapter_path} before chapter 2 is written. "
            f"When it holds up, run: book-genesis approve <project> {FIRST_CHAPTER_SLUG}"
        )
        self.chapter_path = chapter_path
        self.marker = marker


@dataclass
class ChapterResult:
    chapter: int
    accepted: bool
    status: str
    cycles: int
    draft_path: Optional[Path]
    verdicts: List[Verdict] = field(default_factory=list)


def approve(project: Path, slug: str) -> Path:
    approvals = project / "approvals"
    approvals.mkdir(parents=True, exist_ok=True)
    marker = approvals / f"{slug}.approved"
    marker.write_text("approved by a human reader\n", encoding="utf-8")
    return marker


def run_chapter(
    project: Path,
    chapter: int,
    adapters: Dict[str, Adapter],
    *,
    models: Optional[Dict[str, str]] = None,
) -> ChapterResult:
    models = models or {}
    if chapter > 1:
        marker = project / "approvals" / f"{FIRST_CHAPTER_SLUG}.approved"
        if not marker.exists():
            raise AwaitingHuman(project / "manuscript" / "chapters" / f"{FIRST_CHAPTER_SLUG}.md", marker)

    summary = load_state_summary(project)
    genre = summary.get("genre", "")
    reader = summary.get("audience", "")
    profile = load_genre_profile(genre)
    brief = build_chapter_brief(project, chapter)
    previous_tail = _previous_tail(project, chapter)

    drafts_dir = project / "manuscript" / "drafts" / f"chapter-{chapter:02d}"
    evaluations_dir = project / "evaluations"

    draft = clean_chapter(
        adapters["writer"].complete(writer_prompt(brief, chapter, genre, profile), model=models.get("writer", ""))
    )
    if profile.disruptor_default and "disruptor" in adapters:
        draft = clean_chapter(
            adapters["disruptor"].complete(disruptor_prompt(draft, chapter, genre), model=models.get("disruptor", ""))
        )

    draft_number = 1
    _write(drafts_dir / f"draft-{draft_number}.md", draft)
    verdict = judge_chapter(draft, previous_tail, genre, adapters["judge"], models.get("judge", ""), reader=reader)
    _write(evaluations_dir / f"chapter-{chapter:02d}-judge-{draft_number}.md", verdict.raw)
    verdicts = [verdict]

    best, best_verdict = draft, verdict
    accepted = _accepted(verdict)
    cycles = 0
    while not accepted and cycles < profile.max_revision_cycles:
        cycles += 1
        candidate = clean_chapter(
            adapters["editor"].complete(
                editor_prompt(best, best_verdict, chapter, genre, profile),
                model=models.get("editor", ""),
            )
        )
        draft_number += 1
        _write(drafts_dir / f"draft-{draft_number}.md", candidate)
        verdict = judge_chapter(
            candidate,
            previous_tail,
            genre,
            adapters["judge"],
            models.get("judge", ""),
            previous_draft=best,
            reader=reader,
        )
        _write(evaluations_dir / f"chapter-{chapter:02d}-judge-{draft_number}.md", verdict.raw)
        verdicts.append(verdict)
        if verdict.vs_previous != "worse":
            best, best_verdict = candidate, verdict
        accepted = _accepted(verdict)

    if accepted:
        final = project / "manuscript" / "chapters" / f"chapter-{chapter:02d}.md"
        _write(final, best)
        return ChapterResult(chapter, True, "accepted", cycles, final, verdicts)
    return ChapterResult(chapter, False, "blocked", cycles, drafts_dir / f"draft-{draft_number}.md", verdicts)


def writer_prompt(brief: str, chapter: int, genre: str, profile: GenreProfile) -> str:
    return (
        RUNNER_CONTRACT
        + _template("book-writer.md")
        + "\n\n# THE BRIEF\n\n"
        + brief.strip()
        + "\n\n# OUTPUT\n\n"
        + f"Return only Chapter {chapter}, as Markdown, starting with a level-1 heading of the form "
        + f"`# Chapter {chapter}: Title`. Prose only: no craft notes, no self-report, no preamble, no "
        + "commentary before or after the chapter. Stay inside the target length given in the brief "
        + f"({profile.words_per_chapter_min}-{profile.words_per_chapter_max} words unless the outline says otherwise).\n"
    )


def disruptor_prompt(draft: str, chapter: int, genre: str) -> str:
    return (
        RUNNER_CONTRACT
        + _template("book-disruptor.md")
        + f"\n\n# THE CHAPTER (Chapter {chapter}, {genre or 'fiction'})\n\n"
        + draft.strip()
        + "\n\n# OUTPUT\n\n"
        + "Return the full chapter with your disruptions applied, as Markdown, starting with the same "
        + "level-1 heading. Prose only: no report, no list of changes, nothing before or after the chapter.\n"
    )


def editor_prompt(draft: str, verdict: Verdict, chapter: int, genre: str, profile: GenreProfile) -> str:
    flags = [flag for flag in verdict.flags if flag in FLAG_MEANINGS]
    modes = "\n".join(f"- {flag}: {FLAG_MEANINGS[flag]}" for flag in flags) or (
        "- (no mode flagged: work only on the passage where the reader's attention left the page)"
    )
    remember = "\n".join(f"- {item}" for item in verdict.remember) or "- nothing"
    reader_report = (
        "# WHAT A BLIND READER SAID\n\n"
        f"- Would turn the page: {'yes' if verdict.turn_page else 'no'}\n"
        f"- Attention left the page at: {verdict.stopped_at}\n"
        f"- Would still remember tomorrow:\n{remember}\n"
        f"- Modes to run (see MODES in your instructions):\n{modes}\n\n"
    )
    return (
        RUNNER_CONTRACT
        + _template("book-editor.md")
        + "\n\n"
        + reader_report
        + f"# THE CHAPTER (current best draft of Chapter {chapter}, {genre or 'fiction'})\n\n"
        + draft.strip()
        + "\n\n# OUTPUT\n\n"
        + "Return the full revised chapter as Markdown, starting with the same level-1 heading. Touch "
        + "only what the reader flagged and the passage where attention left the page; do not undo what "
        + "already works; do not change facts, names, or the ending. Prose only: no change log, nothing "
        + "before or after the chapter.\n"
    )


def clean_chapter(raw: str) -> str:
    """Keep the prose, drop what models add around it: fences, preambles, craft notes."""
    text = raw.strip()
    fence = _OUTER_FENCE.match(text)
    if fence:
        text = fence.group(1).strip()
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if _LEVEL_ONE_HEADING.match(line):
            lines = lines[index:]
            break
    for index in range(1, len(lines)):
        if _NOTES_HEADING.match(lines[index]):
            lines = lines[:index]
            break
    while lines and lines[-1].strip() in ("", "---", "***"):
        lines.pop()
    return "\n".join(lines).rstrip() + "\n"


def _accepted(verdict: Verdict) -> bool:
    return verdict.turn_page and verdict.vs_previous != "worse"


def _previous_tail(project: Path, chapter: int) -> str:
    if chapter <= 1:
        return ""
    previous = project / "manuscript" / "chapters" / f"chapter-{chapter - 1:02d}.md"
    if not previous.exists():
        return ""
    return tail_words(previous.read_text(encoding="utf-8"), TAIL_WORDS)


def _template(name: str) -> str:
    path = AGENTS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"agent template missing: {path}")
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :]
    return text.strip()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
