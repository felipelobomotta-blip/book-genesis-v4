"""Bridge for opencode/muse-spark via `opencode run`.

Prompt arrives on stdin (so large chapter prompts never hit the Windows
32k argv limit). The bridge shells out to `opencode run --model {model}
--format json` with the prompt piped on stdin and prints only the
concatenated text parts to stdout — exactly what GenericCliAdapter expects.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys

DEFAULT_MODEL = "opencode/muse-spark-1.2-contributor-free"


def build_command(model: str) -> list[str]:
    """Use the PATH-resolved CLI; never couple a distributed bridge to one user."""
    executable = shutil.which("opencode")
    if not executable:
        raise FileNotFoundError("opencode was not found on PATH")
    return [executable, "run", "--model", model or DEFAULT_MODEL, "--format", "json"]


def extract_text(stdout: str) -> str:
    """Extract text events and reject malformed/empty streams as a provider failure."""
    texts: list[str] = []
    malformed = False
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            malformed = True
            continue
        if not isinstance(obj, dict):
            malformed = True
            continue
        part = obj.get("part")
        if obj.get("type") == "text" and isinstance(part, dict):
            text = part.get("text", "")
        elif isinstance(part, dict) and part.get("type") == "text":
            text = part.get("text", "")
        else:
            continue
        if isinstance(text, str) and text:
            texts.append(text)
    output = "".join(texts).strip()
    if output:
        return output
    if malformed:
        raise ValueError("opencode returned malformed JSON without text parts")
    raise ValueError("opencode returned no text parts")


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].strip() else DEFAULT_MODEL
    prompt = sys.stdin.read()
    if not prompt.strip():
        sys.stderr.write("bridge_opencode: empty prompt on stdin\n")
        sys.exit(2)

    try:
        cmd = build_command(model)
    except FileNotFoundError as exc:
        sys.stderr.write(f"bridge_opencode: {exc}\n")
        sys.exit(127)

    proc = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if proc.returncode != 0:
        # opencode prints errors to stderr; surface them for adapter error reporting
        sys.stderr.write(proc.stderr or proc.stdout)
        sys.exit(proc.returncode)

    try:
        out = extract_text(proc.stdout)
    except ValueError as exc:
        sys.stderr.write(f"bridge_opencode: {exc}\n")
        sys.exit(1)

    sys.stdout.write(out)


if __name__ == "__main__":
    main()
