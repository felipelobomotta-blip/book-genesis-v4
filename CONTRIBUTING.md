# Contributing

Book Genesis accepts improvements to editorial contracts, portable skills, deterministic runner behavior, tests, examples, and documentation.

## Setup

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-v4.git
cd book-genesis-v4
python runner/cli.py verify-suite
python -m unittest discover -s tests -v
```

No provider API key is needed for repository tests. Runner never calls a model.

## Canonical Rules

- `skills/book-genesis/` is canonical portable core.
- Keep Claude Code, Codex, and Kimi Code on same editorial contracts.
- Keep platform-specific behavior in installer or dispatch adapters.
- Never skip adversarial audit before final scoring.
- Keep raw blind evaluators unaware of target and previous scores.
- Preserve commercial-length gate and Literary Barrier loop.
- Do not add literal bestseller guarantees.

## Skill Changes

- Keep `SKILL.md` concise and put detailed contracts under `references/`.
- Preserve `name` and `description` frontmatter.
- Add referenced specialist skills to `distribution/portable-suite.json`.
- Run `python runner/cli.py verify-suite` after changing manifests, registries, prompts, or skill packaging.

## Runner Changes

- Use Python standard library unless dependency earns its installation cost.
- Add tests for filesystem mutations, failure states, and cross-platform paths.
- Do not overwrite user-modified skills silently.
- Keep forced replacement recoverable through backups.

## Pull Requests

Include:

- problem being solved
- behavioral change
- affected skills or phases
- test evidence
- migration note when file contracts change

Keep manuscripts, API keys, session logs, and private reader data out of commits.
