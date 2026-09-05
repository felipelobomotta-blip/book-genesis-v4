# Changelog

## 5.0.0-beta.1 — Imagination Edition — 2026-09-05

Creativity comes first. This public beta makes the writing process easier to inspect, continue and question.

### Added and improved

- Guided sessions with three author checkpoints, persistent notes and safe resume.
- Complete-response validation, recoverable phase publication and immutable chapter-attempt history.
- A manuscript audit that reads canonical prose and blocks completion when revision is needed.
- A local browser reader with chapter navigation, revision comparison and editorial status.
- Canonical Markdown/EPUB exports and a self-contained wheel installable outside the source checkout.
- More reliable provider detection, portable CLI bridges, Windows path/timeout handling and truthful setup errors.
- English and Portuguese documentation, architecture, vision, roadmap, contribution guide, a worked example and a complete marketing kit.

### Evidence and scope

- The preceding quality pass completed 279 local tests, package isolation checks, browser checks and a bounded real-provider exercise. See the [validation record](docs/validation.md) for final release checks and limitations.
- A real audit rejected a structural ending flaw despite favorable model-reader signals. The beta now preserves that objection instead of treating the report file as approval.
- Engineering assistance: **Astra in Codex**, with independent review and recorded tests. This credit does not make Astra a runtime dependency or imply an official OpenAI product.
- Still a beta: no claim of human-reader preference, long-book reliability, guaranteed bestseller status or automatic structural repair.

### Earlier development history

Entries below record what earlier iterations proposed or implemented at the time. Old score thresholds and market claims are not the current specification.

## V5.0 — 2026-09-02 (branch `arch/runner-orchestrates`, unreleased)

### Changed: the runner orchestrates; the judge is blind

Recorded in `docs/adr/0001-runner-orquestra-juiz-cego.md`, motivated by the line-by-line review in `docs/REVISAO-CONSISTENCIA-2026-09.md` (three pipelines, four gate definitions and three rubrics coexisting; the 8.5 gate was self-grading; the last real project had seven chapters and zero evaluations).

- `runner/` now calls models through the local `claude` and `codex` CLIs (no API keys anywhere) and runs the whole pipeline: `run-phase` for phases 0–2 and the post-draft diagnostics, `book` / `chapter` for drafting, `judge` for any chapter file, `approve` for the human checkpoint.
- New `agents/book-judge.md`: a blind reader that sees prose only (plus the previous chapter's tail) and answers `turn_page`, `stopped_at`, `remember`, `flags`; after an edit it compares drafts (`better` / `worse` / `same`). There is no numeric gate any more.
- The writer template no longer teaches the rubric; `agents/book-evaluator.md` is a diagnostic for the editor, not a gate.
- `dialogue-polish` and `hook-craft` became modes of `agents/book-editor.md`, run only when the judge flags them. `book-orchestrator` became code.
- Constants centralised in `runner/config/genre-profiles.yaml` and `runner/config/models.yaml`; the judge defaults to a different model family than the writer.
- A human must approve chapter 1 (`approve <project> chapter-01`) before chapter 2 is written.
- Three earlier pipelines (`skills/book-genesis-full`, `skills/book-genesis`, `skills/optional`, `skills/deprecated`, the orchestrator agent, `docs/architecture.md`) moved, not deleted, to `legacy/`.
- Mechanical fixes from the review (README duplicates, loop max 3 vs 5, dimension 7 never set, `grep -P`, destructive `sed`, taxonomy of structural types, dialogue range).
- **ADR 0002, same day:** no human in the loop by default. Chapter 1 is judged by a panel of three blind readers (different personas; different families when installed; majority decides, flags need two votes); `--human` restores the pause. `doctor` shows what is installed and how roles fall back; a single-family run carries a warning in `RUN_REPORT.md`. Any CLI can be declared in `runner/config/adapters.yaml`; `--manual` turns every call into a prompt file for chat-only setups (exit 5). `panel <project> <n>` runs the panel on any written chapter.
- **ADR 0003, same day:** a real command. `pip install -e .` gives `book-genesis`; `setup` is a terminal wizard that stores the person's providers, keys (hidden input; file or environment variable) and models in `~/.book-genesis/config.yaml`, which wins over the repository defaults; providers by API with the standard library only (`openai` type for OpenRouter, DeepSeek, OpenAI, Groq, Together, Ollama, LM Studio and any compatible endpoint; `anthropic` type for the Messages API); `new` runs from the idea to the editorial package with progress on screen; `resume` continues; `doctor` reports key status without ever printing a key.
- **ADR 0004 (2026-09-03):** onboarding shaped like OpenClaw, Hermes and opencode. `setup` detects CLIs, key variables and local servers; one-keystroke quick start; numbered menus; models listed live from the provider; subscriptions through the OAuth logins of the Claude Code and Codex CLIs (with install/login help when missing); a real completion for writer and judge before anything is saved; keep/change/reset on re-run.
- Tests: 12 → 113, no network.

## V4.2 — 2026-06-10

### Added: Premise Forge (Phase 1.5)

The pipeline now transforms raw ideas into structurally sound premises **before** writing starts.

Previously, the system executed your idea as-is. If your shower thought lacked an irony engine — the structural contradiction that makes readers unable to put a book down — the best prose in the world couldn't fix it.

Phase 1.5 introduces a forge step between research and foundation:

- `book-architect` is dispatched in "forge mode" (dispatch 0)
- 5 premise variants are generated: Variant 1 is your raw idea scored honestly; Variants 2–5 use different irony engines (inverted protagonist, relocated stakes, market gap fusion, weaponized reader frustrations from negative comp reviews, collapsed character contradiction)
- Each variant is scored across 6 dimensions: hook, irony engine, native escalation, the central question, gap fit, retellability
- The floor IS the score — a 9/9/9/9/9/4 is a 4
- Winner needs floor ≥ 8.0; one re-forge round allowed; if still below 8.0, the system proceeds with the best variant and flags it at Checkpoint 1
- Hard rule: **ELEVATE, DON'T REPLACE** — you must recognize your idea inside the winning premise
- Output: `premise.md` — binding for the entire foundation downstream

Checkpoint 1 now opens by showing you the transformation: raw idea → forged pitch sentence → "what changed and why" in plain language.

### Added: 8.5 Gate System

The quality gate was previously a target without enforcement. V4.2 makes it a hard gate:

- **Per-chapter gate**: chapters below 8.5 on Genesis Floor or Casual score cannot advance
- **Polish Loop**: the evaluator produces a "Path to 8.5" work order; the editor targets only the blocking dimensions; max 5 iterations per chapter
- **Anti-inflation**: each polish cycle can add +0.5 maximum — jumping from 7.5 to 8.5 requires ≥ 2 real improvement cycles
- **3-state verdict**: PASS (Floor ≥ 8.5 AND Casual ≥ 8.5) / POLISH (above hard floor but below 8.5) / FAIL (below hard floor)
- **Exit gate**: manuscript only moves to packaging when ALL chapters ≥ 8.5 AND CVI-Launch ≥ 9.0

The hard floor is genre-adjusted: literary fiction and memoir set it at 7.5; commercial fiction, thriller, and prescriptive nonfiction at 7.0.

### Added: Phase 5 exit criteria

Phase 5 (full manuscript revision) now has a concrete exit condition:
- Every chapter must hold Genesis Floor ≥ 8.5
- CVI-Launch must reach ≥ 9.0 ("breakout potential, Gone Girl tier")
- Up to 3 full revision cycles
- If still below after 3 cycles: explicit decision at Checkpoint 2 (proceed anyway, keep revising, or abort)

### Changed: book-architect

- Role updated from 2 dispatches to 3 (dispatch 0 = forge mode → premise.md, dispatch 1 = foundation + outline, dispatch 2 = voice DNA)
- New section: PREMISE FORGE MODE — full scoring rules, variant generation instructions, elevate-don't-replace constraint, genre shift detection
- Foundation section now reads premise.md first; the winning variant's irony engine, escalation ladder, and central question are binding inputs
- Beat Subversion marked MANDATORY in outline section

### Changed: book-orchestrator

- Pipeline diagram updated with Phase 1.5
- PHASE 1.5 block added with full dispatch instructions, after-return state update, and genre-shift delta research trigger
- CHECKPOINT 1 updated to show premise transformation first
- Parallelism chain updated: research → premise forge → foundation → voice DNA → entity build → outline continuity
- Project init tree updated with premise.md

### Changed: README

- Full rewrite. Previous README described V3 architecture with different agent names.
- New README explains the pipeline in plain English, describes all 3 gates with concrete scoring examples, and lists all 8 agents with plain-English descriptions.

### Added: all 8 agents to `agents/` folder

Previous repo only contained `book-orchestrator.md`. All agents now included:
- `book-orchestrator.md`
- `book-architect.md`
- `book-researcher.md`
- `book-writer.md`
- `book-evaluator.md`
- `book-editor.md`
- `book-disruptor.md`
- `book-packager.md`

---

## V4.0 — 2026-05-26 (initial public release)

- First public release of Book Genesis V4
- 8.5+ editorial quality target (not yet enforced as a hard gate)
- 9-skill book studio documentation
- MIT licensed
