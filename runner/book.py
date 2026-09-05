"""Write the manuscript chapter by chapter until it is done, blocked, or (human mode) waiting."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Callable, Dict, List, Optional

from runner.adapters import Adapter
from runner.brief import CHAPTER_MARK
from runner.chapter import AwaitingHuman, FIRST_CHAPTER_SLUG, Judge, resolve_human_checkpoint, run_chapter


@dataclass
class BookResult:
    status: str
    chapters_done: List[int] = field(default_factory=list)
    last_chapter: int = 0
    message: str = ""


def count_chapters(outline: str) -> int:
    numbers = _chapter_numbers(outline)
    return max(numbers) if numbers else 0


def outline_chapters(outline: str) -> List[int]:
    numbers = _chapter_numbers(outline)
    if not numbers:
        return []
    expected = list(range(1, max(numbers) + 1))
    if sorted(numbers) != expected:
        raise ValueError(f"outline chapters must be exactly 1..N without duplicates or gaps; found {numbers}")
    return numbers


def _chapter_numbers(outline: str) -> List[int]:
    numbers: List[int] = []
    for line in outline.splitlines():
        match = CHAPTER_MARK.match(line)
        if match:
            numbers.append(int(match.group("number")))
    return numbers


def _validate_range(first: int, last: int, total: int) -> None:
    if first < 1 or last < first or last > total:
        raise ValueError(f"invalid chapter range {first}..{last}; expected 1 <= start <= end <= {total}")


def run_book(
    project: Path,
    adapters: Dict[str, Adapter],
    models: Dict[str, str],
    *,
    start: Optional[int] = None,
    end: Optional[int] = None,
    human_checkpoint: bool = False,
    panel: Optional[Judge] = None,
    panel_chapters: Optional[List[int]] = None,
    progress: Optional[Callable[[str], None]] = None,
) -> BookResult:
    """Chapter 1 (and any chapter in ``panel_chapters``) is judged by the panel when one is given.

    Every other chapter is judged by the single judge. With ``human_checkpoint`` the run stops
    after chapter 1 until ``approve`` is recorded, as in ADR 0001.
    """
    outline_path = project / "artifacts" / "05-outline.md"
    if not outline_path.exists():
        raise ValueError(f"no outline at {outline_path}; run the architecture phase first")
    total = len(outline_chapters(outline_path.read_text(encoding="utf-8")))
    if total == 0:
        raise ValueError("the outline has no `## Chapter N` headings; nothing to write")

    say = progress or (lambda _message: None)
    human_checkpoint = resolve_human_checkpoint(project, requested=human_checkpoint)
    gate_chapters = set(panel_chapters if panel_chapters is not None else [1])
    first = start or 1
    last = end or total
    _validate_range(first, last, total)
    done: List[int] = []
    for number in range(first, last + 1):
        if human_checkpoint and number > 1:
            marker = project / "approvals" / f"{FIRST_CHAPTER_SLUG}.approved"
            if not marker.exists():
                waiting = AwaitingHuman(project / "manuscript" / "chapters" / f"{FIRST_CHAPTER_SLUG}.md", marker)
                return BookResult("awaiting_human", done, number, str(waiting))
        pending_rewrite = project / "work" / f"rewrite-chapter-{number:02d}.pending"
        if (project / "manuscript" / "chapters" / f"chapter-{number:02d}.md").exists() and not pending_rewrite.exists():
            say(f"chapter {number}: already written, skipped")
            continue
        judge = panel if (panel is not None and number in gate_chapters) else None
        say(f"chapter {number} of {total}: starting" + (" (reader panel)" if judge is not None else ""))
        try:
            result = run_chapter(
                project,
                number,
                adapters,
                models=models,
                judge=judge,
                human_checkpoint=human_checkpoint,
                progress=progress,
            )
        except AwaitingHuman as exc:
            return BookResult("awaiting_human", done, number, str(exc))
        if not result.accepted:
            return BookResult(
                "blocked",
                done,
                number,
                f"chapter {number} blocked after {result.cycles} revision cycle(s); best draft: {result.draft_path}",
            )
        if pending_rewrite.exists():
            pending_rewrite.unlink()
        done.append(number)
    return BookResult("completed", done, last, f"{len(done)} chapter(s) written this run; {total} in the outline")


def discover_chapters(project: Path) -> List[int]:
    """Chapter numbers that already exist in ``manuscript/chapters`` (ADR 0006)."""
    chapters_dir = project / "manuscript" / "chapters"
    numbers: List[int] = []
    if not chapters_dir.exists():
        return numbers
    for path in chapters_dir.iterdir():
        match = re.fullmatch(r"chapter-(\d+)\.md", path.name)
        if match:
            numbers.append(int(match.group(1)))
    return sorted(numbers)


def run_polish(
    project: Path,
    adapters: Dict[str, Adapter],
    models: Dict[str, str],
    *,
    start: Optional[int] = None,
    end: Optional[int] = None,
    judge: Optional[Judge] = None,
    progress: Optional[Callable[[str], None]] = None,
) -> BookResult:
    """Polish chapters that already exist: seed each file into the loop (ADR 0006).

    The writer and the disruptor are never called. Flagged chapters get an
    editor pass even when the page-turn verdict is yes (``revise_on_flags``);
    the ``vs_previous`` guard keeps the original whenever a revision does not
    improve it. A chapter without a file is skipped with a warning; a chapter
    the judge never approves stops the run with the file untouched.
    """
    numbers = discover_chapters(project)
    if not numbers:
        raise ValueError(f"no chapter files under {project / 'manuscript' / 'chapters'}; nothing to polish")

    say = progress or (lambda _message: None)
    first = start or numbers[0]
    last = end or numbers[-1]
    if first < 1 or last < first:
        raise ValueError(f"invalid chapter range {first}..{last}; start must be positive and no later than end")
    done: List[int] = []
    skipped: List[int] = []
    for number in range(first, last + 1):
        path = project / "manuscript" / "chapters" / f"chapter-{number:02d}.md"
        if not path.exists():
            skipped.append(number)
            say(f"chapter {number}: no file in manuscript/chapters, skipped")
            continue
        say(f"chapter {number} of {last}: polishing")
        result = run_chapter(
            project,
            number,
            adapters,
            models=models,
            judge=judge,
            seed_draft=path.read_text(encoding="utf-8"),
            revise_on_flags=True,
            progress=progress,
        )
        if not result.accepted:
            return BookResult(
                "blocked",
                done,
                number,
                f"chapter {number} blocked after {result.cycles} revision cycle(s); file left untouched; best draft: {result.draft_path}",
            )
        done.append(number)
    skipped_note = f"; skipped (no file): {', '.join(str(n) for n in skipped)}" if skipped else ""
    return BookResult("polished", done, last, f"{len(done)} chapter(s) polished this run{skipped_note}")
