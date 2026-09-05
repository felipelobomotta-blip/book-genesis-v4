"""The guided session: one idea in, a judged manuscript out, with the person watching and
agreeing along the way (ADR 0009).

UI-agnostic: everything visible goes through a ``View``. The real one draws with rich
(``runner.ui``); tests record calls. Three points of agreement: the brief, the outline and
chapter 1 read blind. Enter agrees; text becomes author notes and the stage runs again with
them; ``q`` stops (``book-genesis resume`` picks it up). Without a terminal, or with
``--yes``, nothing is asked and the run is the autonomous one of ADR 0002.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Dict, List, Optional, Protocol, Tuple

from runner.adapters import AdapterError, AwaitingManual
from runner.book import count_chapters, run_book
from runner.chapter import AwaitingHuman, resolve_human_checkpoint
from runner.filesystem import advance_phase, current_phase, load_state_summary, update_state_value
from runner.judge import parse_verdict
from runner.phases import DRAFTING_LABEL, recover_pending_publication, run_phase
from runner.score import ScoreCard, genesis_score
from runner.history import sha256

AUTHOR_NOTES = Path("work") / "author-notes.md"
STAGES: Tuple[str, ...] = ("Intake", "Foundation", "Architecture", "Drafting", "Audit", "Score", "Package")
PHASE_STAGE = {
    "Phase 0: Intake": "Intake",
    "Phase 1: Foundation": "Foundation",
    "Phase 2: Architecture": "Architecture",
    "Phase 3: Drafting": "Drafting",
    "Phase 4: Adversarial Audit": "Audit",
    "Phase 5: Final Score": "Score",
    "Phase 6: Editorial Package": "Package",
}
CHECKPOINT_AFTER = {
    "Phase 0: Intake": ("artifacts/00-brief.md", "The brief", "This is what the book is going to be."),
    "Phase 2: Architecture": ("artifacts/05-outline.md", "The outline", "Every chapter, in order, before a word of prose."),
}
CHECKPOINT_HINT = "Enter = go on  |  type what to change  |  q = stop here (resume later)"
CHAPTER_HINT = "Enter = write the rest  |  type notes to rewrite chapter 1 with them  |  q = stop here"
CONTINUE_WORDS = {"", "y", "yes", "ok", "go", "s", "sim", "continue"}
STOP_WORDS = {"q", "quit", "stop", "exit", "n", "no", "nao", "não"}
MAX_RERUNS = 2
EXCERPT_CHARS = 1200

_STARTING = re.compile(r"^chapter (?P<number>\d+) of (?P<total>\d+): starting")
_STEP = re.compile(r"^chapter (?P<number>\d+): (?P<rest>.+)$")
_PANEL_LINE = re.compile(r"^## Aggregate \((?P<yes>\d+) of (?P<seats>\d+) would turn the page\)", re.MULTILINE)


class View(Protocol):
    interactive: bool

    def header(self, *, title: str, idea: str, language: str, roles: Dict[str, str], warnings: List[str]) -> None: ...
    def stage_start(self, name: str, detail: str = "") -> None: ...
    def stage_update(self, name: str, detail: str) -> None: ...
    def stage_done(self, name: str, summary: str = "") -> None: ...
    def stage_fail(self, name: str, message: str) -> None: ...
    def stage_stop(self, name: str, message: str) -> None: ...
    def event(self, line: str) -> None: ...
    def checkpoint(self, title: str, body: str, hint: str) -> str: ...
    def score(self, card: ScoreCard) -> None: ...
    def finish(self, paths: Dict[str, Path]) -> None: ...
    def fail(self, message: str) -> None: ...


@dataclass
class SessionResult:
    status: str  # completed | stopped | awaiting_human | awaiting_manual | blocked | failed
    message: str = ""
    score: Optional[ScoreCard] = None


def run_session(project: Path, setup, view: View, *, yes: bool = False, human: bool = False, chapters: Optional[int] = None) -> SessionResult:
    recover_pending_publication(project)
    human = resolve_human_checkpoint(project, requested=human)
    summary = load_state_summary(project)
    view.header(
        title=summary.get("title", ""),
        idea=summary.get("idea", ""),
        language=summary.get("language", ""),
        roles=roles_of(setup),
        warnings=list(getattr(setup, "warnings", [])),
    )
    try:
        if not yes:
            outcome = _resume_pending_checkpoint(project, setup, view)
            if outcome is not None:
                return outcome
        outcome = _phases(project, setup, view, ask=not yes, stop_at=DRAFTING_LABEL)
        if outcome is not None:
            return outcome
        if load_state_summary(project)["status"] != "completed" and current_phase(project).label == DRAFTING_LABEL:
            outcome = _drafting(project, setup, view, ask=not yes, human=human, cap=chapters)
            if outcome is not None:
                return outcome
        outcome = _phases(project, setup, view, ask=False, stop_at=None)
        if outcome is not None:
            return outcome
    except AwaitingHuman as exc:
        view.fail(str(exc))
        return SessionResult("awaiting_human", str(exc))
    except AwaitingManual as exc:
        view.fail(str(exc))
        return SessionResult("awaiting_manual", str(exc))
    except (AdapterError, ValueError, FileNotFoundError, KeyError) as exc:
        view.fail(f"stopped: {exc}")
        return SessionResult("failed", str(exc))

    card = genesis_score(project)
    _append_score(project, card)
    view.score(card)
    view.finish(
        {
            "manuscript": project / "manuscript" / "chapters",
            "editorial package": project / "artifacts" / "10-editorial-package.md",
            "report": project / "RUN_REPORT.md",
        }
    )
    return SessionResult("completed", f"{card.score:.1f} / 10", card)


def roles_of(setup) -> Dict[str, str]:
    adapters = getattr(setup, "adapters", {})
    models = getattr(setup, "models", {})
    roles: Dict[str, str] = {}
    for role in ("writer", "judge"):
        adapter = adapters.get(role)
        if adapter is not None:
            roles[role] = f"{getattr(adapter, 'name', 'adapter')} {models.get(role, '')}".strip()
    panel = getattr(setup, "panel", None)
    members = getattr(panel, "members", None)
    if members:
        roles["panel"] = f"{len(members)} blind readers: " + ", ".join(dict.fromkeys(member.label for member in members))
    return roles


def interpret(answer: str) -> Tuple[str, str]:
    """'' / yes -> continue; q / no -> stop; anything else is a note for the author."""
    text = answer.strip()
    if text.lower() in CONTINUE_WORDS:
        return "continue", ""
    if text.lower() in STOP_WORDS:
        return "stop", ""
    return "notes", text


def strip_leading_heading(text: str) -> str:
    """Drop an artifact's own `# Title` line. The checkpoint panel already carries the title,
    and a Markdown H1 is drawn as a heavy box: without this it was a box inside a box."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            return "\n".join(lines[:index] + lines[index + 1 :]).strip("\n")
        break
    return text


def save_notes(project: Path, notes: str) -> Path:
    path = project / AUTHOR_NOTES
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"- {notes.strip()}\n")
    return path


def _phases(project: Path, setup, view: View, *, ask: bool, stop_at: Optional[str]) -> Optional[SessionResult]:
    for _ in range(8):
        if load_state_summary(project)["status"] == "completed":
            return None
        phase = current_phase(project)
        if stop_at is not None and phase.label == stop_at:
            return None
        stage = PHASE_STAGE.get(phase.label, phase.label)
        view.stage_start(stage)
        result = run_phase(project, setup.adapters, setup.models)
        if not result.ok:
            if phase.label == "Phase 4: Adversarial Audit" and any(item.startswith("audit_status:") for item in result.pending):
                report = project / "artifacts" / "08-adversarial-audit.md"
                message = f"Editorial revision required ({', '.join(result.pending)}). Read {report}; revise the manuscript before resuming."
                view.stage_stop(stage, message)
                return SessionResult("blocked", message)
            message = "not advanced; still missing: " + ", ".join(result.pending)
            view.stage_fail(stage, message)
            return SessionResult("failed", message)
        view.stage_done(stage, _phase_summary(project, phase.label, result.written))

        if ask and phase.label in CHECKPOINT_AFTER:
            outcome = _agree_on_phase(project, setup, view, phase, stage)
            if outcome is not None:
                return outcome
    return None


def _agree_on_phase(project: Path, setup, view: View, phase, stage: str) -> Optional[SessionResult]:
    relative, title, lead = CHECKPOINT_AFTER[phase.label]
    reruns = 0
    while True:
        body = f"{lead}\n\n---\n\n" + strip_leading_heading(_read(project / relative))
        kind, notes = interpret(view.checkpoint(title, body, CHECKPOINT_HINT))
        if kind == "stop":
            _save_checkpoint(project, {"kind": "phase", "phase": phase.label, "stage": stage, "relative": relative, "title": title, "lead": lead})
            return _stopped(project, view, stage)
        if kind == "continue":
            return None
        save_notes(project, notes)
        if reruns >= MAX_RERUNS:
            view.event("notes saved; they reach every later stage, this one is not rerun again")
            return None
        reruns += 1
        _rewind(project, phase.label)
        view.stage_start(stage, "again, with your notes")
        result = run_phase(project, setup.adapters, setup.models)
        if not result.ok:
            message = "not advanced; still missing: " + ", ".join(result.pending)
            view.stage_fail(stage, message)
            return SessionResult("failed", message)
        view.stage_done(stage, _phase_summary(project, phase.label, result.written) + " (rewritten with your notes)")


def _drafting(project: Path, setup, view: View, *, ask: bool, human: bool, cap: Optional[int]) -> Optional[SessionResult]:
    outline = _read(project / "artifacts" / "05-outline.md")
    total = count_chapters(outline)
    last = min(cap, total) if cap else total
    view.stage_start("Drafting", f"0 of {total} chapters")
    progress = _progress_handler(view, total)

    def write_up_to(end: int):
        return run_book(
            project,
            setup.adapters,
            setup.models,
            end=end,
            human_checkpoint=human,
            panel=getattr(setup, "panel", None),
            progress=progress,
        )

    if ask:
        book = write_up_to(1)
        outcome = _book_outcome(book, view)
        if outcome is not None:
            return outcome
        approval = project / "work" / "chapter-01.checkpoint-approved.json"
        current = project / "manuscript" / "chapters" / "chapter-01.md"
        already_approved = approval.exists() and current.exists() and _approved_hash(approval) == sha256(current)
        reruns = 0
        if already_approved:
            approval.unlink()
        while not already_approved:
            kind, notes = interpret(view.checkpoint("Chapter 1, read blind", chapter_report(project, 1), CHAPTER_HINT))
            if kind == "stop":
                _save_checkpoint(project, {"kind": "chapter", "chapter": 1, "stage": "Drafting"})
                return _stopped(project, view, "Drafting")
            if kind == "continue":
                _save_chapter_approval(project, 1)
                break
            save_notes(project, notes)
            if reruns >= MAX_RERUNS:
                view.event("notes saved; they reach every later chapter, chapter 1 is not rewritten again")
                break
            reruns += 1
            _forget_chapter(project, 1)
            view.stage_update("Drafting", "chapter 1 again, with your notes")
            book = write_up_to(1)
            outcome = _book_outcome(book, view)
            if outcome is not None:
                return outcome

    if last > 1 or not ask:
        book = write_up_to(last)
        outcome = _book_outcome(book, view)
        if outcome is not None:
            return outcome

    if cap is not None and last < total:
        message = f"stopped after {last} of {total} chapters by request; resume the rest with: book-genesis resume {project}"
        view.stage_stop("Drafting", message)
        return SessionResult("stopped", message)

    advanced = advance_phase(project)
    if not advanced["ok"]:
        message = "drafting done but the phase could not advance: " + ", ".join(advanced["pending"])
        view.stage_fail("Drafting", message)
        return SessionResult("failed", message)
    view.stage_done("Drafting", f"{total} chapters accepted by a blind reader")
    return None


def chapter_report(project: Path, number: int) -> str:
    """What the checkpoint shows for a chapter: how the blind readers took it, what they
    remembered, and the opening of the prose itself."""
    verdict_text = _latest_verdict_text(project, number)
    lines: List[str] = []
    if verdict_text:
        match = _PANEL_LINE.search(verdict_text)
        aggregate = verdict_text[match.start():] if match else verdict_text
        verdict = parse_verdict(aggregate)
        if match:
            lines.append(f"**{match.group('yes')} of {match.group('seats')} model readers would turn the page.**")
        else:
            lines.append("**The model reader would turn the page.**" if verdict.turn_page else "**The model reader stopped.**")
        if verdict.stopped_at and verdict.stopped_at != "none":
            lines.append(f"Stopped at: {verdict.stopped_at}")
        lines.append(f"Flags: {', '.join(verdict.flags)}" if verdict.flags else "No flags.")
        if verdict.remember:
            lines.append("")
            lines.append("Reported immediately by the model reader:")
            lines += [f"- {item}" for item in verdict.remember]
    chapter = project / "manuscript" / "chapters" / f"chapter-{number:02d}.md"
    if chapter.exists():
        text = strip_leading_heading(chapter.read_text(encoding="utf-8").strip())
        lines += ["", "---", "", text]
    return "\n".join(lines)


def _latest_verdict_text(project: Path, number: int) -> str:
    manifest = project / "manuscript" / "chapters" / "history" / f"chapter-{number:02d}" / "manifest.json"
    canonical = project / "manuscript" / "chapters" / f"chapter-{number:02d}.md"
    if manifest.exists() and canonical.exists():
        try:
            accepted = json.loads(manifest.read_text(encoding="utf-8")).get("accepted")
            if isinstance(accepted, dict) and accepted.get("status") == "accepted":
                relative = accepted.get("verdict_path")
                candidate = (project / relative).resolve() if isinstance(relative, str) else None
                if candidate and project.resolve() in candidate.parents and candidate.is_file():
                    return candidate.read_text(encoding="utf-8")
        except (OSError, ValueError, json.JSONDecodeError):
            return ""
    evaluations = project / "evaluations"
    if not evaluations.exists():
        return ""
    candidates = sorted(evaluations.glob(f"chapter-{number:02d}-judge-*.md"), key=lambda path: int(path.stem.rsplit("-", 1)[1]))
    return candidates[-1].read_text(encoding="utf-8") if candidates else ""


EVENT_CHARS = 96


def _progress_handler(view: View, total: int):
    state = {"number": 0}

    def handler(line: str) -> None:
        # The panel's own label names all three personas and runs to four wrapped lines; the
        # event strip is a glance, not a transcript. The full label stays in RUN_REPORT.md.
        view.event(line if len(line) <= EVENT_CHARS else line[: EVENT_CHARS - 3].rstrip() + "...")
        starting = _STARTING.match(line)
        if starting:
            state["number"] = int(starting.group("number"))
            view.stage_update("Drafting", f"chapter {starting.group('number')} of {total}: starting")
            return
        step = _STEP.match(line)
        if step:
            view.stage_update("Drafting", f"chapter {step.group('number')} of {total}: {step.group('rest')[:70]}")

    return handler


def _book_outcome(book, view: View) -> Optional[SessionResult]:
    if book.status == "awaiting_human":
        view.stage_stop("Drafting", book.message)
        return SessionResult("awaiting_human", book.message)
    if book.status == "blocked":
        view.stage_fail("Drafting", book.message)
        return SessionResult("blocked", book.message)
    return None


def _stopped(project: Path, view: View, stage: str) -> SessionResult:
    message = f"stopped here; continue any time with: book-genesis resume {project}"
    view.stage_stop(stage, message)
    return SessionResult("stopped", message)


def _checkpoint_path(project: Path) -> Path:
    return project / "work" / "pending-checkpoint.json"


def _save_checkpoint(project: Path, data: Dict[str, object]) -> None:
    path = _checkpoint_path(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")


def _resume_pending_checkpoint(project: Path, setup, view: View) -> Optional[SessionResult]:
    path = _checkpoint_path(project)
    if not path.exists():
        return None
    try:
        pending = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise ValueError(f"invalid pending checkpoint: {path}")
    if pending.get("kind") == "phase":
        relative, title, lead = pending["relative"], pending["title"], pending["lead"]
        kind, notes = interpret(view.checkpoint(title, f"{lead}\n\n---\n\n" + strip_leading_heading(_read(project / relative)), CHECKPOINT_HINT))
        if kind == "stop":
            return _stopped(project, view, str(pending["stage"]))
        path.unlink()
        if kind == "notes":
            save_notes(project, notes)
            _rewind(project, str(pending["phase"]))
        return None
    if pending.get("kind") == "chapter":
        number = int(pending["chapter"])
        kind, notes = interpret(view.checkpoint(f"Chapter {number}, read blind", chapter_report(project, number), CHAPTER_HINT))
        if kind == "stop":
            return _stopped(project, view, "Drafting")
        path.unlink()
        if kind == "notes":
            save_notes(project, notes)
            _forget_chapter(project, number)
        else:
            _save_chapter_approval(project, number)
        return None
    raise ValueError(f"unknown pending checkpoint kind: {pending.get('kind')}")


def _rewind(project: Path, label: str) -> None:
    state = project / "PROJECT_STATE.yaml"
    update_state_value(state, "current_phase", label)
    update_state_value(state, "status", "in_progress")


def _forget_chapter(project: Path, number: int) -> None:
    """Request a replacement without deleting the accepted chapter first.

    The marker survives a stopped session, so resume performs the pending rewrite
    rather than silently treating the old canonical snapshot as complete.
    """
    marker = project / "work" / f"rewrite-chapter-{number:02d}.pending"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("rewrite requested by author notes\n", encoding="utf-8")
    approval = project / "work" / f"chapter-{number:02d}.checkpoint-approved.json"
    if approval.exists():
        approval.unlink()


def _approved_hash(path: Path) -> str:
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("sha256", ""))
    except json.JSONDecodeError:
        return ""


def _save_chapter_approval(project: Path, number: int) -> None:
    chapter = project / "manuscript" / "chapters" / f"chapter-{number:02d}.md"
    if chapter.exists():
        path = project / "work" / f"chapter-{number:02d}.checkpoint-approved.json"
        path.write_text(json.dumps({"sha256": sha256(chapter)}) + "\n", encoding="utf-8")


def _phase_summary(project: Path, label: str, written: List[str]) -> str:
    summary = load_state_summary(project)
    if label == "Phase 0: Intake":
        title = summary.get("title", "")
        genre = summary.get("genre", "")
        return ", ".join(part for part in (title, genre) if part) or f"wrote {len(written)} files"
    if label == "Phase 2: Architecture":
        outline = project / "artifacts" / "05-outline.md"
        if outline.exists():
            return f"{count_chapters(_read(outline))} chapters outlined"
    return f"wrote {len(written)} file{'s' if len(written) != 1 else ''}"


def _append_score(project: Path, card: ScoreCard) -> None:
    report = project / "RUN_REPORT.md"
    if not report.exists():
        report.write_text("# Run Report\n\n", encoding="utf-8")
    with report.open("a", encoding="utf-8") as handle:
        handle.write("\n" + card.markdown())


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


__all__ = [
    "run_session",
    "SessionResult",
    "View",
    "interpret",
    "save_notes",
    "strip_leading_heading",
    "chapter_report",
    "roles_of",
    "STAGES",
    "AUTHOR_NOTES",
]
