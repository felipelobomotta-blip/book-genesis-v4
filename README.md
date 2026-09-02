<div align="center">

# Best Seller Studio

**Turn any idea into a publication-ready book. Fully autonomous. Quality-gated.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Claude Code](https://img.shields.io/badge/Runs%20on-Claude%20Code-blueviolet?style=flat-square)](https://claude.ai/code)
[![Quality Gate](https://img.shields.io/badge/Quality%20Gate-8.5%2F10%20enforced-brightgreen?style=flat-square)](#the-quality-gates)
[![Agents](https://img.shields.io/badge/11%20specialized%20agents-orange?style=flat-square)](#the-agents)
[![Books Shipped](https://img.shields.io/badge/Books%20Shipped-10%2B-blue?style=flat-square)](#proof)

https://github.com/felipelobomotta-blip/book-genesis-v4/raw/master/video-demo/out/demo.mp4

</div>

---

You have an idea. Maybe it came to you in the shower. Maybe it's been in a note on your phone for two years. Maybe it's one sentence you've never finished.

Type it in. That's it. The system takes over.

11 AI agents run in sequence — researching your genre, forging a premise with a structural irony engine, writing every chapter, scoring each one independently, revising anything below the quality gate, and packaging the result for publication.

You approve 3 times. Everything else is automatic.

**No writing experience required. No prompt engineering. No creative blocks.**

---

## Quick start

**Step 1 — Get Claude Code**

Download it free at [claude.ai/code](https://claude.ai/code). It runs in your terminal.

**Step 2 — Install the agents**

```bash
# macOS / Linux
git clone https://github.com/felipelobomotta-blip/book-genesis-v4
cd book-genesis-v4 && ./install.sh
```

```powershell
# Windows (PowerShell)
git clone https://github.com/felipelobomotta-blip/book-genesis-v4
cd book-genesis-v4; .\install.ps1
```

The installer copies all 11 pipeline agents, the skills, and the bestseller knowledge base, then verifies every agent the orchestrator dispatches actually resolves. If it prints `Pipeline verified`, you're ready. Copying `agents/*.md` by hand is not enough — the pipeline also reads `~/.claude/knowledge/`.

**Step 3 — Give it an idea**

Open Claude Code and type:

```
I have an idea for a book: [your idea here]
```

That's it. The `book-orchestrator` agent takes over and runs the whole pipeline.

---

## What happens when you run it

Here's the exact sequence:

```
┌─────────────────────────────────────────────────────┐
│  YOUR IDEA                                          │
│  "what if a journalist covering the 2026 World Cup  │
│   discovers an alien contact cover-up?"             │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 1 — Market Research                          │
│  • Finds 5–10 comparable published books            │
│  • Reads what readers hate about them (1-star       │
│    reviews are gold — that's your gap)              │
│  • Maps what's missing in the market                │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 1.5 — Premise Forge  ⬅ the secret weapon    │
│  • Your raw idea becomes 5 structural variants      │
│  • Each is scored on 6 dimensions                   │
│  • The one with the strongest irony engine wins     │
│  • Floor required: 8.0/10                           │
│  • Rule: your idea is ELEVATED, never replaced      │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 2 — Foundation & Outline                     │
│  • Character profiles (with contradictions baked in)│
│  • Full chapter map                                 │
│  • Every story beat intentionally subverted         │
│  • Voice DNA established                            │
└──────────────────────┬──────────────────────────────┘
                       │
             ╔═════════╧══════════╗
             ║   CHECKPOINT 1     ║  ← YOU APPROVE
             ║  "here's what we   ║
             ║   built and why"   ║
             ╚═════════╤══════════╝
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 3 — Chapter Loop (repeats for every chapter) │
│                                                     │
│  write → polish dialogue → sharpen hooks →          │
│  inject chaos → score independently                 │
│                                                     │
│  ✓ Score ≥ 8.5? → next chapter                     │
│  ↺ Score 7.0–8.5? → polish loop (max 5×)           │
│  ✗ Score < 7.0? → escalate to full revision        │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  PHASES 4 & 5 — Full Review & Revision              │
│  • Evaluates entire manuscript as one unit          │
│  • Re-attacks any weak chapter                      │
│  • Target: CVI-Launch ≥ 9.0                        │
│    (CVI = Commercial Viability Index — our          │
│     "Gone Girl tier" bestseller proxy)              │
└──────────────────────┬──────────────────────────────┘
                       │
             ╔═════════╧══════════╗
             ║   CHECKPOINT 2     ║  ← YOU APPROVE
             ║  "every chapter    ║
             ║   score shown"     ║
             ╚═════════╤══════════╝
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  PHASE 6 — Delivery Package                         │
│  • Logline & back-cover blurb                       │
│  • Query letter (ready to send to agents)           │
│  • Formatted ebook + print files                    │
└──────────────────────┬──────────────────────────────┘
                       │
             ╔═════════╧══════════╗
             ║   CHECKPOINT 3     ║  ← YOU APPROVE
             ║   your book        ║
             ╚════════════════════╝
```

---

## The quality gates

This is what makes Best Seller Studio different from just asking ChatGPT to write a book.

### Gate 1 — Premise must score 8.0+ before a word is written

Every bestseller has the same structural DNA: a contradiction that generates conflict automatically. Gone Girl works because the "perfect marriage" premise immediately contradicts itself. Breaking Bad works because "chemistry teacher becomes drug lord" is a contradiction that escalates by its own logic.

The Premise Forge scores your idea across 6 dimensions:

| Dimension | What it tests |
|---|---|
| **Hook** | Does the one-sentence pitch make someone say "oh damn"? |
| **Irony engine** | Is there a structural contradiction that generates conflict by itself? A story without one maxes at 5.0. |
| **Native escalation** | Can you name 3 escalation steps that follow from the premise — not from external events? |
| **The question** | Is there one central question that only the last page can answer? |
| **Gap fit** | Is this meaningfully different from every comparable title on the market? |
| **Retellability** | Can someone retell this tomorrow without notes? This is the word-of-mouth mechanism — and the bestseller mechanism. |

**The floor IS the score.** A premise that scores 9/9/9/9/9/4 is a **4**, not an 8.2 average.

Your raw idea is always Variant 1 (scored honestly as a baseline). If it already hits 8.0, it wins — the system doesn't forge for the sake of forging. Variants 2–5 are alternatives using different irony engines.

### Gate 2 — Every chapter scores 8.5+ before the manuscript advances

The evaluator that scores your chapters is a **separate agent that never wrote any of them**. No self-grading.

It runs:
- 7-dimension Genesis Score (floor is the score)
- 20-pattern anti-AI scan (clichés, hedged language, fake profundity, on-the-nose dialogue...)
- Simulation of 4 reader types reading independently
- "Would you remember this chapter tomorrow?" test

Chapters between the hard floor and the 8.5 target enter the **Polish Loop**: the evaluator writes a surgical work order naming the exact failing dimensions, and the editor fixes only those. The rest is untouched.

Anti-inflation protection: each cycle can only add +0.5 maximum. You can't shortcut the gate.

### Gate 3 — All chapters 8.5+ AND CVI-Launch ≥ 9.0

CVI-Launch is our best-seller potential proxy. 9.0 is "breakout potential, Gone Girl tier" — the manuscript has a word-of-mouth mechanism built in structurally, not just good prose.

The manuscript only reaches packaging when both gates pass.

---

## The agents

| Agent | Role |
|---|---|
| `book-orchestrator` | Pipeline manager. Dispatches everyone, enforces all gates, routes checkpoints to you. |
| `book-researcher` | Market reader. Finds what readers actually hate about existing books in your genre — that gap is your premise's foundation. |
| `book-architect` | Premise forger + structural architect. Dispatched 3 times: forge mode → foundation → voice DNA. |
| `entity-tracker` | Canonical state keeper. Maintains `ENTITY_STATE.yaml` — every character, location, object, timeline event, plot thread, and who knows what when. |
| `continuity-guardian` | Continuity auditor. Runs once on the outline and once on the full manuscript. Flags timeline, knowledge, and plot-thread violations with severity — never rewrites. |
| `book-writer` | Chapter writer. Has the 8.5 bar as design targets, not afterthoughts. |
| `dialogue-polish` | Dialogue-only pass. Runs the cover-the-name test until every character is identifiable by voice alone. Never touches narrative prose. |
| `hook-craft` | Chapter openings and endings. Scores the first and last lines, rewrites only those 3–5 sentences when they fall below the genre floor. |
| `book-evaluator` | Independent critic. Never writes — only judges. Runs the full 4-reader simulation and anti-AI scan. |
| `book-editor` | Surgical editor. Given a work order from the evaluator, touches only the failing dimensions. Never disrupts what's working. |
| `book-disruptor` | Chaos agent. Runs between writer and evaluator to break AI predictability — injects unexpected details and authentic human noise. |
| `book-packager` | Delivery. Logline, synopsis, query letter, formatted files. |

All agents are plain markdown files in `agents/`. Read them directly to see exactly what each agent does.

---

## Real examples

These ideas were run through the pipeline:

> *"A memoir-style essay about growing up between two cultures, not belonging to either"*
→ **Protocolo Não Encontrado** — strong external response on early readers

> *"What if the world's top chess players are actually running a secret intelligence network"*
→ **Age of Aquarius** — high internal Genesis Score after iterative evaluation

> *"A journalist covering the 2026 World Cup discovers an alien contact cover-up"*
→ **THE LAST COVENANT** — currently in production, first V4.2 benchmark run

---

## Cost

Using **Claude Sonnet 4.6** (recommended):

| What | Cost |
|---|---|
| Full book, 20 chapters | ~$20–30 |
| Per chapter (avg 1.5 polish cycles) | ~$1.00–1.50 |
| Setup phases (research + forge + foundation) | ~$1.50 |

Claude Code runs on your Anthropic account via OAuth — no separate API key needed.

---

## Requirements

- [Claude Code](https://claude.ai/code) — log in with your Anthropic account (OAuth). No API key needed.
- ~30 minutes unattended runtime per book (the pipeline runs autonomously)

---

## Honest caveats

**What the system guarantees:** The manuscript scores 8.5+ on the internal quality gate before leaving the pipeline. No chapter ships silently below target. Every gate failure is surfaced to you explicitly.

**What the system does not guarantee:** A literal bestseller. Cover design, marketing, timing, and luck are outside the manuscript and outside this system. The quality gate attacks the word-of-mouth mechanism (retellability + CVI) because that's the lever we actually control.

**About the 8.5 score:** It's an internally-calibrated ruler based on comps that hit bestseller lists — not a certified external measurement. It's the best proxy we can build before a real audience reads the book.

---

## Live benchmark

**THE LAST COVENANT** is the first book running the complete V4.2 pipeline (premise forge → chapter gate → exit gate).

Chapters 1–9 in Phase 5 revision. Chapters 10–14 being written through the new gate. When it's done, every chapter's Genesis Score, evaluator work orders, and CVI-Launch will be published in [`SHOWCASE.md`](SHOWCASE.md) — the first real-world V4.2 benchmark.

---

## About

Built by [Felipe Lobo](https://github.com/felipelobomotta-blip) — developer from Brazil.

6 months of iteration. 10+ books shipped. MIT licensed.

[X / Twitter](https://x.com/FelipeL72767971) · [LinkedIn](https://www.linkedin.com/in/felipeloboai/) · [GitHub](https://github.com/felipelobomotta-blip)


## Community

- Questions? Open a [Discussion](https://github.com/felipelobomotta-blip/book-genesis-v4/discussions)
- Found a bug? [Open an issue](https://github.com/felipelobomotta-blip/book-genesis-v4/issues)
- Want to contribute? Check [`good first issue`](https://github.com/felipelobomotta-blip/book-genesis-v4/issues?q=label%3A%22good+first+issue%22) and [`CONTRIBUTING.md`](CONTRIBUTING.md)
- First-time contributors welcome — happy to pair on the first PR

[![Contributors](https://contrib.rocks/image?repo=felipelobomotta-blip/book-genesis-v4)](https://github.com/felipelobomotta-blip/book-genesis-v4/graphs/contributors)

[![Star History Chart](https://api.star-history.com/svg?repos=felipelobomotta-blip/book-genesis-v4&type=Date)](https://star-history.com/#felipelobomotta-blip/book-genesis-v4&Date)

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/book-genesis-codex.md) | Multi-agent pipeline overview |
| [Portability](docs/portability.md) | Agent-agnostic design notes |
| [Showcase](SHOWCASE.md) | 10+ books shipped, case breakdowns |
| [Contributing](CONTRIBUTING.md) | How to contribute |
| [Security](SECURITY.md) | Security policy |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards |
| [Changelog](CHANGELOG.md) | Version history |
| [Release Checklist](RELEASE_CHECKLIST.md) | Release process |
| [Coverage Plan](COVERAGE_PLAN.md) | Test coverage roadmap |


---

## 🤝 Contribute

Book Genesis wouldn't be what it is without contributions from developers like you. Whether it's a new agent prompt, a genre calibration, a bug fix, or a new evaluation dimension — every contribution matters.

Please read our [Contributing Guide](CONTRIBUTING.md) to get started. We also welcome your feedback — share your experience by opening a [Discussion](https://github.com/felipelobomotta-blip/book-genesis-v4/discussions).

A huge Thank You 🙏 to everyone who contributes!

[![Contributors](https://contrib.rocks/image?repo=felipelobomotta-blip/book-genesis-v4)](https://github.com/felipelobomotta-blip/book-genesis-v4/graphs/contributors)

