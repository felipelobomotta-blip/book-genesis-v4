"""How the guided session looks (ADR 0009).

``RichView`` draws with rich: a header, a stage track with the active stage spinning and the
time each one took, the last few pipeline events, full-width panels at the points of
agreement, and the score card at the end. ``PlainView`` prints the same content as lines
for pipes, CI and machines without rich. Both implement ``runner.session.View``.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import os
import sys
import time
from typing import Deque, Dict, List, Optional

from runner.score import ScoreCard
from runner.session import STAGES, strip_leading_heading

RECORD_ENV = "BOOK_GENESIS_RECORD_SVG"
# A Windows console on cp1252 (the default one, still) cannot encode box-drawing characters:
# rich crashed with UnicodeEncodeError on the very first panel border when this was measured
# on 2026-09-04. Unicode boxes only when the stream proves it can carry them.
_BOX_PROBE = "─╭║"


def unicode_safe(stream=None) -> bool:
    """A stream with no encoding (an in-memory capture) can carry anything; one that declares
    an encoding is only trusted when that encoding really carries box drawing."""
    encoding = getattr(stream or sys.stdout, "encoding", "") or ""
    if not encoding:
        return True
    try:
        _BOX_PROBE.encode(encoding)
    except (LookupError, UnicodeEncodeError, TypeError):
        return False
    return True


def force_utf8(stream=None) -> None:
    """Ask the stream for UTF-8 before deciding anything: on Windows this turns a cp1252
    console into one that can carry the book's own accents."""
    reconfigure = getattr(stream or sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass


@dataclass
class StageState:
    name: str
    status: str = "pending"  # pending | running | done | failed | stopped
    detail: str = ""
    started: Optional[float] = None
    ended: Optional[float] = None

    def elapsed(self) -> str:
        if self.started is None:
            return ""
        end = self.ended if self.ended is not None else time.monotonic()
        seconds = int(end - self.started)
        return f"{seconds // 60}:{seconds % 60:02d}"


def interactive_terminal() -> bool:
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


def make_view(*, plain: bool = False, interactive: Optional[bool] = None):
    """The rich view on a terminal; the plain one for pipes, ``--plain`` and machines without rich."""
    force_utf8()
    is_tty = interactive_terminal() if interactive is None else interactive
    record_path = os.environ.get(RECORD_ENV, "")
    if not plain:
        try:
            import rich  # noqa: F401
        except ImportError:
            plain = True
    if plain:
        return PlainView(interactive=is_tty)
    return RichView(interactive=is_tty, live=is_tty and not record_path, record_path=record_path or None)


class PlainView:
    """Lines only. What a log file, a CI job or a pipe sees."""

    def __init__(self, *, interactive: bool = False, out=None) -> None:
        self.interactive = interactive
        self.out = out or sys.stdout
        self.stages: Dict[str, StageState] = {name: StageState(name) for name in STAGES}

    def _say(self, text: str = "") -> None:
        print(text, file=self.out, flush=True)

    def ask(self, prompt: str, default: str = "") -> str:
        shown = f"{prompt} [{default}]: " if default else f"{prompt}: "
        try:
            answer = input(shown).strip()
        except EOFError:
            answer = ""
        return answer or default

    def header(self, *, title: str, idea: str, language: str, roles: Dict[str, str], warnings: List[str]) -> None:
        self._say("BOOK GENESIS")
        if title:
            self._say(f"title: {title}")
        self._say(f"idea: {idea}")
        for role, who in roles.items():
            self._say(f"{role}: {who}")
        for warning in warnings:
            self._say(f"warning: {warning}")

    def stage_start(self, name: str, detail: str = "") -> None:
        stage = self.stages.setdefault(name, StageState(name))
        stage.status, stage.detail, stage.started, stage.ended = "running", detail, time.monotonic(), None
        self._say(f"{name}: running...{' ' + detail if detail else ''}")

    def stage_update(self, name: str, detail: str) -> None:
        self.stages.setdefault(name, StageState(name)).detail = detail

    def stage_done(self, name: str, summary: str = "") -> None:
        stage = self.stages.setdefault(name, StageState(name))
        stage.status, stage.detail, stage.ended = "done", summary, time.monotonic()
        self._say(f"{name}: done ({stage.elapsed()}){' ' + summary if summary else ''}")

    def stage_fail(self, name: str, message: str) -> None:
        stage = self.stages.setdefault(name, StageState(name))
        stage.status, stage.detail, stage.ended = "failed", message, time.monotonic()
        self._say(f"{name}: failed: {message}")

    def stage_stop(self, name: str, message: str) -> None:
        stage = self.stages.setdefault(name, StageState(name))
        stage.status, stage.detail, stage.ended = "stopped", message, time.monotonic()
        self._say(f"{name}: {message}")

    def event(self, line: str) -> None:
        self._say(f"  {line}")

    def checkpoint(self, title: str, body: str, hint: str) -> str:
        self._say("")
        self._say(f"== {title} ==")
        self._say(body)
        self._say("")
        if not self.interactive:
            return ""
        return self.ask(hint, "")

    def score(self, card: ScoreCard) -> None:
        self._say("")
        self._say(card.markdown().rstrip())
        self._say("Reader-model signals are simulated internal evidence; they are not human reading, later memory, literary quality, or publication readiness.")

    def finish(self, paths: Dict[str, "os.PathLike[str]"]) -> None:
        self._say("")
        self._say("done")
        for label, path in paths.items():
            self._say(f"{label}: {path}")

    def fail(self, message: str) -> None:
        self._say(message)


class RichView:
    """The terminal experience. Live stage track while stages run; static prints between."""

    def __init__(self, *, interactive: bool = True, live: bool = True, record_path: Optional[str] = None, console=None, width: Optional[int] = None) -> None:
        from rich.console import Console

        self.interactive = interactive
        self.record_path = record_path
        if console is None:
            force_utf8()
            console = Console(record=bool(record_path), width=width or (110 if record_path else None), force_terminal=bool(record_path))
        else:
            # A console handed in from outside still writes somewhere; ask that stream for
            # UTF-8 too. Measured 2026-09-04: without this the first checkmark crashed the run.
            force_utf8(getattr(console, "file", None))
        self.console = console
        self.live_enabled = live
        self.unicode = bool(record_path) or unicode_safe(getattr(self.console, "file", None))
        self.stages: Dict[str, StageState] = {name: StageState(name) for name in STAGES}
        self.events: Deque[str] = deque(maxlen=6)
        self._live = None
        self._track_printed = False

    # -- what this terminal can draw ---------------------------------------------------
    def _box(self, unicode_style: str):
        """Unicode boxes where the stream can carry them, ASCII everywhere else. Same
        decision as the ASCII banner of ADR 0005, for the same console."""
        from rich import box

        if not self.unicode:
            return box.ASCII
        return getattr(box, unicode_style)

    def _glyph(self, unicode_char: str, ascii_char: str) -> str:
        return unicode_char if self.unicode else ascii_char

    # -- input -------------------------------------------------------------------------
    def ask(self, prompt: str, default: str = "") -> str:
        shown = f"[bold]{prompt}[/]" + (f" [dim][{default}][/]" if default else "") + ": "
        try:
            answer = self.console.input(shown).strip()
        except EOFError:
            answer = ""
        return answer or default

    # -- header ------------------------------------------------------------------------
    def header(self, *, title: str, idea: str, language: str, roles: Dict[str, str], warnings: List[str]) -> None:
        from rich.panel import Panel
        from rich.text import Text

        body = Text()
        body.append("B O O K   G E N E S I S\n", style="bold cyan")
        body.append("one idea -> a chapter read blind -> a book\n\n", style="dim")
        fields = [("Title", title), ("Idea", idea), ("Language", language)]
        fields += [(role.capitalize(), who) for role, who in roles.items()]
        for label, value in fields:
            if not value:
                continue
            body.append(f"{label:<10}", style="bold")
            body.append(f"{value}\n")
        for warning in warnings:
            body.append(f"! {warning}\n", style="yellow")
        self.console.print(Panel(body, box=self._box("ROUNDED"), border_style="cyan", padding=(0, 2)))
        self._start_live()

    # -- stages ------------------------------------------------------------------------
    def stage_start(self, name: str, detail: str = "") -> None:
        stage = self.stages.setdefault(name, StageState(name))
        stage.status, stage.detail, stage.started, stage.ended = "running", detail, time.monotonic(), None
        self._refresh()

    def stage_update(self, name: str, detail: str) -> None:
        self.stages.setdefault(name, StageState(name)).detail = detail
        self._refresh()

    def stage_done(self, name: str, summary: str = "") -> None:
        stage = self.stages.setdefault(name, StageState(name))
        stage.status, stage.detail, stage.ended = "done", summary, time.monotonic()
        self._track_printed = False
        if self._live is not None:
            self._live.refresh()
        else:
            # No live widget (a pipe, a log, CI): one line per finished stage. Reprinting the
            # whole seven-stage track each time stacked seven copies down the log.
            self._print_stage_line(stage)

    def stage_fail(self, name: str, message: str) -> None:
        stage = self.stages.setdefault(name, StageState(name))
        stage.status, stage.detail, stage.ended = "failed", message, time.monotonic()
        self._stop_live()
        self._print_track()
        self._plain_print(message, "red")

    def stage_stop(self, name: str, message: str) -> None:
        stage = self.stages.setdefault(name, StageState(name))
        stage.status, stage.detail, stage.ended = "stopped", message, time.monotonic()
        self._stop_live()
        self._print_track()
        self._plain_print(message, "yellow")

    def event(self, line: str) -> None:
        self.events.append(line)
        self._refresh()

    # -- agreement ---------------------------------------------------------------------
    def checkpoint(self, title: str, body: str, hint: str) -> str:
        from rich.markdown import Markdown
        from rich.panel import Panel

        self._stop_live()
        self._print_track()
        # The three choices live in the frame, not only in the input prompt: they stay on
        # screen while the person reads a long outline.
        self.console.print(
            Panel(
                Markdown(strip_leading_heading(body)),
                title=f"[bold]{title}[/]",
                subtitle=f"[dim]{hint}[/]",
                box=self._box("ROUNDED"),
                border_style="magenta",
                padding=(1, 2),
            )
        )
        if not self.interactive:
            return ""
        answer = self.ask(hint, "")
        self._start_live()
        return answer

    # -- ending ------------------------------------------------------------------------
    def score(self, card: ScoreCard) -> None:
        from rich.console import Group
        from rich.panel import Panel
        from rich.table import Table
        from rich.text import Text

        self._stop_live()
        self._print_track()
        style = "bold green" if card.score >= 7.5 else ("bold yellow" if card.score >= 6.0 else "bold red")
        headline = Text()
        headline.append(f"{card.score:.1f}", style=style)
        headline.append(" / 10   ", style="bold")
        headline.append(card.band(), style="italic")
        table = Table(box=None, show_header=False, padding=(0, 1))
        table.add_column(style="bold")
        table.add_column()
        table.add_column(style="dim", justify="right")
        for component in card.components:
            table.add_row(component.label, component.detail, f"{int(component.weight * 100)}%")
        if card.blocked:
            table.add_row("Blocked", ", ".join(f"chapter {n}" for n in card.blocked), "")
        note = Text("Judges receive prose without the outline. Model independence depends on the configured roles. These are internal model-reader and revision signals, not human reading, later memory, literary quality, or publication readiness.", style="dim")
        self.console.print(
            Panel(
                Group(headline, Text(""), table, Text(""), note),
                title="[bold]Genesis Score[/]",
                box=self._box("DOUBLE"),
                border_style=style.split()[-1],
                padding=(1, 2),
            )
        )

    def finish(self, paths: Dict[str, "os.PathLike[str]"]) -> None:
        from rich.table import Table

        self._stop_live()
        table = Table(box=None, show_header=False, padding=(0, 1))
        table.add_column(style="bold")
        table.add_column(style="cyan")
        for label, path in paths.items():
            table.add_row(label, str(path))
        self.console.print(table)
        self._save_record()

    def fail(self, message: str) -> None:
        self._stop_live()
        self._plain_print(message, "red")
        self._save_record()

    def _plain_print(self, message: str, style: str) -> None:
        """A message from anywhere else (a provider error, a path holding `[draft]`) is text,
        never rich markup: printing it as markup swallowed the brackets and whatever followed."""
        from rich.text import Text

        self.console.print(Text(message, style=style))

    # -- drawing -----------------------------------------------------------------------
    def _track(self):
        from rich.console import Group
        from rich.rule import Rule
        from rich.spinner import Spinner
        from rich.table import Table
        from rich.text import Text

        table = Table.grid(padding=(0, 2))
        table.add_column(width=2)
        table.add_column(min_width=13)
        table.add_column(min_width=5, justify="right")
        table.add_column(ratio=1, overflow="fold")
        glyphs = {
            "pending": Text(self._glyph("○", "o"), style="dim"),
            "done": Text(self._glyph("✔", "+"), style="bold green"),
            "failed": Text(self._glyph("✘", "x"), style="bold red"),
            "stopped": Text(self._glyph("■", "="), style="bold yellow"),
        }
        for stage in self.stages.values():
            if stage.status == "running":
                glyph = Spinner("dots", style="cyan") if (self.live_enabled and self.unicode) else Text(">", style="cyan")
                name_style = "bold cyan"
            else:
                glyph = glyphs[stage.status]
                name_style = {"pending": "dim", "done": "bold", "failed": "bold red", "stopped": "bold yellow"}[stage.status]
            table.add_row(glyph, Text(stage.name, style=name_style), Text(stage.elapsed(), style="dim"), Text(stage.detail, style="dim" if stage.status != "running" else ""))
        parts = [table]
        if self.events and any(stage.status == "running" for stage in self.stages.values()):
            parts.append(Rule(style="dim"))
            parts.append(Text("\n".join(f"  {line}" for line in self.events), style="dim"))
        return Group(*parts)

    def _start_live(self) -> None:
        if not self.live_enabled or self._live is not None:
            return
        from rich.live import Live

        self._live = Live(get_renderable=self._track, console=self.console, refresh_per_second=8, transient=True)
        self._live.start()
        self._track_printed = False

    def _stop_live(self) -> None:
        if self._live is not None:
            self._live.stop()
            self._live = None

    def _print_stage_line(self, stage: StageState) -> None:
        from rich.text import Text

        line = Text()
        line.append(f"{self._glyph('✔', '+')}  ", style="bold green")
        line.append(f"{stage.name:<13}", style="bold")
        line.append(f"{stage.elapsed():>5}  ", style="dim")
        line.append(stage.detail, style="dim")
        self.console.print(line)

    def _print_track(self) -> None:
        """The live widget is transient, so the track has to be printed once when it stops.
        Without live (a pipe, a recording) stage_done already printed it: printing again here
        is the duplicate track seen on 2026-09-04."""
        if self._track_printed:
            return
        self.console.print(self._track())
        self._track_printed = True

    def _refresh(self, *, snapshot: bool = False) -> None:
        self._track_printed = False
        if self._live is not None:
            self._live.refresh()
        elif snapshot:
            self._print_track()

    def _save_record(self) -> None:
        if self.record_path:
            self.console.save_svg(self.record_path, title="book-genesis")


__all__ = [
    "RichView",
    "PlainView",
    "make_view",
    "interactive_terminal",
    "unicode_safe",
    "force_utf8",
    "StageState",
    "RECORD_ENV",
]
