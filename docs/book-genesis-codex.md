# Book Genesis Runner Map

`skills/book-genesis-codex/` contains the phase prompts and supporting references used by the local Book Genesis runner. The folder name is retained for compatibility; the supported product path is the Python runner, not a chat command that asks an agent to write project files on its own.

Start with [Quickstart](quickstart.md), [Architecture](architecture.md), and the operational [Runner reference](runner.md).

## Current execution model

```text
book-genesis new / resume
  └─ runner session
      ├─ run-phase: Intake, Foundation, Architecture
      ├─ book / chapter: Drafting
      └─ run-phase: Audit, internal Score, Editorial Package
```

The runner reads phase prompts, assembles context from the project directory, calls an adapter, validates the response contract, and writes approved outputs. A model returns text only; it does not own state transitions or project file writes.

The canonical pipeline has seven stages:

| Stage | Primary output |
|---|---|
| Intake | assumptions, brief, market map, story engine |
| Foundation | characters, theme, emotional curve |
| Architecture | outline, tension map, opening strategy |
| Drafting | canonical chapter files and attempt history |
| Adversarial Audit | manuscript-level editorial report |
| Final Score | internal model-reader process signal |
| Editorial Package | logline, synopsis, blurb, and related draft materials |

## Key contracts

- Drafting runs one chapter at a time. A blind judge sees prose and the previous chapter tail, not the outline or writer notes.
- Chapter 1 can use a model-reader panel. `--human` instead requires explicit author approval before chapter 2.
- Phase replies must contain all required `=== FILE: path ===` blocks before the runner publishes them.
- The adversarial audit must contain a standalone `audit_status: pass`, `revise`, or `major_rewrite`. Only `pass` proceeds to Score and Package.
- `revise` and `major_rewrite` leave the project in `awaiting_revision`. The author revises and runs `book-genesis resume`; there is no automatic structural repair command.

The runner bundles these prompt resources into its wheel, so an installed build can run outside a repository checkout.

## Historical material

Some files in this folder and `legacy/` preserve earlier V4-era approaches, including numeric 8.5 gates, commercial-viability predictions, and chat-first commands. They are not the current runner contract and must not be used to make present-tense product claims. The decisions replacing them are recorded in the ADRs, especially [ADR 0001](adr/0001-runner-orquestra-juiz-cego.md) and [ADR 0015](adr/0015-gate-semantico-do-audit.md).
