# Architecture -- Book Genesis V4

> Current note: the default workflow for new projects is now the Universal Book Genesis Core (`skills/book-genesis-codex/`). This document remains the legacy V4/V5 architecture reference. See `docs/book-genesis-codex.md` for the portable agent pipeline.

Book Genesis V4.1 is a 17-phase pipeline (with sub-phases) that transforms a one-sentence idea into a commercially viable, publishable manuscript. V4 was built from the ground up after a 5-genre stress test (SYSTEM-ANALYSIS.md) identified 9 structural problems in V2. V4.1 adds 8 skills, doubles the phase count, and introduces fully autonomous execution via `/book-auto`. Every architectural change traces back to a specific failure in the system analysis or lessons learned from real manuscript iterations.

---

## Pipeline Overview

```
IDEA (1 sentence)
    |
    v
+-------------------------------------------------------------------+
| PHASE 1 -- Research                                                |
|                                                                    |
| Skill:  book-researcher (NEW in V4)                               |
| Input:  User idea + genre + target audience                       |
| Actions:                                                           |
|   - WebSearch for top 10 books in niche (last 5 years)            |
|   - Identify market gaps and white space                           |
|   - Define 3-5 comp titles with positioning analysis               |
|   - Extract bestseller DNA (prose patterns, pacing, hooks)         |
|   - Estimate target word count by genre conventions                |
|   - Pull 3-5 comp title PASSAGES for evaluator benchmarking        |
| Output: Research report + bestseller-dna.md + comp passages        |
| Gate:   User approves direction before advancing                   |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 1.5 -- Reader Personas (NEW in V4.1)                        |
|                                                                    |
| Skill:  reader-persona                                             |
| Actions:                                                           |
|   - Build 3-5 reader personas from research data                   |
|   - PRIMARY persona (drives writing when conflicts arise)          |
|   - HOSTILE persona (drives evaluator's toughest simulation)       |
|   - STRETCH persona (adjacent-genre reader)                        |
|   - Each persona: psychology, deal-breakers, triggers, channels    |
| Output: reader-personas.md                                         |
| Downstream: writer, evaluator, packager, chaos-engine              |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 2 -- Foundation                                              |
|                                                                    |
| Skill:  narrative-foundation                                       |
| Produces:                                                          |
|   - Characters with 7 layers + CHAOS PROFILES (NEW)               |
|     (irrelevant obsessions, cognitive distortions,                 |
|      unprompted memories, voice-under-pressure)                    |
|   - Emotional ANCHORS per chapter (not numerical curves)           |
|   - Emotional SURPRISES per chapter (the wrong emotion)            |
|   - Theme as question + 4 levels of weaving                        |
|   - Voice guide with voice bank (10-15 samples)                    |
|     INCLUDING 3+ samples of voice FAILING under pressure           |
|   - Engagement type ranking (primary/secondary/tertiary)           |
|   - Re-read architecture (details that gain meaning after ending)  |
|   - Cultural vocabulary (branded terms)                            |
|   - Stylistic device configuration (if any)                        |
|   - Chapter-by-chapter outline with:                               |
|     - Structural approach (1 of 8 types, no consecutive repeats)   |
|     - Opening strategy (for Ch. 1: voice bomb, in medias res, etc.)|
|     - Value shift (positive <-> negative)                          |
|     - Chapter-ending hook type                                     |
|                                                                    |
| Gate: User approves foundation + outline before writing            |
| Loop-back: If writing reveals foundation needs change, return here |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 2.5 -- Voice DNA (NEW in V4.1)                              |
|                                                                    |
| Skill:  voice-fingerprint                                          |
| Actions:                                                           |
|   - Global narrative voice profile (POV, sentence architecture)    |
|   - Per-character voice cards with speech patterns, syntax,        |
|     metaphor source, voice-under-pressure (3 stress levels)        |
|   - Voice differentiation matrix (3+ markers per character pair)   |
|   - Anti-pattern budget (em-dash limits, Pattern #11 per chapter)  |
|   - Cover-the-name test definition per character                   |
| Output: voice-dna.md                                               |
| Gate: Voice DNA approved before writing begins                     |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 2.7 -- Entity Tracking (NEW in V4.1.1)                      |
|                                                                    |
| Skill:  entity-tracker (BUILD mode)                                |
| Actions:                                                           |
|   - Read foundation.md: extract characters, relationships,         |
|     physical traits, knowledge, world rules                        |
|   - Read outline.md: extract locations, timeline skeleton,         |
|     key objects, organizations                                     |
|   - Generate ENTITY_STATE.yaml from scratch                        |
|   - All entries sourced to foundation or outline                   |
| Output: ENTITY_STATE.yaml                                          |
| Gate: YAML created before continuity check                         |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 2.8 -- Outline Continuity                                    |
|                                                                    |
| Skill:  continuity-guardian (first pass)                           |
| Actions:                                                           |
|   - Reads ENTITY_STATE.yaml for structured entity data             |
|   - Audit outline for character consistency                        |
|   - Validate timeline logic                                        |
|   - Check information flow (no character knows before being told)  |
|   - Verify all plot threads have resolution planned                |
|   - Check world rules consistency                                  |
| Output: continuity-report-outline.md                               |
| Gate: No CRITICAL issues before writing begins                     |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 3 -- Writing                                                 |
|                                                                    |
| Skill:  prose-craft (Writer)                                       |
| Process:                                                           |
|   - VOICE INHABITATION before each chapter:                        |
|     200-300 word freewrite AS the character (discarded)             |
|   - Write chapter following 6 flexible obligations:                |
|     1. Voice (non-negotiable, must CHANGE under pressure)          |
|     2. Substance (30-40% texture details, no thematic echo chamber)|
|     3. Emotional Anchor (specific image/moment, not intensity #)   |
|     4. Theme (allowed to RECEDE in some chapters)                  |
|     5. Device (if applicable)                                      |
|     6. Pacing (value shift, chapter hook, speed variation)          |
|   - CHARACTER CHAOS mandatory per chapter:                         |
|     irrelevant thought, cognitive distortion, unprompted memory,    |
|     failed emotional management                                    |
|   - Anti-AI Protocol: 20 patterns (not 10) internalized BEFORE     |
|     writing, with genre-adjusted thresholds                        |
|   - 1 deliberately ugly sentence per chapter                       |
|   - THE IMPULSE INSTRUCTION: follow unplanned pulls for 2-3        |
|     paragraphs, keep if better                                     |
|   - Structural diversity enforced (8 types, no consecutive repeat) |
|   - Reading speed design (acceleration + deceleration passages)    |
|   - Scene transition variation (5 types)                           |
|   - Exposition disguises (5 techniques)                            |
|   - Dialogue craft (interruptions, repetition, silence, "said")    |
|                                                                    |
| Output: Chapter + writer self-report (chapter-N-report.md)         |
| Gate: Anti-AI scan + self-report before advancing                  |
| Loop-backs: Outline change -> Phase 2. Research gap -> Phase 1     |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 3.1 -- Dialogue Polish (NEW in V4.1)                        |
|                                                                    |
| Skill:  dialogue-polish                                            |
| Actions:                                                           |
|   - Cover-the-name test on ALL speaking characters                 |
|   - Subtext injection (5 techniques)                               |
|   - Tag/beat ratio optimization                                    |
|   - Dialogue-to-prose ratio check against genre targets            |
|   - Does NOT touch narrative prose                                 |
| Output: Polished chapter (dialogue only)                           |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 3.2 -- Hook Craft (NEW in V4.1)                             |
|                                                                    |
| Skill:  hook-craft                                                 |
| Actions:                                                           |
|   - Score chapter opening (6 hook types) 1-10                      |
|   - Score chapter ending (6 pull types) 1-10                       |
|   - Rewrite if below threshold                                     |
|   - Hook type variety tracking (no consecutive repeats)            |
|   - Binge Test: read all endings + openings in sequence            |
| Output: Hooked chapter + hook-pull scorecard                       |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 3.5 -- Disruption (NEW in V4)                               |
|                                                                    |
| Skill:  chaos-engine (Disruptor)                                   |
| Purpose: Break the chapter's predictability BEFORE evaluation      |
| Actions:                                                           |
|   - Move a scene to an unexpected position                         |
|   - Delete the most expected paragraph, assess if chapter improves |
|   - Insert genuinely irrelevant detail                             |
|   - Break one moment of emotional management (let character lose   |
|     control without narrating it)                                  |
|   - Remove one explanatory clause from a simile (leave it raw)     |
|   - Challenge structural defaults                                  |
|                                                                    |
| This agent introduces WILDNESS into a system that defaults to      |
| control. It reads the writer's self-report and targets the areas   |
| where the writer played it safe.                                   |
|                                                                    |
| Output: Disrupted chapter + disruption report                      |
| Gate: Writer reviews disruptions (can reject individual changes)   |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 3.7 -- Entity Update (NEW in V4.1.1)                       |
|                                                                    |
| Skill:  entity-tracker (UPDATE mode)                               |
| Actions:                                                           |
|   - Read new chapters (not in meta.chapters_tracked)               |
|   - 5 extraction passes: character, temporal, entity, object,      |
|     knowledge flow                                                 |
|   - Merge into YAML (append new, flag conflicts, never overwrite)  |
| Output: Updated ENTITY_STATE.yaml                                  |
| Runs: After every 3-5 chapter batch                                |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 3.8 -- Mechanical Preprocessing (NEW in V4.1)               |
|                                                                    |
| Skill:  mechanical-preprocess                                      |
| Actions:                                                           |
|   - Em-dash census and reduction (genre-adjusted targets)          |
|   - Pattern #11 grep and flagging                                  |
|   - Adverb density check                                           |
|   - Sentence-start repetition detection                            |
|   - Filter word counting (just, really, very, quite, rather)       |
|   - 80% bash / 20% AI review split                                 |
| Output: Cleaned chapter + mechanical-report.md                     |
| Why bash: AI agents hit context limits on 30 chapters. Bash scales.|
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 4 -- Evaluation                                              |
|                                                                    |
| Skills: Genesis Score V3.7 (built into book-genesis)               |
|         beta-reader (5 profiles: Devourer, Critic, Hostile,        |
|           Casual Reader, + DEVOTED READER -- NEW in V4)            |
| Process:                                                           |
|   - Run Genesis Score on manuscript (7 dimensions, genre-adjusted) |
|   - Run beta-reader with 5 profiles including Casual Reader and Devoted Reader        |
|   - THE CASUAL READER GATE (NEW):                                  |
|     "Would a person who picks this up at an airport give it 10     |
|     pages?" If no, the chapter fails regardless of craft scores.   |
|   - "Would You Remember This Tomorrow?" test                       |
|   - Cross-reference: Score weak + readers confirm = real problem   |
|   - Progressive evaluation (per part, not just final)              |
|   - Comp title passage comparison (from Phase 1 research)          |
|   - CVI-Launch calculation for submission readiness                |
|   - Pattern #11 hard check (explanatory extensions)                |
|                                                                    |
| Output: Score per dimension, floor, CVI-Launch, CVI-Legacy,        |
|         top weaknesses/strengths, revision priority                |
| Gate: Floor >= genre threshold (7.0-7.5) to advance               |
|       CVI-Launch >= 7.0 for submission readiness                   |
| Loop-back: Floor below genre threshold -> Phase 5 -> return here   |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 4.5 -- Quality Gate (NEW in V4.1)                           |
|                                                                    |
| Skill:  quality-gate                                               |
| Actions:                                                           |
|   - Auto-loop: evaluate -> synthesize -> dispatch fix -> re-eval   |
|   - Max 3 iterations per chapter                                   |
|   - Regression detection (fix one thing, break another)            |
|   - Near-miss protocol (fails by small margin)                     |
|   - Parallel batch mode with systemic issue detection              |
|   - Escalation report with 4 options for orchestrator              |
| Output: Quality gate report + pass/fail/escalate decision          |
| Gate: Pass to advance. Escalate returns to orchestrator.           |
+------------------------------------+------------------------------+
                                     |
                                     v (if floor below genre threshold)
+-------------------------------------------------------------------+
| PHASE 5 -- Revision                                                |
|                                                                    |
| Skill:  book-editor (NEW in V4)                                    |
|         prose-craft (for prose issues)                              |
|         narrative-foundation (for structural issues)               |
| Process:                                                           |
|   1. Classify each weakness by taxonomy:                           |
|      Type 1 -- Structural (highest priority)                       |
|      Type 2 -- Connective                                          |
|      Type 3 -- Prose                                               |
|      Type 4 -- Factual/Punctual (lowest priority)                  |
|   2. Execute in order (structural first, punctual last)            |
|   3. Genesis Score governs REVISION PRIORITY                       |
|      (weakest dimension gets attention first)                      |
|   4. Verify strengths not degraded by corrections                  |
|   5. Max 3 revision cycles per iteration                           |
|                                                                    |
| Loop-back: Always returns to Phase 4 for re-evaluation             |
| Escalation: 3 cycles without floor improvement -> Phase 2          |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 5.5 -- Entity Update (NEW in V4.1.1)                       |
|                                                                    |
| Skill:  entity-tracker (UPDATE mode)                               |
| Actions:                                                           |
|   - Capture all changes from revision phase                        |
|   - Resolve conflicts where edited text now has single value       |
|   - Update ENTITY_STATE.yaml with revision changes                 |
| Output: Updated ENTITY_STATE.yaml                                  |
+------------------------------------+------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------+
| PHASE 5.6 -- Manuscript Continuity                                 |
|                                                                    |
| Skill:  continuity-guardian (second pass -- full manuscript)        |
| Actions:                                                           |
|   - Full-manuscript audit after all revisions complete              |
|   - 6 audits: character, timeline, information flow, plot, world,  |
|     YAML vs Text Divergence (NEW in V4.1.1)                        |
|   - Reads ENTITY_STATE.yaml for structured validation              |
|   - Catches cross-chapter inconsistencies introduced by revision   |
|   - Grep-based pattern detection for names, dates, descriptions    |
|   - CRITICAL/WARNING/MINOR severity classification                 |
|   - Outputs suggested YAML patches                                 |
| Output: continuity-report-manuscript.md + yaml-patches.md          |
| Gate: No CRITICAL issues before delivery                           |
+------------------------------------+------------------------------+
                                     |
                                     v (when floor >= genre threshold)
+-------------------------------------------------------------------+
| PHASE 6 -- Delivery                                                |
|                                                                    |
| Skills: editorial-package, production-prep                         |
| Produces:                                                          |
|   - Logline (1 sentence)                                           |
|   - Cover synopsis (100 words)                                     |
|   - Editorial synopsis (300 words, reveals ending)                 |
|   - Query letter (personalized)                                    |
|   - Cover brief (with AI generation prompts)                       |
|   - Final proofreading (8 categories, 3 passes)                    |
|   - Formatting for ebook and/or print                              |
|   - CVI-Launch assessment for submission readiness                 |
|   - Final STATE.yaml update                                        |
|                                                                    |
| Gate: CVI-Launch >= 7.0 for editorial submission                   |
| Output: Manuscript + editorial package + formatted files           |
+-------------------------------------------------------------------+
```

---

## The Two Scoring Systems

V4 introduces a critical separation between two measures that V2 conflated:

### Genesis Score -- Governs Revision Priority

The Genesis Score is the craft quality measure. It has 7 dimensions, uses a FLOOR system (score = weakest dimension), and determines what gets revised first.

- If Emotion is 7.0 and Prose is 8.5, Emotion gets revision priority.
- The floor must reach the genre-adjusted threshold (7.0-7.5 depending on genre) before the pipeline can advance to delivery.
- The Genesis Score tells you HOW GOOD the book is.

### CVI (Commercial Viability Index) -- Governs Submission Readiness

CVI is the market measure. It predicts whether the book will sell, not whether it is well-crafted.

- **CVI-Launch** predicts first-year sales. 6 inputs: market timing, comp title freshness, hook strength, platform/audience, pacing score, genre convention compliance.
- **CVI-Legacy** predicts 20-year sales. 5 inputs: re-readability, emotional resonance, shareability, identity effect, cultural vocabulary penetration.

A book can have a Genesis Score of 8.5 (strong craft) but a CVI-Launch of 5.0 (bad market timing, no platform). Or a Genesis Score of 7.5 (decent craft) but a CVI-Launch of 8.0 (perfect market moment, huge audience).

**The Genesis Score tells you to keep revising. The CVI tells you when to stop revising and ship.**

---

## State Management

State is managed via `STATE.yaml` (renamed from `PROJECT_STATE.yaml` in V4 for brevity):

- **STATE.yaml is the source of truth.** Every agent reads it at the start of work and writes to it at the end.
- **CHECK-IN** at the start of every session: reads state, reports progress, verifies consistency.
- **CHECK-OUT** at the end of every session: updates state, logs decisions, manages handoffs.
- **Decision Log**: every significant decision recorded with justification and reversibility.
- **Handoff Tracking**: inter-skill tasks with priority and staleness alerts (>2 sessions).
- **Session Recovery**: if context is lost, STATE.yaml contains everything needed to resume.
- **Chapter Reports**: each chapter's writer self-report and disruption report are tracked.
- **Score History**: full Genesis Score + CVI history with per-dimension evidence.

---

## Quality Gates

| Gate | Where | Condition | Failure Action |
|------|-------|-----------|----------------|
| Direction Approval | Phase 1 -> 1.5 | User approves research direction | Revise research |
| Persona Validation | Phase 1.5 -> 2 | PRIMARY + HOSTILE personas defined | Revise personas |
| Foundation Approval | Phase 2 -> 2.5 | User approves foundation + outline | Revise foundation |
| Voice DNA Approval | Phase 2.5 -> 2.7 | Voice DNA with per-character specs approved | Revise voice DNA |
| Entity State Built | Phase 2.7 -> 2.8 | ENTITY_STATE.yaml created with all foundation entities | Rebuild YAML |
| Outline Continuity | Phase 2.8 -> 3 | No CRITICAL continuity issues | Fix outline |
| Anti-AI Check | Phase 3 (per chapter) | 20-pattern scan passes genre threshold | Revise chapter prose |
| Writer Self-Report | Phase 3 -> 3.1 | Report filed with chaos moments, ugly sentence, anchor | Rewrite chapter |
| Dialogue Test | Phase 3.1 -> 3.2 | Cover-the-name test passes | Polish dialogue |
| Hook Score | Phase 3.2 -> 3.5 | Hook and pull scores above threshold | Rewrite opening/ending |
| Disruption Review | Phase 3.5 -> 3.8 | Writer reviews disruptions | Accept/reject changes |
| Mechanical Clean | Phase 3.8 -> 4 | Pattern counts within genre targets | Re-run mechanical pass |
| Casual Reader Gate | Phase 4 | "Would an airport reader give this 10 pages?" | Revise hook/pacing |
| Memory Test | Phase 4 | "What would the reader remember tomorrow?" | Strengthen anchor |
| Genesis Floor | Phase 4 -> 4.5 | Floor >= genre threshold (7.0-7.5) | Enter quality gate loop |
| Quality Gate | Phase 4.5 -> 5 or 6 | Pass after max 3 iterations | Escalate to orchestrator |
| Entity State Updated | Phase 5.5 -> 5.6 | ENTITY_STATE.yaml reflects all revisions | Re-run entity update |
| Manuscript Continuity | Phase 5.6 -> 6 | No CRITICAL cross-chapter issues | Fix inconsistencies |
| CVI-Launch Gate | Phase 6 | CVI-Launch >= 7.0 | Revise market positioning |

---

## Loop-Back Rules

The pipeline is not linear. These are the sanctioned backward jumps:

| From | To | Trigger |
|------|----|---------|
| Phase 3 (Writing) | Phase 2 (Foundation) | Character evolves beyond outline; outline needs restructuring |
| Phase 3 (Writing) | Phase 1 (Research) | Insufficient data for non-fiction chapter |
| Phase 4 (Evaluation) | Phase 5 (Revision) | Floor below genre threshold (7.0-7.5) |
| Phase 5 (Revision) | Phase 4 (Evaluation) | After every revision cycle (re-evaluate) |
| Phase 5 (Revision) | Phase 2 (Foundation) | 3 revision cycles without floor improvement (structural problem) |
| Phase 6 (Delivery) | Phase 5 (Revision) | CVI-Launch < 7.0 (market positioning issue) |

**Hard rule:** Maximum 3 revision cycles per evaluation round. If the floor does not improve after 3 cycles, the problem is structural -- return to Phase 2.

---

## The Casual Reader Gate

This is V4's most commercially important addition. It was identified as a missing architectural element in the system analysis.

The Casual Reader is not the Devourer (who reads fast and feels everything), the Critic (who analyzes), or the Hostile (who attacks). The Casual Reader is the person who picks up a book at an airport, reads 10 pages, and decides based on vibes. Not craft. Vibes.

The Casual Reader does not care about:
- Thematic depth
- Prose quality
- Character psychology
- Anti-AI compliance

The Casual Reader cares about:
- "Am I curious?"
- "Do I like this person's voice?"
- "Is something happening?"
- "Do I want to know what happens next?"

If the Casual Reader would put the book down, the chapter fails -- regardless of its Genesis Score. This gate exists because pacing is the #2 predictor of commercial success, and a book with 7.5 prose + 9.0 pacing outsells 9.0 prose + 7.5 pacing by 10x.

---

## Skill Interaction Map

```
book-auto (Autonomous Entry Point — NEW in V4.1)
    |  One command, 200 turns, 3 human checkpoints
    v
book-genesis (Orchestrator)
    |
    +-- book-researcher -------> Phase 1 (Research)
    |     Outputs: comp titles, market gaps, bestseller-dna.md,
    |              comp title passages for evaluator
    |
    +-- reader-persona --------> Phase 1.5 (Reader Personas — NEW)
    |     Outputs: reader-personas.md
    |     Reads: research report
    |
    +-- narrative-foundation --> Phase 2 (Foundation)
    |     Outputs: foundation.md, outline.md, voice-bank/
    |     Reads: research report, comp titles, reader-personas.md
    |
    +-- voice-fingerprint -----> Phase 2.5 (Voice DNA — NEW)
    |     Outputs: voice-dna.md
    |     Reads: foundation.md, voice-bank/
    |
    +-- entity-tracker -------> Phase 2.7 (Entity Tracking — NEW in V4.1.1)
    |     Outputs: ENTITY_STATE.yaml
    |     Reads: foundation.md, outline.md
    |
    +-- continuity-guardian ---> Phase 2.8 (Outline Continuity)
    |     Outputs: continuity-report-outline.md
    |     Reads: outline.md, foundation.md, ENTITY_STATE.yaml
    |
    +-- prose-craft -----------> Phase 3 (Writing)
    |     Outputs: chapter-N.md, chapter-N-report.md
    |     Reads: foundation.md, outline.md, voice-dna.md,
    |            reader-personas.md, previous chapter, bestseller-dna.md
    |
    +-- dialogue-polish -------> Phase 3.1 (Dialogue — NEW)
    |     Outputs: polished chapter (dialogue only)
    |     Reads: chapter, voice-dna.md
    |
    +-- hook-craft ------------> Phase 3.2 (Hooks & Pulls — NEW)
    |     Outputs: hooked chapter + hook-pull scorecard
    |     Reads: chapter, outline.md
    |
    +-- chaos-engine ----------> Phase 3.5 (Disruption)
    |     Outputs: disrupted chapter, disruption report
    |     Reads: chapter, writer self-report, ENTITY_STATE.yaml
    |
    +-- entity-tracker -------> Phase 3.7 (Entity Update — NEW in V4.1.1)
    |     Outputs: updated ENTITY_STATE.yaml
    |     Reads: new chapters, existing ENTITY_STATE.yaml
    |
    +-- mechanical-preprocess -> Phase 3.8 (Mechanical Cleanup — NEW)
    |     Outputs: cleaned chapter + mechanical-report.md
    |     Reads: chapter
    |
    +-- beta-reader -----------> Phase 4 (Evaluation)
    |     Outputs: 5-reader report + cross-diagnosis
    |     Reads: chapter or full manuscript, reader-personas.md
    |
    +-- quality-gate ----------> Phase 4.5 (Quality Gate — NEW)
    |     Outputs: quality gate report + pass/fail/escalate
    |     Reads: evaluation report, Genesis Score
    |
    +-- book-editor -----------> Phase 5 (Revision)
    |     Outputs: revision plan, revised chapters
    |     Reads: evaluation report, Genesis Score, manuscript
    |
    +-- entity-tracker -------> Phase 5.5 (Entity Update — NEW in V4.1.1)
    |     Outputs: updated ENTITY_STATE.yaml
    |     Reads: revised chapters, existing ENTITY_STATE.yaml
    |
    +-- continuity-guardian ---> Phase 5.6 (Manuscript Continuity)
    |     Outputs: continuity-report-manuscript.md + yaml-patches.md
    |     Reads: full revised manuscript, ENTITY_STATE.yaml
    |
    +-- editorial-package -----> Phase 6 (Delivery)
    +-- production-prep -------> Phase 6 (Delivery)
    |
    +-- series-architect ------> Multi-volume projects
```

---

## Autonomous Mode (NEW in V4.1)

V4.1 introduces `/book-auto`, which replaces 150+ manual skill invocations with a single command. The `book-auto` skill dispatches the `book-genesis` orchestrator agent with 200 turns of autonomous execution.

**3 Human Checkpoints:**
1. **Foundation checkpoint** (after Phase 2.8): User approves research direction, reader personas, foundation, outline, voice DNA, entity state, and continuity report before any writing begins.
2. **Manuscript checkpoint** (after Phase 5.6): User reviews the complete revised manuscript, entity state, and continuity report before delivery packaging begins.
3. **Delivery checkpoint** (after Phase 6): User approves the final editorial package before submission.

Everything between checkpoints runs automatically: writing, dialogue polish, hook craft, disruption, mechanical preprocessing, evaluation, quality gate loops, revision, and continuity audits.

**Invocation:** `/book-auto [language] [idea]`

---

## File Structure (V4)

```
project/
  STATE.yaml                    # Source of truth
  ENTITY_STATE.yaml             # Persistent entity tracking (NEW in V4.1.1)
  foundation/
    foundation.md               # Characters, chaos profiles, theme, engagement type
    outline.md                  # Chapter outline with structural approaches
    reader-personas.md          # 3-5 reader personas (NEW in V4.1)
    voice-dna.md                # Per-character voice specs (NEW in V4.1)
    voice-bank/
      samples.md                # 10-15 voice samples
      voice-under-pressure.md   # 3+ samples of voice failing
      irrelevant-thoughts.md    # Character-specific irrelevant thoughts
    continuity/
      continuity-report-outline.md     # Outline-stage audit (NEW in V4.1)
      continuity-report-manuscript.md  # Full manuscript audit (NEW in V4.1)
  manuscript/
    chapters/
      chapter-01.md
      chapter-01-report.md      # Writer self-report
      chapter-02.md
      chapter-02-report.md
      ...
  research/
    comp-titles.md
    bestseller-dna.md           # Prose rules extracted from genre leaders
    market-analysis.md
    comp-passages/              # Actual passages from comp titles
  evaluations/
    genesis-score-v1.md
    beta-reader-v1.md
    cvi-launch.md
    cvi-legacy.md
    ...
  editorial/
    logline.md
    synopsis-cover.md
    synopsis-editorial.md
    query-letter.md
    cover-brief.md
  export/
    manuscript-final.md
    ...
```
