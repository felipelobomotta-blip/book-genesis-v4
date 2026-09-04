"""The Genesis Score: one number, computed only from what blind readers did (ADR 0009).

Nothing here is self-graded. The judge never saw the outline; the panel never saw the
writer's plan. The score says how the book behaved in front of readers, not how the writer
felt about it. Four components, fixed weights, every number shown next to the score.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Dict, List, Optional, Tuple

_CHAPTER_LINE = re.compile(
    r"^- chapter (?P<number>\d+): (?P<status>accepted|blocked) after (?P<cycles>\d+) revision cycle\(s\); "
    r"judge: (?P<judge>.*?); last verdict: turn_page=(?P<turn>yes|no), flags=\[(?P<flags>.*?)\], stopped_at=",
    re.MULTILINE,
)
_PANEL_LINE = re.compile(r"^## Aggregate \((?P<yes>\d+) of (?P<seats>\d+) would turn the page\)", re.MULTILINE)
_JUDGE_FILE = re.compile(r"^chapter-(?P<number>\d+)-judge-(?P<draft>\d+)\.md$")
_YAML_BLOCK = re.compile(r"```yaml\s*\n(.*?)\n```", re.DOTALL)
_REMEMBER_ITEM = re.compile(r"^\s+-\s+\S", re.MULTILINE)

WEIGHTS: Tuple[Tuple[str, float], ...] = (("panel", 0.4), ("first_pass", 0.3), ("accepted", 0.2), ("remembered", 0.1))


@dataclass(frozen=True)
class ChapterRow:
    number: int
    status: str
    cycles: int
    turn_page: bool
    flags: List[str]


@dataclass(frozen=True)
class Component:
    key: str
    label: str
    value: float  # 0..1
    detail: str
    weight: float


@dataclass
class ScoreCard:
    score: float
    chapters: int
    components: List[Component] = field(default_factory=list)
    blocked: List[int] = field(default_factory=list)

    def band(self) -> str:
        if self.chapters == 0:
            return "no chapters were judged"
        if self.blocked:
            return "a chapter never convinced the reader"
        if self.score >= 9.0:
            return "readers turned every page"
        if self.score >= 7.5:
            return "readers kept going; revisions did the rest"
        if self.score >= 6.0:
            return "it holds, with visible seams"
        return "not there yet"

    def markdown(self) -> str:
        lines = ["## Genesis Score", "", f"**{self.score:.1f} / 10**: {self.band()}.", ""]
        for component in self.components:
            lines.append(f"- {component.label}: {component.detail} ({int(component.weight * 100)}%)")
        if self.blocked:
            lines.append(f"- Blocked chapters: {', '.join(str(n) for n in self.blocked)}")
        lines += [
            "",
            "Computed only from blind readers who never saw the outline. Nothing was graded by the model that wrote it.",
        ]
        return "\n".join(lines) + "\n"


def genesis_score(project: Path) -> ScoreCard:
    rows = chapter_rows(project / "RUN_REPORT.md")
    if not rows:
        return ScoreCard(0.0, 0, [], [])
    numbers = sorted(rows)
    accepted = [n for n in numbers if rows[n].status == "accepted"]
    blocked = [n for n in numbers if rows[n].status == "blocked"]
    first_pass = [n for n in accepted if rows[n].cycles == 0]
    panel_yes, panel_seats, panel_detail = _panel_votes(project, rows)
    remembered = [n for n in numbers if _remembered(project, n)]

    total = len(numbers)
    values = {
        "panel": (panel_yes / panel_seats) if panel_seats else 0.0,
        "first_pass": len(first_pass) / total,
        "accepted": len(accepted) / total,
        "remembered": len(remembered) / total,
    }
    details = {
        "panel": panel_detail,
        "first_pass": f"{len(first_pass)} of {total} chapters accepted on the first draft",
        "accepted": f"{len(accepted)} of {total} chapters accepted in the end",
        "remembered": f"{len(remembered)} of {total} chapters left the reader with something specific",
    }
    labels = {
        "panel": "Reader panel",
        "first_pass": "First-draft acceptance",
        "accepted": "Chapters accepted",
        "remembered": "Memorable",
    }
    components = [Component(key, labels[key], values[key], details[key], weight) for key, weight in WEIGHTS]
    score = round(10 * sum(component.value * component.weight for component in components), 1)
    return ScoreCard(score, total, components, blocked)


def chapter_rows(report: Path) -> Dict[int, ChapterRow]:
    """The last line per chapter in RUN_REPORT.md wins: a chapter rewritten after the
    person's notes reports twice, and the second run is the one that counts."""
    if not report.exists():
        return {}
    rows: Dict[int, ChapterRow] = {}
    for match in _CHAPTER_LINE.finditer(report.read_text(encoding="utf-8")):
        number = int(match.group("number"))
        flags = [flag.strip() for flag in match.group("flags").split(",") if flag.strip()]
        rows[number] = ChapterRow(number, match.group("status"), int(match.group("cycles")), match.group("turn") == "yes", flags)
    return rows


def _panel_votes(project: Path, rows: Dict[int, ChapterRow]) -> Tuple[int, int, str]:
    yes = seats = 0
    for number in sorted(rows):
        first = project / "evaluations" / f"chapter-{number:02d}-judge-1.md"
        if not first.exists():
            continue
        match = _PANEL_LINE.search(first.read_text(encoding="utf-8"))
        if match:
            yes += int(match.group("yes"))
            seats += int(match.group("seats"))
    if seats:
        return yes, seats, f"{yes} of {seats} blind readers would turn the page"
    # No panel ran (single judge only): the judge's first read of each chapter stands in.
    first_reads = [n for n in rows if _first_read_turns_page(project, n)]
    return len(first_reads), len(rows), f"no panel; the judge turned the page on {len(first_reads)} of {len(rows)} first reads"


def _first_read_turns_page(project: Path, number: int) -> bool:
    first = project / "evaluations" / f"chapter-{number:02d}-judge-1.md"
    if not first.exists():
        return False
    block = _last_yaml_block(first.read_text(encoding="utf-8"))
    return bool(re.search(r"^turn_page:\s*(yes|true)\s*$", block, re.MULTILINE | re.IGNORECASE))


def _remembered(project: Path, number: int) -> bool:
    latest = _latest_judge_file(project, number)
    if latest is None:
        return False
    block = _last_yaml_block(latest.read_text(encoding="utf-8"))
    section = re.search(r"^remember:(?P<body>.*?)(?=^\S|\Z)", block, re.MULTILINE | re.DOTALL)
    if not section:
        return False
    body = section.group("body")
    if "[]" in body.strip()[:2]:
        return False
    return bool(_REMEMBER_ITEM.search(body))


def _latest_judge_file(project: Path, number: int) -> Optional[Path]:
    evaluations = project / "evaluations"
    if not evaluations.exists():
        return None
    best: Optional[Tuple[int, Path]] = None
    for path in evaluations.iterdir():
        match = _JUDGE_FILE.match(path.name)
        if match and int(match.group("number")) == number:
            draft = int(match.group("draft"))
            if best is None or draft > best[0]:
                best = (draft, path)
    return best[1] if best else None


def _last_yaml_block(text: str) -> str:
    blocks = _YAML_BLOCK.findall(text)
    return blocks[-1] if blocks else text


__all__ = ["ScoreCard", "Component", "ChapterRow", "genesis_score", "chapter_rows", "WEIGHTS"]
