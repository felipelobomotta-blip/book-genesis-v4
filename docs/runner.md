# Local Runner

Book Genesis is still a markdown-first, agent-run workflow. The local runner exists to make the workflow reproducible: it scaffolds the project tree, prepares the active phase packet, validates required outputs, and advances gates.

It does not call an LLM and it does not claim literary quality. Agents still write, audit, score, and package the manuscript using the active phase prompt.

## Commands

```bash
python runner/cli.py init my-book --idea "a detective audits a haunted manuscript"
python runner/cli.py status my-book
python runner/cli.py prepare-phase my-book
python runner/cli.py advance-phase my-book
python runner/cli.py validate my-book
python runner/cli.py prepare-swarm my-book --mode hybrid --slug launch-reaction
python runner/cli.py prepare-agent-packet my-book prose_writer
```

`prepare-phase` writes:

```text
my-book/work/current-phase.md
```

That file contains the phase label, gate, required outputs, and the full active phase prompt from `skills/book-genesis/references/`.

`prepare-swarm` writes:

```text
my-book/evaluations/book-swarm/<date>-launch-reaction/
```

That folder contains the Book Swarm Panel contract: persona roster, sample map, cohort reports, interviews, public-opinion report, risk heatmap, revision tickets, score calibration, summary, and an optional `mirofish-requirement.md` bridge file for external MiroFish runs.

`prepare-agent-packet` writes:

```text
my-book/work/agent-packets/prose_writer.md
```

That file contains the specialist mission, missing inputs, required outputs, gates, score floor, and relevant skill prompt from `skills/book-bestseller-studio/references/agent-registry.yaml`.

## Mechanical Demo

Use this before launch, CI, or a demo recording:

```bash
python runner/cli.py demo .tmp-book-genesis-demo
python runner/cli.py status .tmp-book-genesis-demo
python runner/cli.py validate .tmp-book-genesis-demo
```

The demo fills deterministic placeholder outputs and advances all gates. It proves the file contract and phase mechanics, not manuscript quality.

## What The Runner Guarantees

- `PROJECT_STATE.yaml` exists and tracks the current phase.
- `ASSUMPTIONS.md`, `RUN_REPORT.md`, `artifacts/`, `manuscript/chapters/`, `evaluations/`, and `delivery/` exist.
- Phase outputs must be replaced before `advance-phase` succeeds.
- Phase 4 cannot be skipped because phase order is read from the manifest.
- Book-swarm runs use a durable folder contract before clean-room simulation or external MiroFish import.
- Specialist agents use packet files so worldbuilding, writing, pacing, continuity, scoring, packaging, and launch work have explicit ownership.

## What The Runner Does Not Do

- It does not call Claude, Codex, Kimi, OpenAI, or any other model.
- It does not generate real prose.
- It does not score a manuscript by itself.
- It does not run MiroFish. It prepares import/export files for an external MiroFish run when available.
- It does not build EPUB/PDF files.

Those steps belong to the agent executing the phase prompt.
