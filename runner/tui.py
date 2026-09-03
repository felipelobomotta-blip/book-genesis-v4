"""A tiny, dependency-free arrow-key menu and startup banner.

Windows reads raw keys through ``msvcrt``; everything else through ``termios``/``tty``. Both
are standard library, so this costs nothing extra to install (README promise: "Python 3.10 or
newer. No other packages.").

The picker only runs for real when stdin and stdout are both an actual terminal
(``supports_interactive``); ``runner/setup.py`` falls back to typing a number otherwise. That
fallback is also what every automated test uses, so the only things here that need a live
terminal to exercise (``read_key``, ``interactive_choose``) are verified by hand, in a real
terminal, not by ``pytest`` - ``apply_key`` carries the actual navigation logic and is what the
test suite checks.
"""

from __future__ import annotations

import sys
from typing import List, Optional, TextIO

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
CYAN = "\x1b[36m"
DIM = "\x1b[2m"

TITLE = "B O O K   G E N E S I S"
SUBTITLE = "one idea -> a chapter read blind -> a book"

_ansi_ready = False


def supports_interactive(stdin: Optional[object] = None, stdout: Optional[object] = None) -> bool:
    """True only when both streams are a real terminal - never true under a test runner,
    a pipe, or a redirect, which is exactly when the fallback in setup.py should be used."""
    stdin = stdin if stdin is not None else sys.stdin
    stdout = stdout if stdout is not None else sys.stdout
    try:
        return bool(stdin.isatty()) and bool(stdout.isatty())
    except (AttributeError, ValueError):
        return False


def banner(color: bool = True) -> str:
    # Plain ASCII on purpose, not box-drawing Unicode: this machine's console defaults to
    # cp1252, which cannot encode a single box-drawing character and crashes the whole
    # command on the spot. ANSI color codes are themselves plain ASCII bytes, so they carry
    # no such risk - that is where the "bonito" comes from instead.
    width = max(len(TITLE), len(SUBTITLE)) + 4
    border = "+" + "-" * width + "+"
    blank = "|" + " " * width + "|"
    title_line = "|" + TITLE.center(width) + "|"
    subtitle_line = "|" + SUBTITLE.center(width) + "|"
    lines = [border, blank, title_line, subtitle_line, blank, border]
    if not color:
        return "\n".join(lines)
    styled = []
    for line in lines:
        if line == border:
            styled.append(f"{CYAN}{BOLD}{line}{RESET}")
        elif line == blank:
            styled.append(f"{CYAN}{line}{RESET}")
        else:
            styled.append(f"{CYAN}|{RESET}{BOLD}{line[1:-1]}{RESET}{CYAN}|{RESET}")
    return "\n".join(styled)


def apply_key(key: str, selected: int, count: int) -> int:
    """Pure navigation: one key plus the current 0-based selection gives the next one.
    Up/Down wrap around the ends; a digit jumps straight to that option (1-based, like the
    text fallback); anything else leaves the selection where it was."""
    if key == "up":
        return (selected - 1) % count
    if key == "down":
        return (selected + 1) % count
    if key.isdigit():
        index = int(key) - 1
        if 0 <= index < count:
            return index
    return selected


def interactive_choose(question: str, options: List[str], default: int = 1) -> int:
    """Draws the list, moves the highlight with the arrow keys, Enter confirms.
    Ctrl+C (or Esc) raises KeyboardInterrupt, same as anywhere else in the CLI."""
    _enable_windows_ansi()
    selected = max(0, min(default - 1, len(options) - 1))
    first = True
    while True:
        lines = [f"? {question}"] + [_option_line(option, index == selected) for index, option in enumerate(options)]
        _draw(sys.stdout, lines, first=first)
        first = False
        key = read_key()
        if key == "enter":
            _draw(sys.stdout, [f"{CYAN}*{RESET} {question}: {BOLD}{options[selected]}{RESET}"], first=False, clear_extra=len(lines) - 1)
            return selected + 1
        selected = apply_key(key, selected, len(options))


def _option_line(option: str, active: bool) -> str:
    if active:
        return f"  {CYAN}>{RESET} {BOLD}{option}{RESET}"
    return f"    {DIM}{option}{RESET}"


def _draw(stream: TextIO, lines: List[str], *, first: bool, clear_extra: int = 0) -> None:
    if not first:
        stream.write(f"\x1b[{len(lines) + clear_extra}A")
    for line in lines:
        stream.write("\x1b[2K\r" + line + "\n")
    for _ in range(clear_extra):
        stream.write("\x1b[2K\r\n")
    stream.flush()


def read_key() -> str:
    if sys.platform == "win32":
        return _read_key_windows()
    return _read_key_posix()


def _read_key_windows() -> str:
    import msvcrt

    ch = msvcrt.getch()
    if ch in (b"\x00", b"\xe0"):
        ch2 = msvcrt.getch()
        return {b"H": "up", b"P": "down"}.get(ch2, "")
    if ch in (b"\r", b"\n"):
        return "enter"
    if ch in (b"\x03", b"\x1b"):
        raise KeyboardInterrupt
    text = ch.decode("utf-8", errors="ignore")
    return text if text.isdigit() else ""


def _read_key_posix() -> str:
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            if select.select([sys.stdin], [], [], 0.05)[0]:
                rest = sys.stdin.read(2)
                return {"[A": "up", "[B": "down"}.get(rest, "")
            raise KeyboardInterrupt
        if ch in ("\r", "\n"):
            return "enter"
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch if ch.isdigit() else ""
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _enable_windows_ansi() -> None:
    """Legacy conhost.exe needs virtual-terminal processing turned on before ANSI codes
    render instead of printing as garbage; Windows Terminal already has it on. Best effort:
    never breaks the picker if this fails."""
    global _ansi_ready
    if _ansi_ready or sys.platform != "win32":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:  # noqa: BLE001 - cosmetic only
        pass
    _ansi_ready = True


__all__ = ["apply_key", "banner", "interactive_choose", "read_key", "supports_interactive"]
