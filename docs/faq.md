# FAQ -- Book Genesis

> Current note (2026-09-02): the default workflow is the Python runner (`README.md`, `docs/runner.md`): it drives the `claude` and `codex` CLIs, judges every chapter blind, and stops for a human after chapter 1. There is no numeric quality gate any more (ADR 0001). The V4/V5 answers below (17 phases, Genesis Score as a gate, CVI, `/book-genesis` commands) describe material that now lives in `legacy/` and are kept for history.

---

## General

### What is Book Genesis?

Book Genesis is a file-backed book production system. The current universal core is `book-genesis-codex`, a portable 7-phase pipeline for Claude Code, Codex, Antigravity, Kimi, and generic agent IDEs. The repository also preserves the older V4/V5 Claude Code skill network: 17 phases, specialized skills, Genesis Score, commercial viability prediction, anti-AI pattern checks, and automated revision loops.

For the current architecture, start with `docs/book-genesis-codex.md`.

### What changed from V2 to V4?

Everything that the system analysis identified as a structural ceiling was rebuilt. The short version:

- **3 new skills** added: chaos-engine (disruption), book-editor (dedicated revision), book-researcher (deep market research with comp passages)
- **Phase 3.5 (Disruption)** added between writing and evaluation
- **4th beta reader** (Casual Reader) added -- the airport reader who decides on vibes
- **Anti-AI protocol expanded** from 10 to 20 patterns, with genre-adjusted thresholds
- **Character chaos system** -- irrelevant thoughts, cognitive distortions, unprompted memories, failed emotional management
- **Emotional anchors** replace numerical curves (specific images, not "4/10 intensity")
- **Voice inhabitation** protocol before every chapter (freewrite as the character)
- **CVI (Commercial Viability Index)** separated from craft quality: CVI-Launch (first-year sales) and CVI-Legacy (20-year staying power)
- **Genesis Score V3.7** with genre-adjusted profiles, external benchmark anchoring, engagement types, 10 anti-inflation rules (up from 5)
- **8 structural types** for chapters with mandatory variation (no consecutive repeats)
- **7 opening strategies** for Chapter 1 (not just "competent professional encounters anomaly")
- **Impulse instruction** -- writer follows unplanned creative pulls
- **Mandatory ugly sentence** -- one deliberately rough sentence per chapter
- **Reading speed design** -- explicit acceleration and deceleration passages
- **5 scene transition types** with variation tracking
- **5 exposition disguise techniques**
- **Dialogue craft** expanded: interruptions, repetition, silence, responding to the wrong thing

See docs/changelog.md for the full list organized by category.

### What changed in V4.1?

- **Entity Tracker** -- new skill that builds and maintains `ENTITY_STATE.yaml`, a persistent structured state file tracking all manuscript entities (characters, locations, timeline, objects, world rules, organizations, knowledge graph)
- **Continuity Guardian upgraded** -- now reads ENTITY_STATE.yaml instead of rebuilding databases. New Audit 6 (YAML vs Text Divergence). Outputs suggested YAML patches.
- **All skills now in English** -- editorial-package and production-prep translated from Portuguese
- **Language-adaptive orchestrator** -- checkpoint messages match the book's language
- **Knowledge graph** -- tracks who knows what, when they learned it, and how (told, overheard, witnessed, discovered, inferred)
- **Chekhov tracking** -- objects tracked as `chekhov_open`, `chekhov_resolved`, or `texture`
- **Conflict detection** -- contradictions flagged as `UNRESOLVED` without auto-resolving

### What is the Entity Tracker?

A new skill (V4.1) that builds and maintains `ENTITY_STATE.yaml` -- a persistent, structured state file for all manuscript entities. It runs in two modes:

- **BUILD mode** (Phase 2.7): Reads foundation.md and outline.md to create the initial YAML with all characters, locations, timeline skeleton, objects, organizations, and world rules.
- **UPDATE mode** (Phases 3.7 and 5.5): Reads new chapters incrementally, runs 5 extraction passes (character scan, temporal scan, entity scan, object scan, knowledge flow), and merges findings into the YAML without reprocessing old chapters.

The entity-tracker never resolves contradictions -- it flags them as `UNRESOLVED` for the continuity-guardian to audit and the book-editor to fix. Every entry requires a source citation (chapter:paragraph).

The knowledge graph (`character.knowledge`) is the key innovation: it tracks who knows what, when they learned it, and by what method. This prevents the most common continuity error readers catch -- "how does this character KNOW that?"

### What is the Chaos Engine?

A new skill (Phase 3.5) whose only job is to break the predictability of each chapter AFTER the writer produces it and BEFORE the evaluator scores it. It moves scenes, deletes expected paragraphs, inserts irrelevant details, breaks moments of emotional control, and strips explanatory clauses from similes.

The system analysis found that all 5 test books produced by V2 were under authorial control at all times. Every chapter followed the same structure: establish normal, introduce anomaly, escalate, close on tension. The chaos-engine is the mechanism for controlled unpredictability -- the deliberate introduction of the wildness that separates competent from unforgettable.

The writer can review and reject any individual disruption.

### What is CVI?

Commercial Viability Index. Two separate scores:

**CVI-Launch** predicts first-year sales based on 6 inputs: market timing, comp title freshness, hook strength, platform/audience, pacing score, genre convention compliance. A book can have brilliant craft (Genesis Score 8.5) but bad market timing (CVI-Launch 5.0).

**CVI-Legacy** predicts 20-year staying power based on 5 inputs: re-readability, emotional resonance, shareability, identity effect, cultural vocabulary penetration. Some books explode at launch and vanish. Others sell modestly and become classics.

The Genesis Score tells you to keep revising. The CVI tells you when to stop revising and ship.

### How is this different from ChatGPT or other AI writing tools?

Most AI writing tools do one thing: generate text from a prompt. Book Genesis is a complete production SYSTEM with quality control.

The differences:
- **Quality gates** -- nothing advances without passing. A chapter that scores below threshold goes back for revision.
- **Anti-AI protocol** -- 20 patterns actively eliminated. The goal is prose that editors cannot distinguish from human writing.
- **Character chaos** -- characters think irrelevant thoughts, fail to manage emotions, and have unprompted memories. They behave like humans, not narrative vehicles.
- **Multi-agent architecture** -- separate skills for research, foundation, writing, disruption, evaluation, revision, and packaging. Each agent has a different perspective and different goals.
- **State persistence** -- STATE.yaml tracks everything across sessions. A 30-session book project maintains perfect continuity.
- **Commercial viability assessment** -- not just "is it well-written?" but "will it sell?"
- **Evaluation against published bestsellers** -- comp title passages provide real benchmarks, not abstract rubrics.

ChatGPT generates a chapter. Book Genesis generates a book that competes on the shelf.

### Can it write in languages other than English?

Yes. All skills are written in English. Claude adapts the output to whatever language you use. If you start a conversation in English, the entire pipeline operates in English. Same for Spanish, French, German, Japanese, etc.

The voice bank and foundation documents should be in the target language. The anti-AI patterns are language-agnostic (they describe structural patterns, not specific words).

### What genres does it support?

V4 has 8 genre profiles with adjusted scoring across all 7 dimensions:

- Literary Fiction
- Memoir
- Thriller
- Commercial Fiction
- Romance
- Sci-Fi/Fantasy
- Prescriptive Non-Fiction
- Narrative Non-Fiction

Each genre has different expectations for prose quality, pacing, character depth, theme weight, and anti-AI thresholds. A thriller where the reader notices the prose has failed. Literary fiction without a stopping sentence has failed. The same manuscript scores differently depending on genre because the genre's readers expect different things.

If your genre is not listed, the system uses the closest profile. You can also specify a custom combination (e.g., "literary thriller" = literary prose expectations + thriller pacing expectations).

### How long does it take to generate a full book?

Depends on length, genre, and revision cycles.

Rough estimates:
- **Short book (30-40K words):** 15-25 sessions across 3-5 days
- **Standard novel (60-80K words):** 25-40 sessions across 5-10 days
- **Long novel (100K+ words):** 40-60 sessions across 10-20 days

Each session is limited by Claude's context window. Longer books require more sessions. The revision loop (Phase 4-5) typically adds 30-50% more sessions.

The proof-of-concept (Protocolo Nao Encontrado, 67.8K words) took approximately 20-30 sessions with 2 full revision cycles.

### How much does it cost (Claude usage)?

Book Genesis is free and open source (MIT license). Your cost is the Claude subscription:

- **Claude Pro ($20/month):** Works for shorter books or chapter-by-chapter work. You may hit usage limits on intensive revision sessions.
- **Claude Max ($100/month):** Recommended for full manuscripts. Extended context windows, higher usage limits. Better for evaluation and revision of large sections.

There are no external API calls, no databases, no build steps. Just markdown files and Claude.

### What is the Genesis Score?

A 7-dimension FLOOR scoring system for manuscript quality. The score equals the WEAKEST dimension -- not the average. A book with 6 dimensions at 9.0 and one at 7.0 has a Genesis Score of 7.0.

The 7 dimensions: Originality, Theme, Characters, Prose and Voice, Pacing and Coherence, Emotion, and a Configurable dimension (Market, Worldbuilding, Humor, etc.).

V3.7 includes:
- Genre-adjusted profiles (what scores 8.0 varies by genre)
- External benchmark anchoring against 5 bestsellers (338M+ copies)
- 10 anti-inflation rules
- 20-pattern anti-AI scan with genre thresholds
- CVI-Launch and CVI-Legacy calculations
- 5 engagement type configurations

The floor must reach the genre-adjusted threshold (7.0-7.5 depending on genre) to advance to delivery. 8.0+ is recommended for editorial submission.

### Can I use my own voice samples?

Yes. The voice construction protocol in narrative-foundation supports two paths:

**If you have writing samples:** Provide 3-5 pages of natural writing (emails, social media posts, diary entries, audio transcripts -- writing where you were NOT trying to write well). The system extracts patterns: sentence length, vocabulary, verbal tics, irony level, emotional handling, rhythm, punctuation, cultural references.

**If you do not have samples:** Define by reference. Choose 2-3 published authors whose voice approximates what you want. The system decomposes their voice elements and synthesizes a unique combination.

V4 requires the voice bank to include 3+ samples of the voice FAILING under pressure. A voice that sounds the same at peace and in crisis is a robot. The voice-under-pressure specification is mandatory.

---

## Technical

### How do I install it?

From a local checkout. On macOS/Linux:
```bash
./install.sh
```

On Windows PowerShell:
```powershell
.\install.ps1
```

Skills are installed to `~/.claude/skills/`. Modern multi-file skills, including `book-genesis-codex`, must be copied as full directories because their references live outside `SKILL.md`.

### Can I use individual skills without the full pipeline?

Yes. Every skill works standalone. Use `/narrative-foundation` to build characters for any project. Use `/prose-craft` to improve dialogue in an existing manuscript. Use `/beta-reader` to get feedback on any text. Use `/chaos-engine` to disrupt a chapter that feels too controlled.

### Does it use external APIs?

No. Book Genesis is markdown and file contracts. No external APIs, no databases, no build step. Research phases may use the host agent's web/search capability when the active tool supports it.
