# Changelog

## Unreleased

### Added

- Safe portable installer for Claude Code, Codex, Kimi Code, and shared Agent Skills directories.
- Distribution manifest, dependency validation, checksums, dry-run, conflict detection, and recoverable forced replacement.
- Independent evaluator protocol with Grade A/B/C isolation reporting.
- Blind literary critic role that receives no target score or previous evaluation.
- Commercial-length fields and Literary Barrier phase in canonical runner state.
- Portable-suite and installer regression tests.

### Changed

- `skills/book-genesis/` is now canonical universal core.
- Platform-specific agents consume shared packets and gates instead of redefining editorial logic.
- Public links now point to `felipelobomotta-blip/book-genesis-v4`.
- Legacy V4 skills, plus native Claude agents/knowledge, remain opt-in through `--include-legacy`.

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
