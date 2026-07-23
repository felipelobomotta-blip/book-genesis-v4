<div align="center">

# Best Seller Studio

**Turn any idea into a rigorously built and audited book. Agent-native. Quality-gated.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Runtimes](https://img.shields.io/badge/Runs%20on-Claude%20%7C%20Codex%20%7C%20Kimi-blueviolet?style=flat-square)](docs/portability.md)
[![Quality Gate](https://img.shields.io/badge/Quality%20Gate-calibrated%208.5%2B-brightgreen?style=flat-square)](#quality-gates)
[![Skills](https://img.shields.io/badge/15%20portable%20skills-orange?style=flat-square)](distribution/portable-suite.json)
[![Books Shipped](https://img.shields.io/badge/Books%20Shipped-10%2B-blue?style=flat-square)](#proof)

https://github.com/felipelobomotta-blip/book-genesis-v4/raw/master/video-demo/out/demo.mp4

</div>

---

You have an idea. Maybe it came to you in the shower. Maybe it's been in a note on your phone for two years. Maybe it's one sentence you've never finished.

Type it in. That's it. The system takes over.

Portable specialist roles research the genre, forge the premise, build the manuscript, audit it adversarially, revise weak dimensions, score with isolated evaluators, and package the result.

Important decisions, assumptions, gates, and blockers stay visible in project files. Runtime handles model execution; Book Genesis handles editorial protocol.

**No writing experience required. No prompt engineering. No creative blocks.**

---

## Quick start

**Step 1 — Choose a runtime**

Use Claude Code, Codex, Kimi Code, or another file-aware agent. Install Python 3.10+ for the deterministic runner and installer.

**Step 2 — Clone and verify**

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-v4.git
cd book-genesis-v4
python runner/cli.py verify-suite
```

**Step 3 — Install the same portable suite into your runtime**

```bash
# macOS / Linux
bash install.sh claude   # or: codex, kimi, shared
```

```powershell
# Windows (PowerShell)
.\install.ps1 -Target codex   # or: claude, kimi, shared
```

The installer performs a conflict check. It never overwrites a modified skill unless you pass `--force` or `-Force`; forced replacements are backed up first.

**Step 4 — Give it an idea**

Invoke `/book-genesis` in Claude Code, use `/skill:book-genesis` in Kimi Code, or ask Codex to use the installed `book-genesis` skill. Then type:

```
I have an idea for a book: [your idea here]
```

The orchestrator creates durable project files and dispatches specialist roles through runtime-native subagents when available.

---

## What happens when you run it

Default portable sequence: Intake → Foundation → Architecture → Drafting → Adversarial Audit → Literary Barrier Revision Loop → Final Score → Editorial Package.

The diagram below documents the legacy V4 multi-agent route retained for compatibility:

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

## Quality gates

This is what makes Best Seller Studio different from just asking ChatGPT to write a book.

Default portable profile enforces:

1. Product and commercial-length contract before drafting.
2. Mandatory adversarial audit before scoring.
3. Literary Barrier revision with blind evaluator reports and recorded independence grade.
4. Final floor score, weighted score, evidence, and package gates.

The detailed chapter-by-chapter gates below document legacy V4 behavior. Install them only with `--include-legacy`.

### Legacy Gate 1 — Premise must score 8.0+ before a word is written

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

### Legacy Gate 2 — Every chapter scores 8.5+ before the manuscript advances

The evaluator that scores your chapters is a **separate agent that never wrote any of them**. No self-grading.

It runs:
- 7-dimension Genesis Score (floor is the score)
- 20-pattern anti-AI scan (clichés, hedged language, fake profundity, on-the-nose dialogue...)
- Simulation of 4 reader types reading independently
- "Would you remember this chapter tomorrow?" test

Chapters between the hard floor and the 8.5 target enter the **Polish Loop**: the evaluator writes a surgical work order naming the exact failing dimensions, and the editor fixes only those. The rest is untouched.

Anti-inflation protection: each cycle can only add +0.5 maximum. You can't shortcut the gate.

### Legacy Gate 3 — All chapters 8.5+ AND CVI-Launch ≥ 9.0

CVI-Launch is our best-seller potential proxy. 9.0 is "breakout potential, Gone Girl tier" — the manuscript has a word-of-mouth mechanism built in structurally, not just good prose.

The manuscript only reaches packaging when both gates pass.

---

## Portable roles and legacy Claude agents

Portable profile owns specialist behavior through [`agent-registry.yaml`](skills/book-bestseller-studio/references/agent-registry.yaml) and fresh agent packets. Table below documents native Claude V4 profiles retained for compatibility.

| Agent | Role |
|---|---|
| `book-orchestrator` | Pipeline manager. Dispatches everyone, enforces all gates, routes checkpoints to you. |
| `book-researcher` | Market reader. Finds what readers actually hate about existing books in your genre — that gap is your premise's foundation. |
| `book-architect` | Premise forger + structural architect. Dispatched 3 times: forge mode → foundation → voice DNA. |
| `book-writer` | Chapter writer. Has the 8.5 bar as design targets, not afterthoughts. |
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

## Inference and cost

Book Genesis does not host a model and does not call a provider API. The selected runtime owns inference, authentication, quotas, and billing.

- Claude Code uses the user's Claude account or configured provider.
- Codex uses the user's Codex/OpenAI environment.
- Kimi Code uses the user's Kimi membership or configured provider.
- Local or shared Agent Skills directories remain possible through the `shared` target.

No central Book Genesis API bill exists. Runtime limits still apply.

---

## Requirements

- Python 3.10+
- Claude Code, Codex, Kimi Code, or another agent that can read and write project files
- enough runtime quota and context for long-form work

---

## Honest caveats

**What the system guarantees:** The workflow does not approve a manuscript unless required artifacts and documented quality gates pass. Failures and degraded evaluator independence are surfaced explicitly. The mechanical runner validates contracts, not literary truth.

**What the system does not guarantee:** A literal bestseller. Cover design, marketing, timing, and luck are outside the manuscript and outside this system. The quality gate attacks the word-of-mouth mechanism (retellability + CVI) because that's the lever we actually control.

**About the 8.5 score:** It is an internal editorial ruler, not certified external measurement. Final reports record evaluator isolation Grade A, B, or C; Grade C cannot support an independent-quality claim.

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

## Community

- Questions? Start a [Discussion](https://github.com/felipelobomotta-blip/book-genesis-v4/discussions)
- Found a bug? [Open an issue](https://github.com/felipelobomotta-blip/book-genesis-v4/issues)
- Want to contribute? Check [`good first issue`](https://github.com/felipelobomotta-blip/book-genesis-v4/labels/good%20first%20issue) and [`CONTRIBUTING.md`](CONTRIBUTING.md)
- First-time contributors welcome — happy to pair on the first PR

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
