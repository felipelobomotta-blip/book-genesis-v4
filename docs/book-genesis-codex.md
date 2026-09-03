# Universal Book Genesis Core

> **2026-09-02 (ADR 0001):** the phase prompts in this folder are now executed by the runner (`python runner/cli.py run-phase`), not by an agent holding tools. Drafting and the quality gate are described in [`runner.md`](runner.md) and [ADR 0001](adr/0001-runner-orquestra-juiz-cego.md). The 10-dimension Genesis Score below is kept as a diagnostic, not as the gate. Passages about `/book-genesis-codex` as a Claude Code command or about V4/V5 defaults are historical.

The Universal Book Genesis Core is the portable, reduced-pressure version of Book Genesis. It works in Claude Code, Codex, Antigravity, Kimi, and other agents that can read files and maintain project state.

The implementation lives at:

```text
skills/book-genesis-codex/
  SKILL.md
  agents/openai.yaml
  references/
    pipeline/manifest.yaml
    pipeline/phases.md
    prompts/
    scoring/genesis-score-codex.md
    legacy-v4-book-genesis.md
```

The optional local runner lives at:

```text
runner/
  cli.py
  filesystem.py
tests/
  test_runner.py
```

The runner scaffolds projects, runs each phase through a model adapter (`claude` or `codex` CLI), validates required files, advances gates, writes and judges chapters, and still prepares the optional Book Swarm Panel/MiroFish bridge folders and the Book Bestseller Studio agent packets. See `runner.md`; the runner modules are `cli.py`, `phases.py`, `brief.py`, `chapter.py`, `book.py`, `judge.py`, `adapters.py`, `constants.py`, `roles.py`.

The folder name `book-genesis-codex` is historical and preserved so existing commands and installs keep working. The product positioning is broader: **Book Genesis is a universal book pipeline for AI agents.**

## Why It Exists

V4/V5 were powerful but heavy. The system grew into 17 phases, 19 skills, multiple mid-draft gates, quality loops, chaos passes, mechanical preprocessors, and entity tracking. That helped catch problems, but it also trained the writer to satisfy the evaluator while drafting.

The universal core makes a different bet:

- persist decisions to files
- keep the active phase small
- draft before judging
- audit structurally before scoring
- score with evidence, not vibes
- package only after the audit and score are clear
- make the workflow portable across agents instead of tied to one tool

## Runtime Targets

| Agent | Status | Notes |
|-------|--------|-------|
| Claude Code | Native skill | Install the full folder and run `/book-genesis-codex` |
| Codex | Native repo workflow | Use `AGENTS.md` or the skill folder directly |
| Antigravity | Agent playbook | Open the repo and follow `AGENTS.md` |
| Kimi | File-backed workflow | Provide the skill folder or paste the active phase contract |
| Generic coding agents | Portable | Must read files, write artifacts, and update state |

## Canonical Pipeline

| Phase | Name | Output |
|-------|------|--------|
| 0 | Intake | `ASSUMPTIONS.md`, brief, market map, story engine |
| 1 | Foundation | characters, theme, emotional curve |
| 2 | Architecture | outline, tension map, opening strategy |
| 3 | Drafting | chapter files in `manuscript/chapters/` |
| 4 | Adversarial Audit | structural criticism before score |
| 5 | Final Score | Genesis Score report |
| 6 | Editorial Package | logline, blurb, synopsis, cover brief, query strategy |

Default project tree:

```text
PROJECT_STATE.yaml
ASSUMPTIONS.md
artifacts/
manuscript/
  chapters/
evaluations/
delivery/
```

## Genesis Score

The current score uses 10 dimensions:

1. Originality
2. Theme
3. Characters
4. Prose
5. Pacing
6. Emotion
7. Coherence
8. Market
9. Voice
10. Opening

Approval requires:

- Floor Score >= 8.5
- Weighted Average >= 9.0
- no dimension below 8.0
- evidence for every dimension
- adversarial audit not marked `MAJOR REWRITE`

The floor principle remains the most important rule: the manuscript is only as strong as its weakest major dimension.

## What Changed From V4/V5

| Earlier system | Universal core |
|----------------|----------------|
| Many active skills at once | One active phase prompt at a time |
| `STATE.yaml` plus specialized state files | `PROJECT_STATE.yaml` plus explicit assumptions |
| Mid-draft scoring pressure | Draft first, audit and score after |
| Chaos and mechanical passes inside drafting | Structural variety during drafting, repair after |
| Claude Code first | Portable package for Claude Code, Codex, Antigravity, Kimi, and agent IDEs |
| V4 legacy as default | V4 legacy kept as reference only |

## How It Has Behaved

The portable core has been most reliable when treated as a project-file workflow, not as a chat-only prompt. Its strongest behavior so far:

- it resumes cleanly because state is explicit
- it separates assumption, drafting, audit, and score
- it avoids the earlier "19 constraints while writing" failure mode
- it makes migration between agents easier because every phase is a file contract
- it gives a cleaner commercial story: a reproducible pipeline, not a prompt dump

The remaining risk is not technical. It is editorial: any AI writing system can inflate its own assessment if audit and scoring are not adversarial. That is why Phase 4 is mandatory and cannot be skipped.

## Usage Notes

For Claude Code:

```text
/book-genesis-codex pt-br "memoir sobre burnout e reconstrucao profissional"
```

For Codex, Antigravity, Kimi, or another repo-aware agent:

```text
Use Book Genesis. Read AGENTS.md, then run the manifest in skills/book-genesis-codex/references/pipeline/manifest.yaml one phase at a time.
```

For a local mechanical check:

```bash
python runner/cli.py demo .tmp-book-genesis-demo
python runner/cli.py validate .tmp-book-genesis-demo
python runner/cli.py prepare-swarm .tmp-book-genesis-demo --mode hybrid --slug launch-reaction
python runner/cli.py prepare-agent-packet .tmp-book-genesis-demo pacing_engineer
```

For an existing manuscript:

```text
Use Book Genesis to audit this manuscript and continue from Phase 4.
```

For packaging only:

```text
Use Book Genesis to create the editorial package from this approved manuscript.
```

Use the old `/book-genesis` or `/book-genesis-full` only when you explicitly want the legacy Claude Code pipeline.
