"""Model adapters: the only place the runner talks to a model.

Every adapter exposes ``complete(prompt, model=...) -> str``. The model never gets
tools; the runner does all file I/O. CLI adapters shell out to locally authenticated
command-line tools, so no API key is ever read or stored here. The generic adapter
runs any command declared in runner/config/adapters.yaml; the manual adapter writes
the prompt to disk and waits for a person to paste the reply (ADR 0002).
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, Dict, List, Optional, Protocol, Sequence, Tuple, Union
import urllib.error
import urllib.request

DEFAULT_MAX_TOKENS = 16000
Transport = Callable[[str, Dict[str, str], bytes, int], Tuple[int, bytes]]


class AdapterError(RuntimeError):
    """A model call failed or returned nothing usable."""


class AwaitingManual(RuntimeError):
    """Manual adapter: the prompt is on disk; a person has to paste the model's reply."""

    def __init__(self, prompt_path: Path, response_path: Path, role: str) -> None:
        super().__init__(
            f"[{role}] prompt written to {prompt_path}. Send it to your model, paste the full reply "
            f"into {response_path}, then run the same command again."
        )
        self.prompt_path = prompt_path
        self.response_path = response_path
        self.role = role


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


class GenericCliAdapter:
    """Any command-line model tool: prompt on stdin, reply on stdout.

    The command is a template from runner/config/adapters.yaml; ``{model}`` is replaced
    by the role's model name, which may be empty.
    """

    def __init__(self, name: str, command_template: str, timeout_seconds: int = 1800) -> None:
        self.name = name
        self.command_template = command_template
        self.timeout_seconds = timeout_seconds

    def render_command(self, model: str = "") -> str:
        return " ".join(self.command_template.replace("{model}", model).split())

    def complete(self, prompt: str, *, model: str = "") -> str:
        command = self.render_command(model)
        head, rest = _split_head(command)
        resolved = shutil.which(head)
        if resolved is None:
            raise AdapterError(f"{head!r} (adapter {self.name}) was not found on PATH")
        if resolved.lower().endswith((".cmd", ".bat")):
            command = f'cmd /c "{resolved}" {rest}'.strip()
        result = _run(command, prompt, timeout_seconds=self.timeout_seconds)
        if result.returncode != 0:
            raise AdapterError(f"{self.name} exited {result.returncode}: {result.stderr.strip()[:800]}")
        text = result.stdout.strip()
        if not text:
            raise AdapterError(f"{self.name} returned empty output")
        _warn_if_undecodable(text, self.name)
        return text


class ManualAdapter:
    """For people with a chat window and no CLI: the prompt becomes a file, the reply too.

    File names are derived from a hash of the prompt, and the runner's prompts are
    deterministic, so re-running the same command finds the pasted reply.
    """

    name = "manual"

    def __init__(self, directory: Path, role: str) -> None:
        self.directory = Path(directory)
        self.role = role

    def paths_for(self, prompt: str) -> Tuple[Path, Path]:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:10]
        stem = f"{digest}-{self.role}"
        return self.directory / f"{stem}.prompt.md", self.directory / f"{stem}.response.md"

    def complete(self, prompt: str, *, model: str = "") -> str:
        prompt_path, response_path = self.paths_for(prompt)
        if response_path.exists():
            text = response_path.read_text(encoding="utf-8").strip()
            if text:
                return text
        self.directory.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(prompt, encoding="utf-8")
        raise AwaitingManual(prompt_path, response_path, self.role)


class OpenAICompatibleAdapter:
    """Any ``/chat/completions`` endpoint: OpenRouter, DeepSeek, OpenAI, Groq, Together, local servers.

    Stdlib only. The key travels in the Authorization header and nowhere else; error messages
    have it masked. ``transport`` is injectable so tests never touch the network.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        *,
        timeout_seconds: int = 1800,
        transport: Optional[Transport] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.transport: Transport = transport or _http_post
        self.extra_headers = dict(extra_headers or {})

    def complete(self, prompt: str, *, model: str = "") -> str:
        if not model:
            raise AdapterError(f"{self.name}: a model name is required for this provider (set it with `book-genesis setup`)")
        if not self.api_key:
            raise AdapterError(f"{self.name}: no API key; run `book-genesis setup` or set the provider's environment variable")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            **self.extra_headers,
        }
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
        status, raw = self.transport(f"{self.base_url}/chat/completions", headers, body, self.timeout_seconds)
        if status != 200:
            raise AdapterError(f"{self.name} returned HTTP {status}: {_safe_excerpt(raw, self.api_key)}")
        try:
            data = json.loads(raw.decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AdapterError(f"{self.name}: unexpected response shape: {_safe_excerpt(raw, self.api_key)}") from exc
        text = (text or "").strip()
        if not text:
            raise AdapterError(f"{self.name} returned empty output")
        _warn_if_undecodable(text, self.name)
        return text


class AnthropicAdapter:
    """The Anthropic Messages API, stdlib only."""

    def __init__(
        self,
        name: str,
        base_url: str,
        api_key: str,
        *,
        timeout_seconds: int = 1800,
        transport: Optional[Transport] = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.transport: Transport = transport or _http_post
        self.max_tokens = max_tokens

    def complete(self, prompt: str, *, model: str = "") -> str:
        if not model:
            raise AdapterError(f"{self.name}: a model name is required for this provider (set it with `book-genesis setup`)")
        if not self.api_key:
            raise AdapterError(f"{self.name}: no API key; run `book-genesis setup` or set ANTHROPIC_API_KEY")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
        }
        body = json.dumps(
            {"model": model, "max_tokens": self.max_tokens, "messages": [{"role": "user", "content": prompt}]}
        ).encode("utf-8")
        status, raw = self.transport(f"{self.base_url}/v1/messages", headers, body, self.timeout_seconds)
        if status != 200:
            raise AdapterError(f"{self.name} returned HTTP {status}: {_safe_excerpt(raw, self.api_key)}")
        try:
            data = json.loads(raw.decode("utf-8"))
            text = "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")
        except (ValueError, AttributeError, TypeError) as exc:
            raise AdapterError(f"{self.name}: unexpected response shape: {_safe_excerpt(raw, self.api_key)}") from exc
        text = text.strip()
        if not text:
            raise AdapterError(f"{self.name} returned empty output")
        _warn_if_undecodable(text, self.name)
        return text


def _http_post(url: str, headers: Dict[str, str], body: bytes, timeout_seconds: int) -> Tuple[int, bytes]:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()
    except urllib.error.URLError as error:
        raise AdapterError(f"could not reach {url}: {error.reason}") from error


def _safe_excerpt(raw: bytes, secret: str) -> str:
    text = raw.decode("utf-8", errors="replace")
    if secret:
        text = text.replace(secret, "***")
    return " ".join(text.split())[:300]


def _resolve(executable: str) -> List[str]:
    path = shutil.which(executable)
    if not path:
        raise AdapterError(f"{executable!r} was not found on PATH")
    if path.lower().endswith((".cmd", ".bat")):
        return ["cmd", "/c", path]
    return [path]


def _split_head(command: str) -> Tuple[str, str]:
    """First token of a command line (quotes respected) and the rest."""
    text = command.strip()
    if text.startswith('"'):
        end = text.find('"', 1)
        if end != -1:
            return text[1:end], text[end + 1 :].strip()
    parts = text.split(None, 1)
    return parts[0], (parts[1] if len(parts) > 1 else "")


def _run(command: Union[str, Sequence[str]], prompt: str, *, timeout_seconds: int) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)  # allow `claude -p` to run from inside a Claude Code session
    env["PYTHONIOENCODING"] = "utf-8"
    popen_args: Union[str, List[str]]
    if isinstance(command, str):
        popen_args = command if os.name == "nt" else shlex.split(command)
    else:
        popen_args = list(command)
    return subprocess.run(
        popen_args,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
        env=env,
        check=False,
    )


def _warn_if_undecodable(text: str, adapter_name: str) -> None:
    """Long `claude -p` replies on Windows occasionally carry a byte pair that is not UTF-8
    (measured: 2 in ~30k bytes on one 3-minute reply; short replies are clean). The runner
    keeps the text and says so, because a silent U+FFFD in prose would reach the judge."""
    count = text.count("�")
    if count:
        sys.stderr.write(f"warning: {count} undecodable character(s) in {adapter_name} output; search for �\n")
