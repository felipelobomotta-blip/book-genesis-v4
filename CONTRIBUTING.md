# Contributing to Book Genesis

Thank you for helping make serious story-making tools more accessible. Contributions are welcome across code, tests, prompts, genre profiles, documentation, provider compatibility, and reports from real use.

Book Genesis is a local technical beta. Treat author work, credentials, and quality claims with care. A generated text, an internal model score, or a passing unit test is not evidence that a book is ready to publish or that readers will respond well.

## Start locally

Requirements: Python 3.10+ and Git. No paid provider is needed to run the offline test suite.

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-v4.git
cd book-genesis-v4
python -m venv .venv
```

Activate the environment with your platform's normal command, then install the package and test tools:

```bash
python -m pip install -e .
python -m pip install pytest
python -B -m pytest tests -q -p no:cacheprovider
```

The suite uses local fake/manual flows and must not call live providers. Do not put API keys, auth files, private manuscripts, or real provider outputs into tests, fixtures, issues, commits, screenshots, or logs.

## Choose a contribution

- **Bug report:** include the command, operating system, Python version, expected behavior, actual behavior, and a redacted project structure or traceback.
- **Provider or adapter:** describe the CLI/stdin/stdout contract, platform tested, failure behavior, and a no-network regression test. Do not submit a token or config file.
- **Prompt or genre profile:** explain the intended audience and trade-off; add a deterministic test when output contracts or parsing behavior change.
- **Documentation:** correct claims that outrun the code or evidence. Precision is a feature.
- **Writing research:** open a discussion before adding market or literary claims so sources and scope can be reviewed.

Look for issues labeled `good first issue`, or open a discussion if the idea changes product behavior or needs design feedback.

## Development principles

1. The runner, not a model, owns project writes and phase transitions.
2. Keep author notes, drafts, verdicts, and history truthful. Never fabricate a passing verdict or replace a canonical file to make a demo look better.
3. Preserve the blind-reader boundary: judges should not gain outline, writer, or rubric context unless the design explicitly changes and is documented.
4. Fail closed for incomplete provider responses, unsafe paths, and ambiguous audit status.
5. Keep real provider calls opt-in. Tests must remain deterministic and offline.
6. Separate implemented behavior from future ideas in documentation and release copy.

## Pull requests

Before opening a pull request:

```bash
python -B -m pytest tests -q -p no:cacheprovider
python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .
git diff --check
```

In the PR description, explain the user-visible change, relevant files, tests run, and any provider/manual validation. If you did not run a check, say so. Keep a change focused; do not mix unrelated formatting or legacy cleanup with behavior changes.

Changes that affect the phase state machine, artifact contracts, audit gate, history format, provider permissions, or public quality claims need tests and an ADR under `docs/adr/`. Changes to prompts should state whether they alter a machine-readable output contract.

## Reporting security issues

Do not post credentials, private manuscripts, or exploitable details in a public issue. Follow [SECURITY.md](SECURITY.md) for the repository's reporting path.

## Community

Be direct, generous, and specific. Critique the work without treating authors, readers, contributors, or genres as lesser. Follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

The most valuable contribution may be a small one: a reproducible bug, a clearer phrase, a safe adapter test, a note from a first-time author, or evidence that a claim should be narrowed.
