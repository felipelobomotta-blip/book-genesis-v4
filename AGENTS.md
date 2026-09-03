# Agent Instructions

This repository is Book Genesis: a Python runner that turns one idea into a manuscript, chapter by chapter, using Markdown prompt templates in `agents/` and phase prompts in `skills/book-genesis-codex/references/`.

## Default Behavior

When asked to create, plan, draft, judge, revise, or package a book, **use the runner**. Do not orchestrate the phases by hand and do not grade prose yourself.

```bash
python runner/cli.py init <project> --idea "..." --language <code>
python runner/cli.py run-phase <project>        # repeat for intake, foundation, architecture
python runner/cli.py book <project>             # writes chapters; stops after chapter 1 for a human
python runner/cli.py approve <project> chapter-01
python runner/cli.py judge <file.md> --genre "..."   # blind-read any chapter
```

The design is recorded in `docs/adr/0001-runner-orquestra-juiz-cego.md`. The short version:

- the runner owns every file; models receive text and return text, never tools;
- the judge (`agents/book-judge.md`) is blind: prose only, no outline, no foundation, no writer notes; it compares drafts instead of scoring them;
- the writer does not know any rubric; `agents/book-evaluator.md` is a diagnostic for the editor, not a gate;
- a human must approve chapter 1 before chapter 2 is written;
- constants live in `runner/config/genre-profiles.yaml` and `runner/config/models.yaml`; prompts reference them and never restate numbers.

## Rules

- Persist decisions to files inside the project directory; keep `PROJECT_STATE.yaml` and `ASSUMPTIONS.md` truthful.
- Never claim a chapter, a score, or a book is "ready" from an internal signal alone. Internal reader verdicts are not external validation.
- Write Portuguese artifacts and prose in Portuguese when the book is in Portuguese.
- Do not resurrect anything from `legacy/` onto the canonical path without a new ADR.

## Where things are

- `runner/` — the orchestrator: `cli.py`, `phases.py`, `brief.py`, `chapter.py`, `book.py`, `judge.py`, `adapters.py`, `constants.py`, `roles.py`.
- `agents/` — prompt templates read by the runner (also installable as Claude Code subagents).
- `skills/book-genesis-codex/references/` — phase prompts and the manifest the runner follows.
- `knowledge/` — bestseller research the templates cite.
- `tests/` — 52 tests, no network (`python -m pytest tests -q`).
- `legacy/` — the three earlier pipelines, moved on 2026-09-02, not maintained.

## Public Documentation

- `README.md`: overview and quick start.
- `docs/runner.md`: commands, exit codes, configuration, limits.
- `docs/REVISAO-CONSISTENCIA-2026-09.md`: the review that motivated ADR 0001.
- `SHOWCASE.md`, `docs/book-gallery.md`, `examples/cases/`: earlier projects.
