# Portability

Book Genesis is agent-agnostic by design. It is a folder of markdown instructions, phase prompts, manifests, scoring rules, and file contracts. Any agent that can read files and write project artifacts can run it.

> **2026-09-02 (ADR 0001):** the canonical way to run Book Genesis is now the Python runner (`docs/runner.md`), which drives the `claude` and `codex` CLIs. The notes below describe how the phase prompts can still be followed by hand in other agents; they are partly historical.

The repository has three layers:

1. The **runner** in `runner/` and the prompt templates in `agents/` (canonical).
2. The phase prompts and manifest in `skills/book-genesis-codex/`, which the runner follows.
3. Everything earlier, in `legacy/` (not maintained).

The `book-genesis-codex` folder name is historical and kept for compatibility. It does not mean the pipeline only works in Codex.

## Minimum Portable Package

Minimum:

```text
skills/book-genesis-codex/
```

Recommended:

```text
AGENTS.md
skills/book-genesis-codex/
docs/book-genesis-codex.md
docs/portability.md
docs/book-gallery.md
examples/cases/
assets/covers/
```

Do not copy only `SKILL.md`; the skill will lose the phase prompts, manifest, orchestration rules, and scoring contract.

## Claude Code

Claude Code supports multi-file skills with `SKILL.md` plus supporting resources. Install with:

```bash
./install.sh
```

or on Windows:

```powershell
.\install.ps1
```

The installer copies the full skill folders into `~/.claude/skills/`, including `references/`.

Invocation:

```text
/book-genesis-codex
```

The older commands (`/book-genesis`, `/book-genesis-full`) moved to `legacy/` on 2026-09-02 and are no longer installed.

## Codex

Codex can use the core directly from the repo or from Felipe's local skill directory. The important part is that the whole folder is available, not just `SKILL.md`, because the phase prompts live under `references/`.

Expected behavior:

- load `AGENTS.md` or `skills/book-genesis-codex/SKILL.md`
- read `references/pipeline/manifest.yaml`
- load only the active phase prompt
- write project state and artifacts to files
- update `PROJECT_STATE.yaml` after every phase or chapter block

## Antigravity

Antigravity-style IDEs do not need native skill support. Open the repository and tell the agent:

```text
Use Book Genesis. Follow AGENTS.md and the phase order in skills/book-genesis-codex/references/pipeline/manifest.yaml.
Persist every important decision to files.
Only load the active phase prompt.
Do not skip adversarial audit.
```

If the agent asks for the relevant files, provide:

```text
AGENTS.md
skills/book-genesis-codex/SKILL.md
skills/book-genesis-codex/references/pipeline/manifest.yaml
```

## Kimi

Kimi can run Book Genesis as a file-backed playbook. Use the same package:

```text
skills/book-genesis-codex/
```

Then give this instruction:

```text
You are running Book Genesis. Read SKILL.md, then follow the manifest one phase at a time. Create PROJECT_STATE.yaml and ASSUMPTIONS.md. Write artifacts to files. Audit before scoring.
```

If Kimi is being used in a chat-only context, paste `AGENTS.md`, `SKILL.md`, and the active phase prompt. For serious book work, keep a project folder and update the files between turns.

## Other Agents

The minimum requirements are:

- can read a folder of markdown files
- can follow a YAML or markdown phase manifest
- can create and update files
- can keep project state across turns
- can separate drafting, audit, scoring, and packaging

Use this generic instruction:

```text
Run Book Genesis as a file-backed book production pipeline. Read AGENTS.md first. Use skills/book-genesis-codex/SKILL.md as the operating loop. Follow the manifest exactly. Load only the active phase prompt. Persist decisions to files. Never score before adversarial audit.
```

## Why It Ports Cleanly

Book Genesis avoids tool-specific dependencies:

- no external API is required
- no database is required
- no build step is required
- prompts are plain markdown
- project state is plain YAML/markdown
- quality control is defined as written contracts, not hidden runtime logic

That is why the same core can work in Claude Code, Codex, Antigravity, Kimi, and most capable coding agents.
