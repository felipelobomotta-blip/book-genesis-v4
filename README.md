<div align="center">

# Book Genesis

**Turn an idea into a manuscript a stranger would keep reading. Runner-driven. Blind-judged.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Runs on](https://img.shields.io/badge/Runs%20on-Claude%20Code%20%2B%20Codex%20CLI-blueviolet?style=flat-square)](#quick-start)
[![Gate](https://img.shields.io/badge/Gate-blind%20reader%2C%20not%20a%20score-brightgreen?style=flat-square)](#the-gate)
[![Templates](https://img.shields.io/badge/10%20agent%20templates-orange?style=flat-square)](#the-agent-templates)
[![Projects](https://img.shields.io/badge/Book%20projects-10%2B-blue?style=flat-square)](SHOWCASE.md)

https://github.com/felipelobomotta-blip/book-genesis-v4/raw/master/video-demo/out/demo.mp4

</div>

---

You have an idea. Maybe one sentence you never finished.

Type it in. A small Python runner takes it from there: it builds the book's foundation and outline, then writes the manuscript one chapter at a time. Every chapter is read **blind** by a model from a different family than the one that wrote it, someone who has never seen the outline, and who answers the only question that matters: *would I turn the page?* If not, an editor fixes exactly what the reader flagged, and the reader compares the new draft against the old one.

Chapter 1 is read by a **panel** of blind readers before the book goes on: different personas (the genre buyer, the hostile reader, the airport reader) on different model families when your machine has them. No human is required at any point. If you want to read chapter 1 yourself before chapter 2 exists, add `--human`.

**No writing experience required. No prompt engineering. No API keys. No human in the loop unless you ask for one.**

---

## Quick start

**Step 1 — Requirements**

- Python 3.10 or newer. No other packages.
- A way to run models, any one of these: an API key for OpenRouter, DeepSeek, Anthropic, OpenAI, Groq or Together; a local server (Ollama, LM Studio); [Claude Code](https://claude.ai/code) (`claude`) or the [Codex CLI](https://github.com/openai/codex) (`codex`) already logged in; any other command-line tool declared in `runner/config/adapters.yaml`; or nothing at all with `--manual`, which writes every prompt to a file and waits for you to paste the reply from any chat. Two families is better: the writer and the judge then disagree in useful ways. One family works, with a `single family` warning in the run report.

**Step 2 — Install the command and choose your providers**

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-v4
cd book-genesis-v4
pip install -e .                 # gives you the `book-genesis` command; nothing else is installed
book-genesis setup               # providers, keys (typed hidden), models. Once.
book-genesis doctor              # shows what will run where, and whether every key is set
```

`setup` writes `~/.book-genesis/config.yaml` and nothing else. A key is stored there, or read from an environment variable if you leave the prompt blank; it never enters the repository, a prompt, or a log. Skip the install if you prefer: `python -m runner ...` and `python runner/cli.py ...` are the same program.

**Step 3 — Give it an idea**

```bash
book-genesis new
```

It asks for the idea and the language, then runs everything and prints each step as it happens: intake, foundation, architecture, every chapter (chapter 1 through the reader panel), the adversarial audit, the diagnostic score, the editorial package. `book-genesis resume my-book` continues a project from wherever it stopped. The lower-level commands (`run-phase`, `book`, `chapter`, `judge`, `panel`) are still there for when you want one step at a time.

Every artifact is a Markdown file in the project folder. Nothing happens in chat; everything happens on disk. When it is done, read `RUN_REPORT.md`: every chapter, every verdict, every warning, in the order they happened.

Prefer to read chapter 1 yourself before the rest is written? `book-genesis new --human` pauses there until you run `book-genesis approve <folder> chapter-01`.

---

## What happens when you run it

```
idea ─► Phase 0 intake ─► Phase 1 foundation ─► Phase 2 architecture (outline with ## Chapter N sections)
                                                          │
            ┌─────────────────────────────────────────────┘
            ▼
   for each chapter:
     brief  = this chapter's outline section + story engine + characters + last page of the previous chapter
     writer (claude opus)      writes from the brief and nothing else
     disruptor (claude sonnet) breaks predictability          [fiction only]
     judge (codex, blind)      reads prose only: turn the page? where did attention stop? what stays?
        ├─ yes ──────────────────────────────► accepted, saved to manuscript/chapters/
        └─ no ─► editor (modes = judge flags) ─► judge compares new draft vs previous ─► ...
                 (at most N cycles per genre; a worse draft is discarded, not accepted)
     chapter 1 only: the judge is a PANEL of three blind readers (different personas and,
                     when installed, different families); majority decides
                     (`--human` pauses here for you instead)
```

Drafts and verdicts are kept: `manuscript/drafts/chapter-NN/draft-K.md`, `evaluations/chapter-NN-judge-K.md`.

---

## The gate

There is no internal score that decides whether a chapter passes. Earlier versions of this project graded their own prose on a 10-point rubric and required 8.5; the evaluator's own rules said any score above 8.0 needed external validation, and no human ever read the text inside the loop. The review that found this is in [`docs/REVISAO-CONSISTENCIA-2026-09.md`](docs/REVISAO-CONSISTENCIA-2026-09.md); the decisions that replaced it are in [ADR 0001](docs/adr/0001-runner-orquestra-juiz-cego.md).

What decides now:

1. **A blind reader.** `agents/book-judge.md` receives the chapter's prose and the last 300 words of the previous chapter. Not the outline, not the foundation, not the writer's notes. It answers `turn_page`, `stopped_at` (the exact sentence), `remember` (what it would still have tomorrow) and flags (`hook`, `dialogue`, `pacing`, `ai_pattern`, `exposition`, `voice`, `continuity`).
2. **Comparison, not grades.** After an edit the judge sees both drafts and says `better`, `worse` or `same`. A model is unreliable at "8.3 vs 8.6" and reasonable at "A vs B". A worse draft is thrown away and the next edit starts from the best one.
3. **A different family judges.** You choose the providers in `setup` (the repository default is writer on `claude`, judge on `codex`). A system grading its own prose has maximum bias; two families disagree in useful ways. When only one family is available, the judge takes a different model and the run carries a `single family` warning; `doctor` shows the plan before you spend anything.
4. **A panel reads chapter 1.** Three blind readers with different personas (the genre buyer, the hostile reader, the airport reader), on different families when available. Majority decides; a flag needs two votes. If the voice is wrong, the book finds out after one chapter, not twenty. `panel my-book 7` runs the same panel on any chapter. With `--human` the runner pauses after chapter 1 for you instead.
5. **The old rubric is a diagnostic.** `agents/book-evaluator.md` (7 dimensions, anti-AI scan) still exists to tell the editor *what* to fix. It does not approve anything.

Judge any chapter you already have, from any source:

```bash
python runner/cli.py judge path/to/chapter.md --genre "literary thriller" --adapter codex
python runner/cli.py judge path/to/chapter.md --genre "literary thriller" --adapter claude --model sonnet
python runner/cli.py panel my-book 1        # the whole panel on a chapter the runner wrote
```

---

## The agent templates

Templates are plain Markdown in `agents/`. The runner strips the frontmatter, injects the brief or the chapter, and appends an output contract. Models never get tools; the runner does all file I/O.

| Template | Role in the runner |
|---|---|
| `book-judge` | Blind reader. Prose in, reader answers out. Never sees the plan, never gives a number. |
| `book-writer` | Writes one chapter from the brief. Does not know the rubric. |
| `book-disruptor` | Breaks AI predictability between writer and judge (fiction genres). |
| `book-editor` | Surgical revision in modes (`hook`, `dialogue`, `pacing`, `ai_pattern`, `exposition`, `voice`, `continuity`), run only when the judge flags them. |
| `book-architect` | Phases 0–2 through the runner: brief, market map, story engine, characters, theme, emotional curve, outline, opening strategy. |
| `book-researcher` | Market research and reader personas (available as a Claude Code subagent; not yet wired into the runner). |
| `book-evaluator` | 7-dimension rubric and 20-pattern anti-AI scan, as a diagnostic for the editor. |
| `entity-tracker` | Canonical state of characters, places, objects, and who knows what since when. |
| `continuity-guardian` | Timeline, knowledge and plot-thread audit on the outline and the full manuscript. |
| `book-packager` | Logline, synopses, query letter, cover brief, proofreading passes. |

Constants live in one place: `runner/config/genre-profiles.yaml` (chapter length, dialogue share, revision cycles, whether the disruptor runs) and `runner/config/models.yaml` (adapter and model per role). Prompts reference them; they never restate numbers.

---

## Real examples

Projects run through earlier versions of this pipeline (artifacts, not full manuscripts, are public; see [`SHOWCASE.md`](SHOWCASE.md)):

> *"A memoir of asking a mental-health system for help and getting 'protocol not found' back"*
→ **Protocolo Não Encontrado** — memoir, PT-BR; score sheet, outline and synopses in `examples/`

> *"A reclusive programmer's AI finds the same pattern hidden in every spiritual tradition, then the AI is destroyed and the pattern turns out to live in people"*
→ **Age of Aquarius** — literary thriller, EN; outline and synopses in `examples/`

The current runner has been exercised end to end on a Portuguese-language thriller; the run log and timings are in [`docs/runner.md`](docs/runner.md).

---

## Cost

You pay your own providers directly: an API key you connected in `setup`, or the subscriptions behind the `claude` and `codex` command-line tools. Nothing in this repository stores a key, and the runner never sends anything anywhere except to the provider you chose.

Per chapter: three model calls minimum (writer, disruptor, judge) plus two per revision cycle (editor, judge). Phases 0–2: one call each. The judge calls are short; the writer calls are the expensive ones.

---

## Honest caveats

**What the runner guarantees:** every chapter was read blind by a model that did not write it and had not seen the plan; chapter 1 was read by three blind readers before chapter 2 was written; every draft, every verdict and every warning is on disk; no chapter is silently accepted below the readers' bar.

**What it does not guarantee:** a bestseller, or even a good book. A panel of model readers is not a room of human readers. The signals here are cheaper and less biased than self-grading, and they are still not external validation; this README will never say "validated by readers" about a model panel. A blind reading test with real people remains the only thing that turns the output into a claim, and it lives outside the runner as an optional study.

**What is not built:** EPUB/PDF export (the packager writes specs and copy, not files), and the market-research phase inside the runner.

---

## Legacy

Three earlier pipelines, four gate definitions and three scoring rubrics used to coexist in this repository. They were moved, not deleted, to [`legacy/`](legacy/README.md), with git history intact. Nothing in `legacy/` is on the canonical path.

---

## About

Built by [Felipe Lobo](https://github.com/felipelobomotta-blip) — developer from Brazil.

Six months of iteration, 10+ book projects, one honest review. MIT licensed.

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
| [ADR 0001](docs/adr/0001-runner-orquestra-juiz-cego.md) | Why the runner orchestrates and the judge is blind (PT-BR) |
| [ADR 0002](docs/adr/0002-autonomia-painel-adaptadores.md) | No human in the loop by default; the reader panel; running on whatever is installed (PT-BR) |
| [ADR 0003](docs/adr/0003-cli-proprio-provedores-por-api.md) | The `book-genesis` command, `setup`, your own API providers and keys (PT-BR) |
| [Runner](docs/runner.md) | Commands, exit codes, configuration, what it does not do |
| [Consistency review](docs/REVISAO-CONSISTENCIA-2026-09.md) | The line-by-line review that led here (PT-BR) |
| [Phase prompts](docs/book-genesis-codex.md) | The phase prompts the runner feeds to the architect role |
| [Portability](docs/portability.md) | Notes on other agents (partly historical) |
| [Showcase](SHOWCASE.md) | Case breakdowns of earlier projects |
| [Contributing](CONTRIBUTING.md) | How to contribute |
| [Security](SECURITY.md) | Security policy |
| [Code of Conduct](CODE_OF_CONDUCT.md) | Community standards |
| [Changelog](CHANGELOG.md) | Version history |
| [Release Checklist](RELEASE_CHECKLIST.md) | Release process |
| [Coverage Plan](COVERAGE_PLAN.md) | Test coverage roadmap |

---

## 🤝 Contribute

Book Genesis wouldn't be what it is without contributions from developers like you. Whether it's a template change, a genre profile, a bug fix, or a better judge prompt — every contribution matters.

Please read our [Contributing Guide](CONTRIBUTING.md) to get started. We also welcome your feedback — share your experience by opening a [Discussion](https://github.com/felipelobomotta-blip/book-genesis-v4/discussions).

A huge Thank You 🙏 to everyone who contributes!

[![Contributors](https://contrib.rocks/image?repo=felipelobomotta-blip/book-genesis-v4)](https://github.com/felipelobomotta-blip/book-genesis-v4/graphs/contributors)
