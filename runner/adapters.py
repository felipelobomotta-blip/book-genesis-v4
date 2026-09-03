"""Model adapters: the only place the runner talks to a model.

Every adapter exposes ``complete(prompt, model=...) -> str``. The model never gets
tools; the runner does all file I/O. CLI adapters shell out to the locally
authenticated ``claude`` and ``codex`` command-line tools, so no API key is ever
read or stored here.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import List, Protocol, Sequence


class AdapterError(RuntimeError):
    """A model call failed or returned nothing usable."""


@dataclass(frozen=True)
class Call:
    prompt: str
    model: str


class Adapter(Protocol):
    name: str

    def complete(self, prompt: str, *, model: str = "") -> str: ...


class FakeAdapter:
    """Scripted responses for tests. Records every prompt it was sent."""

    name = "fake"

    def __init__(self, responses: Sequence[str] = ()) -> None:
        self._responses: List[str] = list(responses)
        self.calls: List[Call] = []

    def complete(self, prompt: str, *, model: str = "") -> str:
        self.calls.append(Call(prompt=prompt, model=model))
        if not self._responses:
            raise AdapterError("FakeAdapter ran out of scripted responses")
        return self._responses.pop(0)


class ClaudeCliAdapter:
    """``claude -p`` with the prompt on stdin and plain text on stdout."""

    name = "claude"

    def __init__(self, executable: str = "claude", timeout_seconds: int = 1800) -> None:
        self.executable = executable
        self.timeout_seconds = timeout_seconds

    def build_command(self, model: str = "") -> List[str]:
        command = _resolve(self.executable) + [
            "-p",
            "--output-format",
            "text",
            "--no-session-persistence",
        ]
        if model:
            command += ["--model", model]
        return command

    def complete(self, prompt: str, *, model: str = "") -> str:
        result = _run(self.build_command(model), prompt, timeout_seconds=self.timeout_seconds)
        if result.returncode != 0:
            raise AdapterError(f"claude exited {result.returncode}: {result.stderr.strip()[:800]}")
        text = result.stdout.strip()
        if not text:
            raise AdapterError("claude returned empty output")
        _warn_if_undecodable(text, "claude")
        return text


class CodexCliAdapter:
    """``codex exec`` with the prompt on stdin; the reply is read from --output-last-message."""

    name = "codex"

    def __init__(self, executable: str = "codex", timeout_seconds: int = 1800) -> None:
        self.executable = executable
        self.timeout_seconds = timeout_seconds

    def build_command(
        self,
        model: str = "",
        last_message_file: Path | None = None,
        workdir: Path | None = None,
    ) -> List[str]:
        # --ignore-user-config skips the MCP servers and skills in ~/.codex/config.toml
        # (auth still works). The model gets no tools here, so that context is pure cost:
        # measured 40 s and ~20k tokens per call before a single word of the prompt.
        command = _resolve(self.executable) + [
            "exec",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ephemeral",
            "-s",
            "read-only",
        ]
        if workdir is not None:
            command += ["-C", str(workdir)]
        if last_message_file is not None:
            command += ["-o", str(last_message_file)]
        if model:
            command += ["-m", model]
        return command

    def complete(self, prompt: str, *, model: str = "") -> str:
        with tempfile.TemporaryDirectory(prefix="book-genesis-codex-") as tmp:
            last_message = Path(tmp) / "last-message.md"
            result = _run(
                self.build_command(model, last_message, Path(tmp)),
                prompt,
                timeout_seconds=self.timeout_seconds,
            )
            if result.returncode != 0:
                raise AdapterError(f"codex exited {result.returncode}: {result.stderr.strip()[:800]}")
            if not last_message.exists():
                raise AdapterError("codex did not write the last-message file")
            text = last_message.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            raise AdapterError("codex returned empty output")
        _warn_if_undecodable(text, "codex")
        return text


def _warn_if_undecodable(text: str, adapter_name: str) -> None:
    """Long `claude -p` replies on Windows occasionally carry a byte pair that is not UTF-8
    (measured: 2 in ~30k bytes on one 3-minute reply; short replies are clean). The runner
    keeps the text and says so, because a silent U+FFFD in prose would reach the judge."""
    count = text.count("�")
    if count:
        sys.stderr.write(f"warning: {count} undecodable character(s) in {adapter_name} output; search for �\n")


def _resolve(executable: str) -> List[str]:
    path = shutil.which(executable)
    if not path:
        raise AdapterError(f"{executable!r} was not found on PATH")
    if path.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", path]
    return [path]


def _run(command: List[str], prompt: str, *, timeout_seconds: int) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)  # allow `claude -p` to run from inside a Claude Code session
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        command,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        env=env,
        check=False,
    )
