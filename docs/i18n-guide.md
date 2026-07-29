# Internationalization (i18n) Guide

Best Seller Studio is genre- and language-portable. This guide covers what to change (and what not to change) when running the pipeline in a language other than English.

## Supported languages

The pipeline has been end-to-end validated in:

- Portuguese (Brazilian) — full, native
- English — full, native
- Spanish — partial, community-contributed

The pipeline has been *spot-tested* in Italian, French, German. Quality is expected to be comparable; polish is genre-dependent.

Adding a language does not require code changes. It requires only well-written agent prompts for that language's literary conventions.

## Non-English brief handling

You can brief the pipeline in any language Claude Code understands. The pipeline:

1. Runs research in the brief's language
2. Retains genre conventions native to that language (e.g., magical realism as literary default in Latin American Spanish, not commercial thriller)
3. Adjusts the 8.5 gate's genre floor to the target market
4. Produces the manuscript in the brief's language

## Genre-adjusted floor

The Genesis Floor 8.5 is not universal. Different genres in different languages have different market expectations:

| Genre + market | Hard floor |
|---|---|
| English literary fiction | 7.5 |
| English commercial thriller | 7.0 |
| English prescriptive non-fiction | 7.0 |
| Portuguese (BR) literary fiction | 7.5 |
| Portuguese (BR) commercial | 7.0 |
| Spanish literary (Latin American) | 7.5 |
| Spanish commercial (Iberian) | 7.0 |
| Memoir (any language) | 7.5 |

Below the hard floor, the manuscript is auto-rejected at Checkpoint 2 regardless of the 8.5 target.

## Contributing a translation

Two levels:

### Level 1 — README + skill descriptions

Translate high-level docs. Low friction. Great first PR.

- `README.md` → `README.<lang>.md`
- `docs/agents-<lang>.md` — one-line descriptions of the 11 agents
- `SHOWCASE.md` → `SHOWCASE.<lang>.md` if worthwhile

### Level 2 — Agent prompts

Translate the agent instructions themselves. This is a real port, not a translation — literary rules change per language (e.g., Portuguese sentence rhythm is not the same as English's; Spanish paragraph breaks work differently).

- `/agents/book-writer.md` → agents/pt-br/book-writer.md
- Localize CHAPTER FUNCTION, CHARACTER ENTRY LEVELS, REALISM CONSTRAINTS to the target language's craft norms
- Localize the evaluator's REVISION FINDINGS FRAMEWORK to the target market's reader expectations

Native or near-native language reviewers required. Machine translation of agent prompts produces bad books; we do not accept those PRs.

## Right-to-left languages

The pipeline is currently left-to-right only. Arabic, Hebrew, Persian would need:

1. RTL-aware manifest files (JSON is fine; only prose in Markdown needs to be RTL-flagged)
2. RTL-aware demo assets (currently LTR-only)
3. Native reviewer for the evaluator's phonetic/rhythm rules (very different from LTR languages)

We welcome a PR that opens this direction. Talk to us in [Discussions](https://github.com/felipelobomotta-blip/book-genesis-v4/discussions) first — the design work is bigger than the PR.

## Encoding

- All Markdown UTF-8, no BOM
- Line endings LF (enforced by `.gitattributes` since V4.2)
- File names ASCII where possible (avoids Windows/macOS/Linux path issues)
