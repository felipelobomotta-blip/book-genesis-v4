# ADR 0012 — Adapter and Setup Reliability

**Status:** Accepted, 2026-09-04.

## Context

An adapter declared as `python runner/bridge_*.py` was treated as available merely because Python was on `PATH`. That did not establish that `agy` or `opencode`, which the bridge actually invokes, were installed. The Gemini bridge also included a user-specific path and passed an entire prompt through argv. Setup returned `None` both for a failed validation and an intentional skip, so the CLI could exit successfully in either case.

## Decision

- Entries in `adapters.yaml` may declare `requires`. Discovery requires every declared executable; without `requires`, it uses the first command token to retain compatibility with existing user files.
- Distributed adapters declare `agy` and `opencode` as requirements. `bridge_gemini.py` remains the stable configuration name but delegates to the Antigravity bridge, which uses NDJSON on stdin and resolves `agy` from `PATH`.
- The Opencode bridge resolves only through `PATH`, receives its prompt on stdin, and fails for invalid JSON or a response without text parts. Stdout remains reserved for clean response text.
- `run_setup()` keeps its historical `Path | None` return by default. With `return_status=True`, it reports `saved`, `kept`, `skipped`, or `failed` to the CLI: failures return a non-zero code, skips state clearly that nothing was saved, and interruption returns 130.
- `runner.cli new` and `resume` delegate through a late import to `runner.app`, the canonical guided-session entry point. The late import prevents an `app -> cli` import cycle.
- Claude is invoked with `--safe-mode`, `--disable-slash-commands`, and `--tools ""` in a temporary working directory. The supported Codex version has no equivalent universal tool-disable switch, so the runner uses an ephemeral session, `read-only` sandbox, `--ignore-user-config`, and a temporary directory. It does not pass a flag to ignore execution rules; execution policies remain under the CLI contract. This prevents sandbox writes but is not a claim of isolation without reads. Generic CLIs retain the capability model declared by their user and receive a temporary working directory.
- When a subprocess owned by the runner times out on Windows, the runner invokes `taskkill /PID <pid> /T /F`. The tree rooted at that PID is the only target. Cleanup has a bounded wait, and a cleanup failure does not replace the original timeout, which is returned as an actionable adapter error.

## Consequences

`doctor` and automatic selection no longer announce a wrapped provider as installed when its real executable is absent. A user with an older custom bridge that lacks `requires` can add dependencies for more precise discovery. No key is read merely to discover executables, and these checks do not make model calls.
