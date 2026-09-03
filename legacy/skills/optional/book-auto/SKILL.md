---
name: book-auto
description: One-command book generation. Give it an idea, get a publish-ready book. Dispatches the book-orchestrator agent which runs the entire 17-phase pipeline autonomously, pausing only at 3 human checkpoints.
---

# /book-auto — One Command, One Book

## What This Does

You give an idea. You get a book. That's it.

This skill dispatches the `book-orchestrator` agent which runs the entire Book Genesis V4 pipeline autonomously:

1. Market research
2. Reader personas
3. Narrative foundation (characters, outline, theme)
4. Voice DNA (per-character voice specs)
5. **>>> CHECKPOINT 1: You approve the foundation <<<**
6. Entity state initialization (builds ENTITY_STATE.yaml from foundation)
7. Continuity check (outline)
8. Writing all chapters (with dialogue polish, hooks, chaos, entity state update per batch, mechanical cleanup, evaluation, quality gate — all automatic)
9. Full-manuscript evaluation
10. Revisions
11. Entity state update (tracks revisions)
12. Continuity audit (full manuscript)
13. **>>> CHECKPOINT 2: You approve the manuscript <<<**
14. Editorial package (logline, synopsis, query letter, cover brief)
15. Production prep (proofreading, formatting)
16. **>>> CHECKPOINT 3: Book delivered <<<**

## Usage

```
/book-auto [language] [idea]
```

Examples:
```
/book-auto pt-br thriller sobre ex-policial do CORE vingando a família assassinada por milícia
/book-auto en literary fiction about a quantum physicist losing her memory
/book-auto pt-br autoficção sobre burnout de dev em startup brasileira
/book-auto en dark romance between a hitman and a federal agent
```

## How To Execute

When this skill is invoked, IMMEDIATELY dispatch the book-orchestrator agent:

```
Agent tool:
  subagent_type: book-orchestrator
  prompt: "Create a book from this idea: {user's full input including language and idea}. Run the full pipeline autonomously. Only pause at the 3 checkpoints."
```

Do NOT add commentary. Do NOT ask questions. Just dispatch.

The orchestrator will run for up to 200 turns, creating the entire book pipeline autonomously. It will return to the user at the 3 checkpoints for approval.

## Project Location

All books are created at: `~/Desktop/livros/{slug}/`

The slug is auto-generated from the title (lowercase, hyphens, no accents).
