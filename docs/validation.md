# Validation record — Imagination Edition

This is an engineering evidence record for `v5.0.0-beta.1`, prepared on September 5, 2026. It distinguishes software behavior from manuscript quality. A passing test suite does not establish that the resulting books are publishable.

## Automated verification

The publication checkout passed **279 tests in 66.37 seconds** on Windows with Python 3.11. The suite includes interrupted phase recovery, immutable attempt history, canonical text/hash integrity, persisted author checkpoints, adapter errors and timeouts, audit rejection, local reader escaping and containment, Markdown/EPUB integrity, and package resources installed outside the source checkout.

The wheel test builds the package, installs it into an isolated temporary target, changes out of the source directory, and exercises the installed resource lookup. The configured GitHub workflow runs the same suite and a wheel build on Windows and Ubuntu with Python 3.10 and 3.12. Its current remote results are visible in [GitHub Actions](https://github.com/felipelobomotta-blip/book-genesis-v4/actions/workflows/test.yml).

Independent code review identified issues in provider isolation, publication recovery, history integrity, and manuscript audit gating during the quality pass. Those findings were corrected and reviewed again; the final focused audit-gate regression set passed 21 tests. Review does not guarantee the absence of defects.

## A real provider exercise

A limited run used Claude for writing and Codex for the model-reader panel. It produced one 1,910-word Portuguese chapter, *Data de Devolução*. The three reader personas used the same judge model; they were not three human readers or three independent model families.

The original panel accepted the chapter and the process card reported 10/10. A later audit of the **full manuscript prose** found that the ending did not resolve a key premise distinction: disappearance versus death. It requested **MAJOR REWRITE**. That contradicted the favorable early signal and exposed a software issue: an audit artifact existed, but its editorial rejection had not blocked completion.

The corrected implementation requires an explicit audit status. `revise` and `major_rewrite` keep Phase 4 current with `awaiting_revision` and exit code 4. A replay using the saved real audit response verified that Score and Package did not run and that the canonical chapter remained unchanged. That replay used frozen responses; it was not a second live-provider book generation.

See the [case study](../examples/data-de-devolucao/README.md) for the artifact fingerprint and implications.

## Reader UI evidence

The local reader was exercised at desktop and narrow phone dimensions during the quality pass. The public [reader sample](../examples/reader-demo/README.md) uses scripted English text to make navigation, attempt history, comparison, and audit status reproducible. Its screenshot is captured from the actual HTML reader. Neither the sample nor its fixture verdicts measure literary quality.

## Limits still open

- No completed human-reader preference study or publication outcome study.
- No validated relationship between the internal Genesis Score and sales, literary quality, or human preference.
- One short real-provider exercise does not establish long-book continuity, context-window behavior, or reliability across every adapter.
- CLI/API configuration remains part of onboarding. Ease of use for people new to terminals needs direct user testing.
- A rejected structural audit requires author revision and another audit. The beta does not automatically repair the manuscript.
- Model services can time out or reject a request. In the live exercise, a Claude audit timed out at 180 seconds; a later Codex audit path returned a usable result.

The appropriate release status is **beta**. The next evidence should come from reproducible first-chapter runs and consenting human readers, with the model verdicts kept separate from human feedback.

## Reproduce the software checks

```bash
python -m pip install pytest rich wheel setuptools
python -m pytest tests -q
python -m pip wheel --no-deps --no-build-isolation --no-cache-dir --wheel-dir dist .
```

No API key or live model call is needed for the regression suite. Live provider runs are separate and may incur the selected provider's costs.

## Clean-runner findings

The first GitHub CI run exposed three unit tests that depended on installed Claude/Codex commands, a doctor test that depended on local provider configuration, and a Windows-only separator in a rollback fixture. The fixtures now declare their environment explicitly and use path components. Their behavioral assertions remain in place. After these corrections, the isolated local suite passed 279 tests in 26.73 seconds; remote matrix results remain inspectable in GitHub Actions.
