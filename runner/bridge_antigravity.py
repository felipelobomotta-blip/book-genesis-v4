"""Bridge for the Antigravity CLI, `agy` (ADR 0010).

Google retired the Gemini CLI for individual accounts on 2026-06-18; `agy` is the successor.
The prompt goes in as one NDJSON user event on stdin, never on the command line, because a
chapter prompt is far past the 32k character limit Windows puts on a command line.

Measured on 2026-09-04 (agy 1.1.26):

    stdin : {"event":"user","message":{"content":"..."}}
    stdout: {"event":"init",...}
            {"event":"step_update",...}
            {"event":"result","result":{"status":"SUCCESS","response":"OK\\n", ...}}

`status` is `ERROR` for a refused model or an exhausted quota, and the reason is in `error`;
the exit code alone is not enough, so the status is what decides here. Model ids come from
`agy models` (gemini-3.8-flash-high, gemini-3.1-pro-high, claude-sonnet-4-6, ...).
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Optional, Tuple

PRINT_TIMEOUT = "30m"


def build_command(model: str) -> list:
    command = ["agy", "--input-format", "stream-json", "--output-format", "stream-json", "--print-timeout", PRINT_TIMEOUT]
    if model:
        command += ["--model", model]
    return command


def encode_prompt(prompt: str) -> str:
    return json.dumps({"event": "user", "message": {"content": prompt}}) + "\n"


def parse_result(stdout: str) -> Tuple[str, str, Optional[str]]:
    """``(status, response, error)`` from the stream. A stream without a result event is a
    failure, not an empty book chapter."""
    status, response, error = "", "", None
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event") != "result":
            continue
        result = event.get("result", {})
        status = str(result.get("status", ""))
        response = str(result.get("response", ""))
        error = result.get("error") or None
    if not status:
        return "NO_RESULT", "", "agy produced no result event"
    return status, response, error


def main() -> None:
    model = sys.argv[1].strip() if len(sys.argv) > 1 else ""
    prompt = sys.stdin.read()
    if not prompt.strip():
        sys.stderr.write("bridge_antigravity: empty prompt on stdin\n")
        raise SystemExit(2)

    result = subprocess.run(
        build_command(model),
        input=encode_prompt(prompt),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    status, response, error = parse_result(result.stdout)
    if status != "SUCCESS" or not response.strip():
        sys.stderr.write(f"agy status={status or 'unknown'}: {error or result.stderr.strip() or 'no response'}\n")
        raise SystemExit(result.returncode or 1)
    sys.stdout.write(response.strip())


if __name__ == "__main__":
    main()
