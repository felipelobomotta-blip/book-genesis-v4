# Book Genesis 5 — Imagination Edition · v5.0.0-beta.1

> **Creativity comes first. Your story. Your choices.**

Book Genesis is an open-source runner for taking an idea through a documented writing process: foundation, outline, chapter drafting, blind editorial reads, manuscript audit, review, and export. It is a beta for authors and contributors who want to test the process, question it, and improve it in public.

**Engineering update:** Developed with assistance from Astra in Codex, with independent review and recorded tests. This does not make Astra a required runtime provider or imply OpenAI endorsement.

## Start here

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-v4
cd book-genesis-v4
python -m pip install -e .
book-genesis setup
book-genesis new --language en
```

You bring a premise and choose the model provider. The project keeps its artifacts on disk, lets you pause and resume, and can export the canonical manuscript as Markdown or EPUB.

## What changed in this beta

- A guided `book-genesis new` session shows the brief, outline, and first chapter at meaningful checkpoints; notes from the author continue into later phases.
- The runner preserves chapter attempts, judge verdicts, and canonical-text hashes so a later edit cannot silently inherit an earlier approval.
- Interrupted artifact publication can recover from its journal instead of presenting stale files as a completed result.
- `book-genesis review PROJECT` creates a local, responsive reading report with chapter navigation, version comparison, and the editorial audit.
- `book-genesis export PROJECT --format markdown|epub` exports canonical chapters while protecting source artifacts from accidental overwrite.
- Adapters, installation resources, command paths with spaces, and timeouts received regression coverage.
- The manuscript-level audit is now a real gate. `audit_status: revise` or `audit_status: major_rewrite` leaves the project in `awaiting_revision`; Score and Package do not run until a later audit returns `pass`.

## Evidence from this beta

- **All four remote CI jobs passed** on Windows/Ubuntu with Python 3.10/3.12 for commit `4ba8ce2`. [View the run](https://github.com/felipelobomotta-blip/book-genesis-v4/actions/runs/33947757174).

- **279 automated tests passed locally** on Windows with Python 3.11 before remote CI, including package installation outside the checkout, recovery, history integrity, reader UI, export, and CLI regressions.
- One limited real-provider run produced the Portuguese one-chapter story *Data de Devolução* (1,910 words). This is an engineering smoke test, not evidence that the system writes publishable books.
- The first model-reader panel accepted the chapter and generated an internal 10/10 process signal. Once the full prose reached the manuscript audit, the audit found a structural gap and returned **MAJOR REWRITE**. The beta now blocks the pipeline at that point instead of treating the existence of an audit file as approval.

That last result is deliberate product evidence: Book Genesis should surface an editorial problem even when earlier internal signals look strong.

## What this beta does not claim

It does not promise a bestseller, publication readiness, human-reader validation, or consistent quality across long books. The current real run has one chapter. The creator remains responsible for the premise, choices, revision, voice, and publication decision.

## Help shape it

1. **Try one chapter.** Run a short premise through the guided flow and inspect the report.
2. **Report feedback.** Open an issue with your operating system, provider path, command, expected behavior, actual behavior, and any safe-to-share project artifact.
3. **Contribute.** Improve a prompt, a genre profile, an adapter, a test, documentation, or the reader experience. Start with the contributing guide and open a discussion when the change needs design input.

Please do not share API keys, private manuscripts, or personally identifying material in issues.

## Known limits for the beta

- First-run onboarding still uses a terminal and a model-provider configuration.
- Reader-panel results are model signals, not human research; one configured model family is allowed but reported as a warning.
- Long manuscripts can exceed a provider's context limit when the full manuscript is audited.
- A structural audit rejection explains the problem and blocks completion; it does not automatically repair the manuscript.
- Windows/Linux CI runs on Python 3.10 and 3.12; see the [release workflow results](https://github.com/felipelobomotta-blip/book-genesis-v4/actions/workflows/test.yml).

## Launch assets

The [marketing kit](../marketing/README.md) includes English platform copy, original AI-generated launch artwork, a six-slide carousel, a press kit, and a 14-day calendar. The [reader demo](../examples/reader-demo/README.md) is a reproducible scripted interface sample.
