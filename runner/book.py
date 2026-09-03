"""Write the manuscript chapter by chapter until it is done, blocked, or waiting for a human."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from runner.adapters import Adapter
from runner.brief import CHAPTER_MARK
from runner.chapter import AwaitingHuman, run_chapter


@dataclass
class BookResult:
    status: str
    chapters_done: List[int] = field(default_factory=list)
    last_chapter: int = 0
    message: str = ""


def count_chapters(outline: str) -> int:
    numbers = []
    for line in outline.splitlines():
        match = CHAPTER_MARK.match(line)
        if match:
            numbers.append(int(match.group("number")))
    return max(numbers) if numbers else 0


def run_book(
    project: Path,
    adapters: Dict[str, Adapter],
    models: Dict[str, str],
    *,
    start: Optional[int] = None,
    end: Optional[int] = None,
) -> BookResult:
    outline_path = project / "artifacts" / "05-outline.md"
    if not outline_path.exists():
        raise ValueError(f"no outline at {outline_path}; run the architecture phase first")
    total = count_chapters(outline_path.read_text(encoding="utf-8"))
    if total == 0:
        raise ValueError("the outline has no `## Chapter N` headings; nothing to write")

    first = start or 1
    last = end or total
    done: List[int] = []
    for number in range(first, last + 1):
        if (project / "manuscript" / "chapters" / f"chapter-{number:02d}.md").exists():
            continue
        try:
            result = run_chapter(project, number, adapters, models=models)
        except AwaitingHuman as exc:
            return BookResult("awaiting_human", done, number, str(exc))
        if not result.accepted:
            return BookResult(
                "blocked",
                done,
                number,
                f"chapter {number} blocked after {result.cycles} revision cycle(s); best draft: {result.draft_path}",
            )
        done.append(number)
    return BookResult("completed", done, last, f"{len(done)} chapter(s) written this run; {total} in the outline")
