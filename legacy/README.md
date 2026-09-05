# Legacy

Everything in this folder was moved here on 2026-09-02 by
[ADR 0001](../docs/adr/0001-runner-orquestra-juiz-cego.md). Nothing was deleted; git history
is intact (`git log --follow`). None of it is maintained, and none of it is on the canonical path.

| what | why it left the canonical path |
|---|---|
| `agents/book-orchestrator.md` | The orchestrator is now code (`runner/`). An LLM running a state machine drifted, forgot to write state, and spent opus tokens on bookkeeping. |
| `agents/dialogue-polish.md`, `agents/hook-craft.md` | Folded into `agents/book-editor.md` as **modes**, run only when the blind judge flags `dialogue` or `hook`. |
| `skills/book-genesis-full/` | The 17-phase V4 skill pipeline: a third pipeline with its own gates (genre floor, CVI ≥ 7.0). |
| `skills/book-genesis/` | A diverged copy of `skills/book-genesis-codex/` (8 phases vs 7). The runner reads only the codex one. |
| `skills/optional/`, `skills/deprecated/` | Skill versions of agents that also existed under `agents/`; installed twice under the same name. |
| `docs/architecture-v4-skills.md` | Described the 17-phase skills pipeline, not what the README or the runner run. |

The review that led here is in
[`docs/REVISAO-CONSISTENCIA-2026-09.md`](../docs/REVISAO-CONSISTENCIA-2026-09.md). If you want the old
behaviour, copy the folder you need back and point your agent at it; the runner will not use it.
