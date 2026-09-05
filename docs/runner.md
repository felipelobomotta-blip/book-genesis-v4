# The Runner

The runner is the orchestrator. It reads state, assembles prompts from project files, calls a model through an adapter, validates what comes back, writes files, and advances. Models return text under the runner's output contract. Tool isolation depends on the adapter; see below. This document is the operational reference; the reasoning is in [ADR 0001](adr/0001-runner-orquestra-juiz-cego.md).

Source checkouts read templates from `agents/` and `skills/book-genesis-codex/references/`. Wheels bundle those resources under `runner/data`, so an installed package can run outside the checkout. Build locally with `python -m pip wheel --no-deps --no-build-isolation --wheel-dir dist .`; this does not publish a release.

## Commands

Installed with `pip install -e .`, the same program is the `book-genesis` command; `python -m runner` also works.

```bash
book-genesis setup                               # choose providers, connect keys (hidden input), pick models
book-genesis new [--idea "..."] [--language en] [--path DIR] [--human] [--manual]   # guided project run
book-genesis resume <project>                    # continue from wherever it stopped
book-genesis review <project> [--open]           # inspect the report and generated artifacts
book-genesis export <project> --format markdown|epub [--output PATH] [--overwrite]
python runner/cli.py doctor                      # providers found, user config, role plan, panel seats, warnings
python runner/cli.py init <project> --idea "..." --language en
python runner/cli.py status <project>
python runner/cli.py run-phase <project> [--manual] [--fake-responses FILE]
python runner/cli.py brief <project> <chapter>
python runner/cli.py chapter <project> <chapter> [--human] [--manual] [--fake-responses FILE]
python runner/cli.py book <project> [--from N] [--to N] [--human] [--manual] [--fake-responses FILE]
python runner/cli.py panel <project> <chapter> [--manual]   # the whole reader panel on a written chapter
python runner/cli.py approve <project> chapter-01           # human mode only
python runner/cli.py judge <file.md> [--previous FILE] [--genre "..."] [--reader "..."] [--anchor FILE]
                                     [--adapter claude|codex|fake|<adapters.yaml name>] [--model NAME] [--out FILE]
python runner/cli.py validate <project>
python runner/cli.py demo <path>                 # deterministic file-contract demo, no model
```

`--human` additionally requires explicit approval after chapter 1. The guided terminal session also asks for decisions at the brief, outline and chapter 1 unless `--yes` or non-interactive input is used. `--manual` turns every model call into a prompt file under `work/manual/` for people who only have a chat window. In the guided session, Enter continues, a typed response becomes author notes, and `q` stops safely; `resume` continues from the saved state and reports remaining work.

`review` writes a self-contained reading page under `review/index.html`, with chapters, version history and comparison; `--open` opens that local file. `export` writes Markdown or EPUB under `exports/` and explicitly identifies partial work. Choose `--output PATH` for another destination. Inside the project, exports stay under `exports/` to protect inputs; `--overwrite` can replace an export, never the source manuscript. Neither command uploads the book.

`prepare-phase`, `advance-phase`, `prepare-swarm` and `prepare-agent-packet` remain for manual use and for the swarm and bestseller-studio contracts; the commands above are the canonical path.

### Exit codes

| code | meaning |
|---|---|
| 0 | done |
| 1 | failure (adapter error, missing file, phase outputs incomplete) |
| 2 | usage |
| 3 | awaiting a human (`--human` only): read `manuscript/chapters/chapter-01.md`, then `approve` |
| 4 | blocked: chapter revision budget exhausted, or the manuscript audit requests `revise` / `major_rewrite`; drafts and diagnosis remain available |
| 5 | awaiting a pasted reply (`--manual` only): send `work/manual/<hash>-<role>.prompt.md` to your model, paste the reply into the matching `.response.md`, run the same command again |

## What one chapter does

1. `brief` assembles `briefs/chapter-NN.md` deterministically: the chapter's `## Chapter N` section from `artifacts/05-outline.md`, `artifacts/02-story-engine.md`, `artifacts/03-characters.md`, the last 300 words of the previous chapter, and the genre constants.
2. The **writer** gets the brief and the writer template. It returns prose. Craft notes, preambles and fences are stripped before anything else sees the text.
3. The **disruptor** runs when the genre profile says so (fiction by default; not for nonfiction).
4. The **judge** gets prose plus the previous chapter's tail. Never the outline, never the foundation. It returns a fenced YAML block: `turn_page`, `stopped_at`, `remember`, `flags`, `vs_previous`, `vs_anchor`.
5. If the reader would not turn the page, the **editor** runs in the modes the judge flagged, working from the best draft so far and the exact sentence where attention left the page. The judge then compares the new draft with the previous best. `worse` means the new draft is discarded.
6. Accepted chapters go to `manuscript/chapters/chapter-NN.md`. Every draft and verdict stays in `manuscript/drafts/` and `evaluations/`; `RUN_REPORT.md` gets one line per chapter (status, cycles, judge, last verdict).
7. In `book`, chapter 1 is judged by the **model-reader panel** instead of the single judge: the seats in `models.yaml` (`panel_*`), each with its own persona, each reading blind. Majority decides `turn_page`; a flag needs two votes in a panel of three; the most-cited `stopped_at` goes to the editor. A seat whose adapter is not installed falls back to what is, keeping the persona. A single-family run is allowed and recorded as a warning. With `--human`, the runner pauses after chapter 1 until `approvals/chapter-01.approved` exists.

## Phases

`run-phase` runs the current phase of the manifest through the `architect` role: the phase prompt, the project idea, the assumptions, and every artifact already written go into one prompt; the reply is split on `=== FILE: <path> ===` markers and only the files the phase requires are written. A `=== STATE ===` block updates `title`, `genre`, `audience`, `language` and `target_length` in `PROJECT_STATE.yaml`. The phase advances only when every required output exists and is not a template.

Phase 3 (drafting) is never run by `run-phase`; it is `book` / `chapter`. Post-draft phases receive all canonical chapters. Phase 4 is a semantic audit gate: only `audit_status: pass` advances; `revise` and `major_rewrite` persist the report and block the guided session at `awaiting_revision`. Read the report, revise the manuscript, then resume for a new audit. Phase 5 provides an editorial diagnostic, and Phase 6 prepares draft editorial materials. Neither supplies evidence of market success. See [ADR 0015](adr/0015-gate-semantico-do-audit.md).

## Configuration

`setup` (`runner/setup.py`, `runner/onboarding.py`; ADR 0004) detects installed CLIs, key variables and local servers, offers a quick start with what it found, otherwise a numbered provider menu (subscriptions through the Claude Code and Codex OAuth logins, OpenRouter, DeepSeek, Anthropic, OpenAI, Groq, Together, Ollama, LM Studio, another endpoint, manual), lists models live from the provider, and makes one real completion for the writer and one for the judge before writing anything. A failed check saves nothing and says why, without the key. On an existing config it offers keep, change, or reset.

`~/.book-genesis/config.yaml` (written by `setup`; override the location with `BOOK_GENESIS_CONFIG`) holds the person's own providers and roles and wins over the repository defaults. A provider is a `provider_<name>` entry with `type` (`openai` for any `/chat/completions` endpoint, `anthropic` for the Messages API), `base_url`, and either `api_key` or `api_key_env`. Roles and `panel_*` seats use the same shape as `models.yaml`. Never commit that file.

`runner/config/models.yaml` maps each role (`writer`, `disruptor`, `judge`, `editor`, `architect`, `extractor`) to an adapter and a model alias. The default aims to put the judge on a different family than the writer; when that is unavailable, the run proceeds with a recorded single-family warning.

`runner/config/genre-profiles.yaml` holds, per genre: words per chapter, dialogue share, maximum revision cycles, whether the disruptor runs, and the anti-AI pattern budget. Free-text genres from intake are mapped through the `aliases` block; unknown genres fall back to `default`.

## Adapters

| adapter | how | notes |
|---|---|---|
| `claude` | `claude -p --output-format text --model <alias>`, prompt on stdin | works from inside a Claude Code session |
| `codex` | `codex exec --ignore-user-config --ephemeral -s read-only -o <file>`, prompt on stdin | `--ignore-user-config` skips the user's MCP servers and skills, which the judge does not need and which cost ~40 s and ~20k tokens per call |
| provider of type `openai` (from `setup`) | `POST {base_url}/chat/completions`, stdlib `urllib`, key in the Authorization header only | OpenRouter, DeepSeek, OpenAI, Groq, Together, Ollama and LM Studio local servers, any compatible endpoint |
| provider of type `anthropic` (from `setup`) | `POST {base_url}/v1/messages`, `max_tokens` 16000 | the Anthropic API |
| any name in `adapters.yaml` | the declared command template, `{model}` filled in, prompt on stdin, reply on stdout | opencode, ollama, Hermes, DeepSeek CLI, anything |
| `manual` | writes the prompt to `work/manual/<hash>-<role>.prompt.md`, exits 5, reads `<hash>-<role>.response.md` on the next run | chat-only setups: Antigravity, DeepSeek web, a browser tab |
| `fake` | scripted responses from a file, separated by `=== NEXT ===` lines | tests only |

CLI adapters use the session already logged in on the machine. HTTP adapters read the configured key and send it to the chosen provider. Claude is invoked in safe mode with tools disabled. Codex runs in a temporary directory with an ephemeral read-only sandbox and a text-only output contract. This does not prove that every Codex tool is disabled in every host environment.

`doctor` runs the same discovery the commands run: it lists which CLIs are on PATH and prints the role plan. When a configured adapter is missing, its roles fall back to the first installed one; when writer and judge end up in the same family, the judge takes a different model and every run prints and records a `single family` warning.

## Tests

```bash
python -m pytest tests -q
```

The repository contains local tests for the judge parser and blindness, the brief, chapter loop, panel, role plan, adapters, phases, book loop, and CLI flows. Run the suite for the checkout you are reviewing before treating any test count or integration claim as current. Packaging resources are included by the local package wiring; this document does not claim a published package, remote CI result, or a test run.

## Measured run (2026-09-02, Windows 11, subscriptions only)

Idea: *"Uma analista de plantão noturno em Brasília percebe que nove sistemas independentes do governo começaram a cometer exatamente os mesmos erros, no mesmo segundo, e ninguém mais acha isso estranho."* Language pt-BR. Roles as in `models.yaml` (architect and writer: claude opus; disruptor: claude sonnet; judge: codex default model).

| step | result | wall clock |
|---|---|---|
| Phase 0 intake | ASSUMPTIONS.md + 3 artifacts; state updated (title *Nove Erros Idênticos*, genre thriller, 95k words) | 216 s |
| Phase 1 foundation | characters, theme, emotional curve | 353 s |
| Phase 2 architecture | outline (4 parts, 38 chapters, 12 documentary artifacts) + opening strategy | 306 s |
| chapter 1 (`book`) | brief 30 KB assembled; writer + disruptor produced a 1,712-word chapter; blind judge: `turn_page: yes`, no flags, five remembered items; accepted on the first pass; runner stopped with exit 3 for the human checkpoint (ADR 0001 behaviour, now `--human` only) | 268 s (writer + disruptor ≈ 256 s, judge ≈ 12 s) |
| chapter 1 (`panel`, ADR 0002) | three blind readers: codex as the genre buyer, claude sonnet as the hostile reader, claude opus as the airport reader; majority `turn_page: yes`; no flag reached two votes; one reader's attention dropped at the paragraph inventorying the nine data collectors; thirteen remembered details across the three (the coat with the cigarette burn, "412. 412. 412.", the foot that stopped moving) | ≈ 210 s for the three seats |

The first `book` run had failed closed in 0 s: the architect had written chapters as bold lines (`**Capítulo 1 — 3h14**`), not headings. Two fixes followed, both kept: the architecture prompt now states the heading contract, and the runner also accepts bold chapter markers in English and Portuguese (tests `test_bold_portuguese_chapter_markers_are_understood`, `test_counts_bold_portuguese_markers_too`). The second run went through.

What the judge remembered from chapter 1, verbatim from `evaluations/chapter-01-judge-1.md`: *"Aconteceu nos nove. No mesmo pixel."*; Rita covering the other timestamps with her hand to read 412 nine times; Nelson's coat, nineteen years later, with the cigarette burn; the March ticket already marked resolved; Rita counting the cursor's blinks. No craft notes, runner contract text or undecodable characters reached the manuscript.

One accepted chapter read by one model judge is a smoke test, not a validation. The claim this repository can make today is narrower than before and true: the pipeline runs end to end on this machine, from one sentence to a judged chapter, with every draft and verdict on disk.

## Known issues

- On Windows, a long `claude -p` reply occasionally contains a byte pair that is not valid UTF-8 (measured once: 2 characters in ~30k bytes of a 3-minute intake reply; short replies and the JSON format were clean in a direct test). The adapter keeps the text and prints a warning with the count; search the artifact for `�` and fix by hand or re-run the phase.

## What the runner does not do

- Export supports Markdown and EPUB. It does not decide publication readiness; review the generated deliverable with human readers and editors before making publication claims.
- It does not run market research inside `run-phase`; `agents/book-researcher.md` is only available as a subagent for now.
- It does not run the reader swarm; `prepare-swarm` only lays out the folder contract.
- It does not validate anything with human readers. A model-reader signal is still not external validation, a publication decision, or a sales forecast.
