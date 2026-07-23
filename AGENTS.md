# Agent Instructions

This repository contains Book Genesis, an agent-agnostic book-production workflow made of markdown skills, manifests, prompts, scoring rules, and reference files.

## Default Behavior

When asked to create, plan, draft, audit, score, revise, or package a book, use the Universal Book Genesis Core unless the user explicitly asks for legacy V4/V5:

```text
skills/book-genesis/SKILL.md
```

Treat this as the current universal pipeline for Claude Code, Codex, Kimi Code, Antigravity, and other file-aware agents. `skills/book-genesis-codex/` remains only as a compatibility package.

When the user asks for bestseller-level, market-ready, agent/editor-ready, or launch-ready work, layer the market umbrella skill on top of the universal core:

```text
skills/book-bestseller-studio/SKILL.md
```

When the user asks for MiroFish-style reader swarms, public-opinion simulation, niche-risk scouting, or many simulated readers, use:

```text
skills/book-swarm-panel/SKILL.md
```

Load the manifest before advancing phases:

```text
skills/book-genesis/references/pipeline/manifest.yaml
```

## Rules

- Persist important decisions to files.
- Keep `PROJECT_STATE.yaml` synchronized with reality.
- Keep `ASSUMPTIONS.md` explicit.
- Load only the prompt for the active phase.
- Do not skip Phase 4: Adversarial Audit.
- Do not run final scoring before the adversarial audit.
- Write Portuguese artifacts and prose in Portuguese when the book is in Portuguese.
- Treat legacy V4 material as historical reference unless the user asks for it.

## Agent-Specific Notes

- Claude Code can run `/book-genesis` after installing the portable suite.
- Codex can use this repo directly through `AGENTS.md` and the skill folder.
- Antigravity can use this file as the repo-level playbook.
- Kimi Code can run `/skill:book-genesis` after installing the portable suite.
- The optional local runner in `runner/cli.py` can scaffold projects and prepare phase packets, but it does not call a model or write literary output.

## Commands

- `/book-genesis`: canonical portable pipeline.
- `/book-genesis-full`: full legacy production pipeline.
- `/book-genesis-codex`: historical portable command kept for compatibility.

## Public Documentation

- `README.md`: public overview and commercial positioning.
- `docs/book-genesis-codex.md`: universal core architecture.
- `docs/runner.md`: local runner and mechanical demo.
- `docs/portability.md`: Claude Code, Codex, Antigravity, Kimi, and generic agent usage notes.
- `docs/book-gallery.md`: 10-book proof gallery.
- `SHOWCASE.md`: casebook summary.
- `examples/cases/`: case studies.
