---
name: book-bestseller-studio
description: Use when the user wants a complete book-production system aimed at commercial viability, bestseller positioning, agent/editor readiness, or launch readiness. Orchestrates book-genesis, book-researcher, literary-agent-panel, book-editor, copy-editing, humanizer, editorial-package, launch-strategy, and content-strategy.
---

# Book Bestseller Studio

This is the umbrella skill for creating a complete book at market level. It does not replace canonical `book-genesis`; it coordinates specialist skills and adds commercial gates.

Use this when the user says things like:

- "create a complete book"
- "bestseller-level"
- "commercially viable book"
- "prepare for agents/editors"
- "complete book pipeline"
- "market-ready"
- "publication or launch prep"

## Specialist Stack

- `book-genesis`: canonical project pipeline, state files, chapters, audits, Genesis Score.
- `book-researcher`: genre map, comp titles, reader gaps, word count targets, nonfiction evidence.
- `book-swarm-panel`: MiroFish-style simulated reader swarms, niche-risk scouting, public-opinion tests, interviews, heatmaps, and revision tickets.
- `literary-agent-panel`: simulated agent/editor/bookseller review for market acceptance.
- `book-editor`: surgical revision by mode after evaluation.
- `copy-editing`: final language cleanup.
- `humanizer`: remove synthetic phrasing and restore lived voice.
- `editorial-package`: logline, back-cover copy, synopsis, query letter, cover brief.
- `launch-strategy`: go-to-market, offer, launch calendar, proof-driven positioning.
- `content-strategy`: audience-building and content plan around the book.

`launch-strategy` and `content-strategy` are optional external companions. Do not block manuscript completion when they are not installed.

## Operating Rule

Create durable files. Do not keep the book only in chat.

Default project layout:

```text
<project>/
  PROJECT_STATE.yaml
  ASSUMPTIONS.md
  research/
  foundation/
  manuscript/
    chapters/
  evaluations/
  delivery/
  launch/
```

## Market-Level Pipeline

1. Run `book-researcher` before architecture unless user already supplied market research.
2. Run `book-genesis` phases 0-3 to build intake, foundation, architecture, and manuscript.
3. After first full draft or major act, run `literary-agent-panel`.
4. Run `book-swarm-panel` when the project needs many fictional readers, niche/sensitivity-risk scouting, public-opinion reaction, or package-framing tests.
5. Run `book-genesis` adversarial audit and Genesis Score.
6. Use `book-editor` only against specific findings. Pick mode: structural, connective, prose-texture, rag-rewrite, or factual.
7. Use `humanizer` and `copy-editing` after structure is stable.
8. Run `literary-agent-panel` and/or `book-swarm-panel` again after revision.
9. Run `editorial-package` only after manuscript passes product gates.
10. Run `launch-strategy` and `content-strategy` for public-launch readiness.

## Portable Agent Dispatch

Read `references/dispatch.md` and use `references/agent-registry.yaml` for specialist ownership. Prepare packets with `python runner/cli.py prepare-agent-packet <project> <agent>` when the runner is available.

- Claude Code: dispatch a custom or general-purpose subagent with the packet.
- Codex: dispatch an isolated subagent with the packet when available.
- Kimi Code: dispatch a fresh built-in subagent with the packet.
- No subagents: run roles sequentially, mark evaluation independence as degraded, and never call self-scoring independent.

Editorial rules remain identical across adapters. Platform-specific agent files may select tools or models, but must not redefine gates or scoring.

## Commercial Gates

Do not call a project "market-ready", "best-seller-ready", or "publication-ready" unless all gates pass or blockers are documented.

Gate 1: Product Fit

- clear genre/category
- current comp titles
- target reader defined
- reader promise stated in one sentence
- format and word count match category expectations

Gate 2: Manuscript Fit

- complete manuscript or explicit serial/novella positioning
- opening creates immediate reader contract
- chapter endings sustain forward motion
- weakest Genesis Score dimension is not hiding behind average score
- continuity and factual checks complete

Gate 3: Market Package

- logline
- 100-word cover copy
- 300-word editorial synopsis
- query/pitch letter
- cover brief with genre shelf fit
- author positioning

Gate 4: Launch Fit

- proof points or platform plan
- audience acquisition path
- content angles
- launch calendar
- review/ARC strategy
- retailer/category metadata assumptions

## Bestseller Discipline

"Bestseller" is a positioning target, not a promise. Treat it as a standard for product, package, and launch quality:

- write for a specific reader, not "everyone"
- use comp titles from the current market, not classics
- make the first 10 pages commercially ruthless
- preserve voice while improving readability
- document risks instead of pretending certainty
- separate craft excellence from market readiness

## Output Contract

For any full run, maintain:

- `research/market-research.md`
- `foundation/positioning.md`
- `manuscript/chapters/chapter-XX.md`
- `evaluations/agent-panel.md`
- `evaluations/book-swarm/<run>/SUMMARY.md`
- `evaluations/genesis-score.md`
- `delivery/editorial-package.md`
- `launch/launch-plan.md`

If user asks only for one part, run only the relevant specialist and do not force full pipeline.
