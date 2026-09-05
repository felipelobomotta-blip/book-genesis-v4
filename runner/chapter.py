"""The per-chapter loop.

writer -> disruptor (when the genre wants it) -> blind judge -> [editor -> judge]*
until the reader would turn the page and the new draft is not worse than the one
before it, or the genre's revision budget is spent. The runner owns every file;
the models only ever see text and return text (ADR 0001). No human is required;
``human_checkpoint=True`` restores the pause after chapter 1 (ADR 0002).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Callable, Dict, List, Optional, Protocol

from runner.adapters import Adapter
from runner.brief import TAIL_WORDS, build_chapter_brief, tail_words
from runner.constants import GenreProfile, load_genre_profile
from runner.filesystem import load_state_summary
from runner.history import load_manifest, project_relative, record_draft, reserve_attempt, sha256, write_manifest
from runner.judge import SingleJudge, Verdict

from runner.resources import resource_root

REPO_ROOT = resource_root()
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


class Judge(Protocol):
    label: str

    def judge(
        self,
        prose: str,
        previous_tail: str,
        genre: str,
        *,
        previous_draft: Optional[str] = None,
        reader: str = "",
    ) -> Verdict: ...


class AwaitingHuman(RuntimeError):
    """Human mode only: chapter 1 has to be read by a person before chapter 2 is written."""

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
    judge: Optional[Judge] = None,
    human_checkpoint: bool = False,
    progress: Optional[Callable[[str], None]] = None,
    seed_draft: Optional[str] = None,
    revise_on_flags: bool = False,
) -> ChapterResult:
    """Run one chapter through the loop.

    With ``seed_draft`` (polish mode, ADR 0006) the loop starts from existing
    prose instead of calling the writer: the seed becomes draft 1 and the
    blind judge decides whether the editor gets a turn at all. With
    ``revise_on_flags`` the editor also takes a pass on chapters the judge
    would still turn the page on but flagged; the ``vs_previous`` guard keeps
    the original whenever a revision does not improve it.
    """
    models = models or {}
    say = progress or (lambda _message: None)
    if human_checkpoint and chapter > 1:
        marker = project / "approvals" / f"{FIRST_CHAPTER_SLUG}.approved"
        if not marker.exists():
            raise AwaitingHuman(project / "manuscript" / "chapters" / f"{FIRST_CHAPTER_SLUG}.md", marker)

    if judge is None:
        judge = SingleJudge(adapters["judge"], models.get("judge", ""))

    summary = load_state_summary(project)
    genre = summary.get("genre", "")
    reader = summary.get("audience", "")
    profile = load_genre_profile(genre)
    previous_tail = _previous_tail(project, chapter)

    drafts_dir = project / "manuscript" / "drafts" / f"chapter-{chapter:02d}"
    evaluations_dir = project / "evaluations"

    # Reserve before invoking writer/judge: a crashed/manual provider leaves a
    # durable pending attempt and the retry gets a new immutable filename.
    attempt_id, attempt_sequence = reserve_attempt(project, chapter)
    if seed_draft is not None:
        say(f"chapter {chapter}: polish: seeding from existing prose ({len(seed_draft.split())} words)")
        draft = clean_chapter(seed_draft)
    else:
        brief = build_chapter_brief(project, chapter)
        say(f"chapter {chapter}: writer ({adapters['writer'].name}{' ' + models['writer'] if models.get('writer') else ''})...")
        draft = clean_chapter(
            adapters["writer"].complete(writer_prompt(brief, chapter, genre, profile), model=models.get("writer", ""))
        )
        say(f"chapter {chapter}: writer done, {len(draft.split())} words")
        if profile.disruptor_default and "disruptor" in adapters:
            say(f"chapter {chapter}: disruptor...")
            draft = clean_chapter(
                adapters["disruptor"].complete(disruptor_prompt(draft, chapter, genre), model=models.get("disruptor", ""))
            )
            say(f"chapter {chapter}: disruptor done, {len(draft.split())} words")

    draft_number = 1
    draft_path = _attempt_draft_path(drafts_dir, attempt_id, attempt_sequence, draft_number)
    _write(draft_path, draft)
    record_draft(project, chapter, attempt_id, draft_path)
    say(f"chapter {chapter}: judge ({getattr(judge, 'label', 'judge')})...")
    verdict = judge.judge(draft, previous_tail, genre, reader=reader)
    verdict_path = _attempt_verdict_path(evaluations_dir, chapter, attempt_id, attempt_sequence, draft_number)
    _write(verdict_path, verdict.raw)
    say(f"chapter {chapter}: judge says {_verdict_line(verdict)}")
    verdicts = [verdict]

    best, best_verdict, best_draft_path, best_verdict_path = draft, verdict, draft_path, verdict_path
    accepted = _accepted(verdict)
    cycles = 0
    while cycles < profile.max_revision_cycles and (not accepted or (revise_on_flags and best_verdict.flags)):
        cycles += 1
        say(f"chapter {chapter}: editor, cycle {cycles} of {profile.max_revision_cycles} (modes: {', '.join(best_verdict.flags) or 'stopped_at only'})...")
        candidate = clean_chapter(
            adapters["editor"].complete(
                editor_prompt(best, best_verdict, chapter, genre, profile),
                model=models.get("editor", ""),
            )
        )
        draft_number += 1
        draft_path = _attempt_draft_path(drafts_dir, attempt_id, attempt_sequence, draft_number)
        _write(draft_path, candidate)
        record_draft(project, chapter, attempt_id, draft_path)
        say(f"chapter {chapter}: judge compares draft {draft_number} with the previous best...")
        verdict = judge.judge(candidate, previous_tail, genre, previous_draft=best, reader=reader)
        verdict_path = _attempt_verdict_path(evaluations_dir, chapter, attempt_id, attempt_sequence, draft_number)
        _write(verdict_path, verdict.raw)
        say(f"chapter {chapter}: judge says {_verdict_line(verdict)}")
        verdicts.append(verdict)
        if verdict.vs_previous != "worse":
            best, best_verdict, best_draft_path, best_verdict_path = candidate, verdict, draft_path, verdict_path
        elif _accepted(best_verdict):
            # Polish may seek to remove flags from an already accepted text. Once a
            # candidate is worse, retain the accepted best and stop spending calls.
            break
        accepted = _accepted(best_verdict)

    label = getattr(judge, "label", "judge")
    if accepted:
        final = project / "manuscript" / "chapters" / f"chapter-{chapter:02d}.md"
        _write(final, best)
        result = ChapterResult(chapter, True, "accepted", cycles, final, verdicts)
    else:
        result = ChapterResult(chapter, False, "blocked", cycles, best_draft_path, verdicts)
    _record_attempt(project, chapter, attempt_id, attempt_sequence, result, best_draft_path, best_verdict_path)
    _append_run_report(project, result, label)
    say(f"chapter {chapter}: {result.status} after {cycles} revision cycle(s)")
    return result


def _verdict_line(verdict: Verdict) -> str:
    return (
        f"turn_page={'yes' if verdict.turn_page else 'no'}, flags=[{', '.join(verdict.flags)}]"
        + (f", vs_previous={verdict.vs_previous}" if verdict.vs_previous != "none" else "")
        + (f", stopped_at={verdict.stopped_at[:60]}" if verdict.stopped_at != "none" else "")
    )


def writer_prompt(brief: str, chapter: int, genre: str, profile: GenreProfile) -> str:
    return (
        RUNNER_CONTRACT
        + _template("book-writer.md")
        + "\n\n# THE BRIEF\n\n"
        + brief.strip()
        + "\n\n# OUTPUT\n\n"
        + f"Return only Chapter {chapter}, as Markdown, starting with a level-1 heading of the form "
        + f"`# Chapter {chapter}: Title`, translated into the book's language (Portuguese: `# Capítulo {chapter}: Título`). Prose only: no craft notes, no self-report, no preamble, no "
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


def _attempt_draft_path(drafts_dir: Path, attempt_id: str, sequence: int, draft: int) -> Path:
    # Keep the original names for the first run so existing projects and scripts
    # retain their familiar layout. Subsequent runs cannot overwrite those files.
    return drafts_dir / (f"draft-{draft}.md" if sequence == 1 else f"{attempt_id}-draft-{draft}.md")


def _attempt_verdict_path(evaluations_dir: Path, chapter: int, attempt_id: str, sequence: int, draft: int) -> Path:
    stem = f"chapter-{chapter:02d}-judge-{draft}.md" if sequence == 1 else f"chapter-{chapter:02d}-judge-{attempt_id}-{draft}.md"
    return evaluations_dir / stem


def _record_attempt(
    project: Path, chapter: int, attempt_id: str, sequence: int, result: ChapterResult, draft_path: Path, verdict_path: Path
) -> None:
    manifest = load_manifest(project, chapter)
    record = {
        "attempt_id": attempt_id,
        "sequence": sequence,
        "status": result.status,
        "draft_path": project_relative(project, draft_path),
        "verdict_path": project_relative(project, verdict_path),
        "sha256": sha256(draft_path),
    }
    for index, existing in enumerate(manifest["attempts"]):
        if existing.get("attempt_id") == attempt_id:
            manifest["attempts"][index] = record
            break
    else:
        manifest["attempts"].append(record)
    if result.accepted:
        manifest["accepted"] = dict(record)
    write_manifest(project, chapter, manifest)


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


def _append_run_report(project: Path, result: ChapterResult, judge_label: str) -> None:
    """RUN_REPORT.md is where the human reads afterwards what used to be said at a checkpoint."""
    path = project / "RUN_REPORT.md"
    last = result.verdicts[-1] if result.verdicts else None
    verdict_text = "no verdict"
    if last is not None:
        verdict_text = (
            f"turn_page={'yes' if last.turn_page else 'no'}, flags=[{', '.join(last.flags)}], "
            f"stopped_at={last.stopped_at}"
        )
    line = (
        f"- chapter {result.chapter}: {result.status} after {result.cycles} revision cycle(s); "
        f"judge: {judge_label}; last verdict: {verdict_text}; file: {result.draft_path}"
    )
    if not path.exists():
        path.write_text("# Run Report\n\n## Chapter log\n\n", encoding="utf-8")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
