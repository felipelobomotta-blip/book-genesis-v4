---
name: book-genesis
description: Use when the user wants to create, plan, draft, evaluate, revise, package, or run a complete AI-assisted book pipeline. Book Genesis turns a one-line idea into a book project with intake, foundation, architecture, drafting, adversarial audit, Genesis Score, and editorial package artifacts.
---

# Book Genesis

Book Genesis is Felipe's local book-production pipeline adapted for Codex. It uses the newer `book-genesis-codex` core as the canonical workflow.

Use this skill for:

- fiction, memoir, nonfiction, or hybrid book projects
- turning a rough idea into a structured book
- drafting full manuscripts chapter by chapter
- auditing AI-written prose and narrative structure
- producing Genesis Score evaluations
- creating synopses, cover briefs, launch/editorial packages, and formatting handoff notes

Do not use the legacy V4 17-phase workflow as the default. It is copied only for historical reference in `references/legacy-v4-book-genesis.md`.

## Core Rule

Persist important decisions to files. A Book Genesis run should leave a durable project tree, not just chat output.

Commercial-length is a hard contract, not a preference. A manuscript cannot be called complete, final-scored as publication-ready, or packaged for a bestseller/public launch unless it either:

- meets the genre/audience `target_floor_words` recorded in `PROJECT_STATE.yaml`, or
- is explicitly positioned from intake as a novella, short novel, or serial installment.

If no explicit short-form positioning exists, default to full-length commercial book standards.

Default project layout:

```text
<project>/
  PROJECT_STATE.yaml
  ASSUMPTIONS.md
  artifacts/
  manuscript/
    chapters/
  evaluations/
  delivery/
```

## Canonical Pipeline

Load `references/pipeline/manifest.yaml` before starting or advancing phases.

1. Phase 0: Intake
2. Phase 1: Foundation
3. Phase 2: Architecture
4. Phase 3: Drafting
5. Phase 4: Adversarial Audit
6. Phase 5: Literary Barrier Revision Loop
7. Phase 6: Final Score
8. Phase 7: Editorial Package

Use `references/pipeline/phases.md` for the compact phase overview.

## Phase References

Read only the prompt for the active phase:

- Intake: `references/prompts/intake.md`
- Foundation: `references/prompts/foundation.md`
- Architecture: `references/prompts/architecture.md`
- Drafting: `references/prompts/drafting.md`
- Adversarial Audit: `references/prompts/adversarial-audit.md`
- Literary Barrier Revision Loop: `references/prompts/literary-barrier-loop.md`
- Final Score: `references/scoring/genesis-score-codex.md`
- Editorial Package: `references/prompts/editorial-package.md`

`references/prompts/orchestrator.md` contains the portable orchestration rules.

## Operating Loop

1. Identify or create the project directory.
2. Read `PROJECT_STATE.yaml` if it exists. If not, initialize it from the manifest phases and user idea.
3. Read `ASSUMPTIONS.md` if it exists. If not, create it and mark inferred assumptions clearly.
4. Confirm or infer the commercial-length contract before architecture or drafting:
   - `target_range_words`
   - `target_floor_words`
   - `target_ceiling_words`
   - `positioning`: full-length novel, novella, short novel, serial, nonfiction, etc.
   - `chapter_count_planned`
   - `average_words_per_chapter_planned`
5. Load the current phase prompt and produce only that phase's required outputs.
6. Update `PROJECT_STATE.yaml` after every phase, chapter block, audit, or score.
   - record cumulative manuscript word count
   - record planned vs actual word count by chapter/block
   - record whether the length gate is `PASS`, `FLAG`, or `BLOCK`
7. Do not skip Phase 4. Audit before final scoring.
8. When drafting, write in chapter files under `manuscript/chapters/` and keep the state synchronized.
9. When user feedback changes direction, record it in project files before continuing.
10. If the user asks to break a quality threshold such as 8.5, activate the Literary Barrier loop after the adversarial audit and keep iterating until the calibrated critical score clears the threshold or the blocker is documented as requiring human/editorial input.
11. If the manuscript is below `target_floor_words`, run expansion/re-architecture before any final score or editorial package claims publication readiness.

## Quality Policy

- Prefer fewer constraints during drafting; evaluate and repair afterward.
- Separate drafting, audit, scoring, and editorial judgment in the workflow.
- Use the Genesis Score floor principle: the book is only as strong as its weakest major dimension.
- Treat internal literary scores as inflated until calibrated. Apply the score calibration rules in the scoring reference before claiming a threshold was reached.
- Do not optimize prose to satisfy rubrics while drafting. The writer writes; the critic and editor operate after text exists.
- For Portuguese books, write artifacts and prose in Portuguese unless the user requests otherwise.
- If a task is only editing, scoring, or packaging an existing manuscript, start from the matching phase instead of forcing a full restart.
- Do not let literary quality hide product incompleteness. A brilliant 46k-word draft is not a full-length adult thriller unless the project explicitly chose short-form positioning.
- Bestseller/public-launch readiness requires both craft strength and product fit: length, package, target reader, cover/copy, metadata, and launch plan.

## Complementary Skills

Use these only when relevant and already available:

- `copy-editing` for prose-level cleanup
- `book-swarm-panel` for MiroFish-style simulated reader swarms, niche-risk scouting, public-opinion tests, heatmaps, interviews, and revision tickets
- `humanizer` for less synthetic phrasing
- `launch-strategy` or `content-strategy` for go-to-market assets
- `imagegen` or cover-specific workflows for cover ideation
