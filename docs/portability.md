# Portability

Book Genesis is a local Python CLI that uses model routes already available to the author. The runner, not an external agent skill, is the supported way to create, resume, audit, review, and export a project.

## Runtime requirements

- Python 3.10 or later.
- Windows, macOS, or Linux with a supported provider route.
- A writable local project directory.

Install a source checkout with `python -m pip install -e .`, then run `book-genesis setup` and `book-genesis doctor`. The wheel bundles the runner’s prompt resources and can run outside the source checkout.

## Provider routes

| Route | Status | Notes |
|---|---|---|
| Claude Code CLI | Supported | Uses the author’s logged-in CLI session. Claude is invoked with tools disabled in safe mode. |
| Codex CLI | Supported | Uses an ephemeral session, a temporary directory, and a read-only sandbox. This is not a claim that every host-level tool is disabled. |
| OpenAI-compatible or Anthropic-compatible endpoint | Supported through `setup` | The author configures and pays the chosen provider. |
| Ollama or LM Studio | Supported through compatible local-server setup | Model availability and quality depend on the local installation. |
| Declared command adapter | Supported contract | Add a command template and optional `requires` list in `~/.book-genesis/adapters.yaml`; the command determines its own capabilities. |
| Manual copy/paste | Supported | `--manual` writes local prompt files and waits for pasted responses. |

The default role plan prefers different model families for writer and judge. When that is not possible, a single-family run is allowed and recorded as a warning. No route makes model feedback equivalent to human editorial validation.

## Platform evidence

The current beta was verified locally on Windows with Python 3.11: 279 offline tests passed in the September 2026 quality verification, including recovery, history integrity, the audit gate, reader/export flows, and wheel installation outside the checkout. A GitHub Actions workflow is included for Ubuntu and Windows on Python 3.10 and 3.12, but that remote matrix has not yet been run for this beta. Treat the workflow as configured, not as completed remote evidence.

Provider behavior also varies by installed CLI version, operating system, account access, context window, and network conditions. The repository contains deterministic tests and limited real-provider probes; it does not claim that every advertised route has been live-tested on every platform.

## What ports and what does not

The project directory format, Markdown prompts, YAML state, review HTML, Markdown export, and EPUB export are local files. They can be inspected, copied, and backed up without a hosted service.

The legacy `skills/book-genesis-codex/` folder contains phase references bundled into the runner. It is not an installation recipe for every agent host. Do not rely on obsolete skill-installer paths or chat-only commands as the current product interface. Use the CLI and the operational [runner reference](runner.md).

Long manuscripts may exceed a selected provider’s context window during the full-manuscript audit. The beta does not yet provide a chunked audit design with equivalent guarantees. This is a current limit, not a portability failure hidden by a fallback.
