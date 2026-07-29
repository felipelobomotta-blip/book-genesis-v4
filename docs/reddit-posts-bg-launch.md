# Reddit Launch Posts - Book Genesis

Four English launch posts with different angles. Stagger them. Do not cross-post identical copy.

Repo: https://github.com/felipelobomotta-blip/book-genesis-v4

## 1. r/ClaudeAI

**Title:** I built a Claude Code skill suite that runs a full AI book studio

**Body:**

I kept hitting the same problem with AI-assisted fiction: scoring during drafting makes the draft worse. The writer starts optimizing for the evaluator instead of the story.

So I built Book Genesis, a file-backed skill suite for Claude Code / Codex-style agents.

The current version includes:

- a 7-phase book pipeline
- adversarial audit before final scoring
- a developmental editor skill
- a market researcher skill
- a literary-agent panel
- a MiroFish-style reader swarm
- copyediting and humanizer passes
- editorial package generation

Everything persists to files: `PROJECT_STATE.yaml`, `ASSUMPTIONS.md`, `manuscript/`, `evaluations/`, `delivery/`.

The goal is not "AI writes a book in one shot." The goal is a repeatable production loop with evidence, gates, and revision pressure.

Repo: https://github.com/felipelobomotta-blip/book-genesis-v4

Curious how others are structuring multi-skill Claude Code workflows.

## 2. r/SideProject

**Title:** I open-sourced an AI book studio after running 10+ book projects through it

**Body:**

I spent the last few months building and stress-testing an AI book-production workflow.

Most AI writing tools stop at generating more text. I wanted the rest of the studio:

- research
- architecture
- drafting
- developmental editing
- reader simulation
- agent/editor review
- copyediting
- submission package
- launch assets

Book Genesis is the open-source version. It is markdown-first and agent-agnostic: Claude Code, Codex, Kimi, Antigravity, or anything that can read/write files.

The repo includes public case studies, cover concepts, scoring docs, skills, runner scripts, and launch materials. Manuscripts stay private.

Repo: https://github.com/felipelobomotta-blip/book-genesis-v4

Feedback welcome, especially from builders making long-form agent workflows.

## 3. r/LocalLLaMA

**Title:** File-backed long-form generation pipeline with audit-before-score gates

**Body:**

Sharing a pattern that has worked well for long-form generation: separate drafting from scoring.

Book Genesis is a markdown-only, file-backed pipeline. No model wrapper, no SaaS dependency.

The agent reads:

- `AGENTS.md`
- phase prompts
- scoring contracts
- project state files
- manuscript files
- evaluation files

Key design choice: adversarial audit happens before the quantitative score. The evaluator has to find structural cracks before assigning numbers.

The current repo also includes a 9-skill book studio: researcher, editor, agent panel, reader swarm, copyeditor, humanizer, and editorial packager.

Repo: https://github.com/felipelobomotta-blip/book-genesis-v4

Interested in whether this pattern generalizes beyond fiction: courses, reports, research briefs, grants, game narratives, etc.

## 4. r/writing

**Title:** An open-source workflow for using AI without letting the evaluator control the draft

**Body:**

I use AI assistance for long-form writing, but the first versions of my workflow made the writing worse.

The problem: the system scored the draft while it was still being written. That trained me to please the evaluator instead of following the story.

I rebuilt the workflow around one rule:

**No scoring during drafting. Audit structure first. Score with evidence later.**

Book Genesis is the open-source version of that workflow. It runs as a file-backed pipeline with phases for intake, foundation, architecture, drafting, adversarial audit, score, editing, and editorial package.

It also includes a simulated agent/editor panel and reader-swarm diagnostics, but those are decision aids, not replacements for human readers.

Repo: https://github.com/felipelobomotta-blip/book-genesis-v4

I would especially appreciate feedback from writers on what the audit phase should catch before a score is allowed.

## Posting Hygiene

- Read recent posts before posting.
- Do not post all four on the same day.
- Reply to comments for the first 2 hours.
- If a post gets removed, ask moderators why. Do not repost.
- Keep claims modest: "workflow," "skill suite," "pipeline," not "guaranteed bestseller machine."
