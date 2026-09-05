"""Bridge for the Hermes agent CLI (ADR 0010).

`hermes chat -Q --query-file -` reads the prompt from stdin, which is the only safe way to
send a chapter prompt on Windows (the command line stops at 32k characters). `-Q` is the
quiet, programmatic mode: the session id goes to stderr instead of stdout.

Measured on 2026-09-04: stdout still opens with lines like `Warning: Unknown toolsets: bfl`
before the answer, so those are stripped. Everything after the last warning is the reply.
"""

from __future__ import annotations

import re
import subprocess
import sys

DEFAULT_MODEL = ""
NOISE = re.compile(r"^(warning|note|info|deprecat\w*)\s*:", re.IGNORECASE)


def strip_noise(text: str) -> str:
    """Drop the CLI's own leading chatter; stop at the first line of the real answer."""
    lines = text.splitlines()
    start = 0
    for index, line in enumerate(lines):
        if line.strip() and not NOISE.match(line.strip()):
            start = index
            break
        start = index + 1
    return "\n".join(lines[start:]).strip()


def build_command(model: str) -> list:
    command = ["hermes", "chat", "-Q", "--query-file", "-"]
    if model:
        command += ["-m", model]
    return command


def main() -> None:
    model = sys.argv[1].strip() if len(sys.argv) > 1 else DEFAULT_MODEL
    prompt = sys.stdin.read()
    if not prompt.strip():
        sys.stderr.write("bridge_hermes: empty prompt on stdin\n")
        raise SystemExit(2)

    result = subprocess.run(
        build_command(model),
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout)
        raise SystemExit(result.returncode)

    answer = strip_noise(result.stdout)
    if not answer:
        sys.stderr.write("bridge_hermes: hermes answered with nothing but warnings\n")
        sys.stderr.write(result.stdout[:2000])
        raise SystemExit(1)
    sys.stdout.write(answer)


if __name__ == "__main__":
    main()
