> **Historical material.** This page describes earlier experiments or proposals. Its scores, benchmarks, features and demos are not claims about Imagination Edition. Use the [current README](../README.md) and [validation record](../docs/validation.md) for the beta.

# Skills Reference -- Book Genesis V4

> Current note (2026-09-02): this is the legacy V4/V5 skill reference. Most of the skills described below now live in `legacy/skills/` (moved by ADR 0001, not deleted). The canonical path is the runner: see `docs/runner.md`. Skills still under `skills/` (bestseller studio, swarm panel, literary agent panel, copy-editing, humanizer, prose-craft and friends) remain usable standalone.

Market-level add-ons live beside the universal core. The current public positioning is the **Book Genesis Bestseller Skills Suite**:

- `skills/book-bestseller-studio/`: commercial-readiness umbrella for Book Genesis runs.
- `skills/book-swarm-panel/`: MiroFish-style clean-room simulated reader swarms, public-opinion diagnostics, niche-risk scouting, and revision tickets.
- `skills/literary-agent-panel/`: simulated literary agent, acquiring editor, bookseller, and target-reader review.
- `skills/copy-editing/`: prose clarity, grammar, repetition, consistency, and final polish.
- `skills/humanizer/`: voice texture, cadence variation, emotional specificity, and anti-mechanical prose.

Book Bestseller Studio includes `references/agent-registry.yaml`, a specialist team covering market research, worldbuilding, character architecture, theme, plot, pacing, prose writing, continuity, swarm, adversarial audit, revision, scoring, package, viral framing, and launch.

For the new public suite overview, see [`docs/bestseller-skills-suite.md`](bestseller-skills-suite.md).

Book Genesis V4 contains **19 skills** organized into a 17-phase pipeline (with sub-phases). Each skill is a standalone specialist that also works as part of the orchestrated pipeline. V4 adds 3 skills (chaos-engine, book-editor, book-researcher). V4.1 adds skills focused on automation, voice quality, and scaling. V4.1.1 adds entity-tracker for persistent state.

---

## Pipeline Skills

### 1. book-genesis (Orchestrator)

**Phase:** All phases
**Role:** The brain of the system. Coordinates all 12 skills through 7 phases with hard quality gates.

**Key features:**
- 7-phase pipeline: Research -> Foundation -> Writing -> Disruption -> Evaluation -> Revision -> Delivery
- Genesis Score V3.7: 7 dimensions, FLOOR system, genre-adjusted profiles
- CVI-Launch and CVI-Legacy: commercial viability separate from craft quality
- Anti-inflation protocol: 10 rules including external benchmark anchoring
- Casual Reader Gate: would an airport reader give this 10 pages?
- Loop-back rules with escalation paths
- Genre-specific prose targets and anti-AI thresholds

**What changed from V2:** Added Phase 3.5 (Disruption), CVI system, Casual Reader Gate, genre-adjusted scoring, engagement types, 20-pattern anti-AI (up from 10), emotional anchors replacing numerical curves.

---

### 2. narrative-foundation (Architect)

**Phase:** 2 (Foundation)

Builds the complete narrative foundation. Consolidates character-forge, emotion-engineer, and theme-weaver from V1 into one integrated skill.

**Part 1 -- Characters:** 7 layers of depth per character (wound, lie, conscious desire, unconscious need, contradictions, voice, transformation arc).

V4 additions:
- **Chaos profiles** for each character: irrelevant obsessions, cognitive distortions, unprompted memories, failed emotional management patterns
- **Voice-under-pressure** specification: how the voice changes when the character is stressed (fragments, repetition, tense changes)
- **Composure calibration**: characters can be authentically composed (subtle chaos) vs. suppressing chaos (visible cracks)

**Part 1B -- Voice Construction:** Method for building authentic voice from author samples or literary references. Voice bank requires 10-15 samples INCLUDING 3+ samples of voice failing under pressure.

**Part 2 -- Pacing:** Chapter/paragraph/sentence rhythm management. Genre-specific density guidelines.

**Part 3 -- Emotional System (V4 overhaul):**
- Emotional ANCHORS per chapter (specific image/moment) replacing numerical curves (4/10, 7/10)
- Emotional SURPRISES per chapter (where the expected emotion should be wrong)
- 6 emotional techniques beyond physical sensation + metaphor: contradiction, understatement, dramatic irony, wrong reaction, accumulated mundane detail, body rebels
- "Would You Remember This Tomorrow?" anchor definition

**Part 4 -- Theme:** Theme as QUESTION. 4 levels of weaving (macro, medium, micro, nano). Theme is allowed to RECEDE in some chapters.

**Part 5 -- Engagement and Commercial (NEW):**
- Engagement type ranking (primary/secondary/tertiary from 5 types)
- Re-read architecture: planned details that gain meaning after the ending
- Cultural vocabulary: branded terms for reader adoption
- Identity effect planning: moments that make the reader feel something about themselves

**Part 6 -- Outline Enrichment (NEW):**
- Structural approach per chapter (1 of 8 types, no consecutive repeats)
- Opening strategy for Chapter 1 (voice bomb, in medias res, wrong emotion, confession, question, ordinary made strange, failure)
- Value shift per chapter
- Chapter-ending hook type

---

### 3. prose-craft (Writer)

**Phase:** 3 (Writing)

The writing agent. Produces one chapter at a time. Follows the outline but is ALLOWED to deviate when the text wants to go somewhere the outline did not anticipate.

**Voice Inhabitation Protocol (NEW):** Before writing a single word:
1. Read ALL project files
2. Write a 200-300 word freewrite AS the character (discarded -- goes to /dev/null)
3. Only then begin the chapter

**6 Flexible Obligations** (one allowed to take a backseat per chapter):
1. Voice (must change under pressure)
2. Substance (30-40% texture details with no thematic resonance)
3. Emotional Anchor (build toward specific image/moment)
4. Theme (allowed to recede)
5. Device (if applicable)
6. Pacing (value shift, chapter hook, speed variation, vulnerability before competence)

**Character Chaos (Mandatory):**
- Irrelevant thought (1-2 sentences, no narrative justification)
- Cognitive distortion in action
- Unprompted memory at the wrong time
- Failed emotional management
- Secondary character chaos (their own moment, not about protagonist)

**Anti-AI Protocol:** 20 patterns internalized BEFORE writing (not scan-after). Genre-adjusted thresholds.

**The Impulse Instruction:** After writing as planned, follow unplanned pulls for 2-3 paragraphs. Keep if better.

**Mandatory Ugly Sentence:** One deliberately rough sentence per chapter in a quiet moment.

**Structural Diversity:** 8 chapter structures (chronological, reverse chronological, fragmented/mosaic, essayistic, spiral, parallel, epistolary/documentary, stream of consciousness). No consecutive repeats.

**Reading Speed Design:** 1-2 acceleration passages and 1-2 deceleration passages per chapter.

**Scene Transitions:** 5 types (hard cut, sensory bridge, dialogue bridge, time compression, emotional carry). Vary across chapters.

**Exposition Disguises:** 5 techniques (conflict delivery, discovery delivery, wrong delivery, cost delivery, incidental delivery).

**Output:** chapter-N.md + chapter-N-report.md (self-report with chaos moments, ugly sentence, impulse deviations, anti-AI scan results).

Optionally reads ENTITY_STATE.yaml to verify character knowledge before writing dialogue (V4.1.1+).

---

### 4. chaos-engine (Disruptor) -- NEW in V4

**Phase:** 3.5 (Disruption)

The agent that introduces WILDNESS into a system that defaults to control. Operates AFTER the writer and BEFORE the evaluator. Its only job is to break the chapter's predictability.

**Actions:**
- Move a scene to an unexpected position
- Delete the most expected paragraph and assess if the chapter improves
- Insert a genuinely irrelevant detail
- Break one moment of emotional management (let a character lose control without narrating it)
- Remove one explanatory clause from a simile and leave it raw
- Challenge the structural default (if the chapter follows the Graduated Reveal pattern, propose an alternative)
- Target areas where the writer's self-report indicates "played it safe"

**Why it exists:** The system analysis found that all 5 test books shared identical predictability: competent professional encounters anomaly, escalates, closes on tension. Every chapter was under authorial control at all times. The chaos-engine is the mechanism for controlled unpredictability.

**Output:** Disrupted chapter + disruption report.

**Gate:** Writer reviews all disruptions and can reject individual changes.

Optionally reads character traits from ENTITY_STATE.yaml for coherent chaos injection (V4.1.1+).

---

### 5. beta-reader (Evaluator)

**Phase:** 4 (Evaluation)

Simulates 4 radically different readers evaluating the manuscript. V4 adds the Casual Reader profile.

**The Devourer:** Reads fast, feels everything, zero tolerance for dragging. Reports where they would stop reading.

**The Critic:** Literary analysis lens. Hunts for originality, thematic depth, prose quality, coherence.

**The Hostile:** Did not want to read this. Actively seeks flaws, manipulation, AI smell.

**The Casual Reader (NEW):** The person who picks up the book at an airport and gives it 10 pages. Does not analyze. Decides on vibes. If the Casual Reader puts it down, the chapter fails regardless of craft scores. This is the single best predictor of whether the book sells.

**Cross-diagnosis:** 3/3 agree = critical. 2/3 = real problem. 1/1 = investigate. Hostile praises = exceptional. Casual Reader abandons = commercial failure regardless of other scores.

Optionally references ENTITY_STATE.yaml for evidence-based coherence scoring (V4.1.1+).

---

### 6. book-editor (Editor) -- NEW in V4

**Phase:** 5 (Revision)

Dedicated revision agent. V2 relied on the writer to revise their own work, which produced diminishing returns. The editor is a separate agent with a different perspective.

**Revision Taxonomy (4 types, priority order):**
1. **Structural** -- Affects the skeleton. Arcs that don't close, themes that don't appear, parallel chapters.
2. **Connective** -- How parts link. Weak transitions, logic gaps, emotional jumps.
3. **Prose** -- How each section sounds. Voice drift, dialogue without subtext, AI patterns.
4. **Factual/Punctual** -- Isolated errors. Incorrect data, name inconsistencies, typos.

**Key principle:** Genesis Score governs revision priority. The weakest dimension gets attention first. Always revise structural before connective before prose before factual.

**Output:** Revision plan with specific changes per chapter + revised chapters.

Optionally reads suggested_patches from continuity-guardian and confirms conflicts resolved (V4.1.1+).

---

### 7. book-researcher (Researcher) -- NEW in V4

**Phase:** 1 (Research)

Dedicated research agent. V2 combined research into the orchestrator, producing shallow market analysis. The researcher is a deep specialist.

**Delivers:**
- Top 10 books in niche (last 5 years) with sales data
- Market gaps and white space identification
- 3-5 comp titles with detailed positioning analysis
- **bestseller-dna.md**: Extracted prose patterns, pacing structures, hook types, and emotional techniques from genre leaders
- **Comp title passages**: 3-5 actual excerpts from published bestsellers for the evaluator to benchmark against
- Genre convention checklist (word count, structure, reader expectations)
- Cultural moment assessment (is this topic trending?)

**Why it exists:** The system analysis found that the evaluator had no comp title TEXT to compare against. It was told to compare with published works but had no reference material. The researcher provides that material.

---

### 8. editorial-package (Packager)

**Phase:** 6 (Delivery)

Everything the manuscript needs to reach the market.

**Part 1 -- Synopses:** 3 formats -- logline (~25 words), cover synopsis (~100 words), editorial synopsis (~300 words, reveals ending).

**Part 2 -- Query Letter:** 5 mandatory elements. Personalization protocol per agent/publisher.

**Part 3 -- Cover Brief:** Visual positioning, emotional concept, color palette, typography, AI generation prompts.

---

### 9. production-prep (Production)

**Phase:** 6 (Delivery)

Final technical preparation.

**Part 1 -- Proofreading:** 8 error categories (spelling, punctuation, agreement, repetition, factual, verb tense, formatting, invisible errors). 3-pass methodology.

**Part 2 -- Formatting:** Complete guidelines for ebook (EPUB) and print (POD). Checklists for both formats.

---

## Support Skills

### 10. series-architect (Series)

**Phase:** Independent (multi-volume projects)

Builds and maintains the series bible.

**Delivers:** Series premise, protagonist transformation arc across all volumes, volume map, canonical worldbuilding, character management, inter-volume hooks, consistency checklist, canonical glossary.

**When to use:** Before writing Volume 2+. When a plot point could create a future contradiction. When reviewing volume endings.

Book 1 ENTITY_STATE.yaml can feed book 2 tracking for cross-volume continuity (V4.1.1+).

---

## Skill Consolidation Map (V1 -> V2 -> V4 -> V4.1.1)

| V1 Skills (15) | V2 Skills (9) | V4 Skills (12) | V4.1.1 Skills (21) |
|----------------|---------------|----------------|-------------------|
| character-forge + theme-weaver + emotion-engineer | narrative-foundation | narrative-foundation | narrative-foundation (chaos profiles, engagement types, re-read architecture) |
| hook-crafter + dialogue-master | prose-craft | prose-craft | prose-craft (voice inhabitation, impulse instruction, 20 anti-AI, reads ENTITY_STATE.yaml) |
| beta-reader-sim (5 profiles) | beta-reader (3 profiles) | beta-reader (4 profiles) | beta-reader (reads ENTITY_STATE.yaml) |
| -- | -- | **chaos-engine** | chaos-engine (reads ENTITY_STATE.yaml) |
| -- | -- | **book-editor** | book-editor (reads suggested_patches) |
| -- | -- | **book-researcher** | book-researcher |
| synopsis-writer + cover-brief + query-letter | editorial-package | editorial-package | editorial-package (EN) |
| proofreader + book-formatter | production-prep | production-prep | production-prep (EN) |
| book-genesis | book-genesis | book-genesis | book-genesis (17 phases, language-adaptive) |
| series-architect | series-architect | series-architect | series-architect (cross-volume ENTITY_STATE) |
| -- | -- | -- | **reader-persona** (V4.1) |
| -- | -- | -- | **voice-fingerprint** (V4.1) |
| -- | -- | -- | **continuity-guardian** (V4.1, +Audit 6) |
| -- | -- | -- | **dialogue-polish** (V4.1, reads ENTITY_STATE.yaml) |
| -- | -- | -- | **hook-craft** (V4.1, reads ENTITY_STATE.yaml) |
| -- | -- | -- | **mechanical-preprocess** (V4.1) |
| -- | -- | -- | **quality-gate** (V4.1) |
| -- | -- | -- | **book-auto** (V4.1) |
| -- | -- | -- | **entity-tracker** (V4.1.1) |

---

## V4.1 Skills

### 13. reader-persona (Reader Personas)
**Phase:** 1.5
**Role:** Builds 3-5 reader personas that drive writer decisions, evaluator simulation, and packager targeting.
**Key features:**
- PRIMARY persona (drives writing when conflicts arise)
- HOSTILE persona (drives evaluator's toughest simulation)
- STRETCH persona (adjacent-genre reader)
- Each persona has: reading psychology, deal-breakers, emotional triggers, discovery channels, comp titles
- Downstream consumers: writer (voice calibration), evaluator (reader simulation), packager (marketing targeting), chaos-engine (who to challenge vs protect)

### 14. voice-fingerprint (Voice DNA)
**Phase:** 2.5
**Role:** Creates prescriptive Voice DNA document. Per-character voice specs that the writer MUST follow.
**Key features:**
- Global narrative voice profile (POV, sentence architecture, metaphor domain, prose register)
- Per-character voice cards: speech patterns, syntax fingerprint, metaphor source, voice-under-pressure (3 stress levels)
- Voice differentiation matrix (minimum 3 distinguishing markers per character pair)
- Anti-pattern budget (em-dash limits, Pattern #11 budget per chapter)
- Cover-the-name test definition per character

### 15. continuity-guardian (Continuity)
**Phase:** 2.8 (outline) + 5.6 (full manuscript)
**Role:** Cross-manuscript consistency auditor. Catches errors no individual chapter writer can see.
**Key features:**
- 6 systematic audits: character consistency, timeline validation, information flow, plot threads, world rules, YAML vs Text Divergence (V4.1.1)
- 3 modes: batch (every 3-5 chapters), full-manuscript, post-revision
- Grep-based pattern detection for names, dates, descriptions
- CRITICAL/WARNING/MINOR severity classification
- Now reads ENTITY_STATE.yaml when available (V4.1.1) -- falls back to V4 behavior if absent
- Outputs suggested YAML patches alongside markdown report

### 16. dialogue-polish (Dialogue)
**Phase:** 3.1
**Role:** Dialogue-only editing pass. Ensures distinct character voices in speech.
**Key features:**
- Cover-the-name test on ALL speaking characters
- Subtext injection (5 techniques)
- Tag/beat ratio optimization
- Dialogue-to-prose ratio check against genre targets
- Does NOT touch narrative prose
- Optionally validates voice markers against ENTITY_STATE.yaml (V4.1.1+)

### 17. hook-craft (Hooks & Pulls)
**Phase:** 3.2
**Role:** Chapter openings must hook, endings must pull. Prevents the reader from putting the book down.
**Key features:**
- 6 hook types (in medias res, question, sensory, voice, contrast, ticking clock)
- 6 pull types (cliffhanger, revelation, question plant, gut punch, ominous promise, decision point)
- Scoring 1-10 with rewrite if below threshold
- Hook type variety tracking (no consecutive repeats)
- Binge Test: read all endings + openings in sequence to check momentum
- Optionally queries ENTITY_STATE.yaml for chekhov_open objects (V4.1.1+)

### 18. mechanical-preprocess (Mechanical Cleanup)
**Phase:** 3.8
**Role:** Bash-first pattern cleanup. Scales to any manuscript size.
**Key features:**
- Em-dash census and reduction (genre-adjusted targets)
- Pattern #11 grep and flagging
- Adverb density check
- Sentence-start repetition detection
- Filter word counting (just, really, very, quite, rather, somewhat)
- 80% bash / 20% AI review split

### 19. quality-gate (Quality Gate)
**Phase:** 4.5
**Role:** Automated evaluate→fix→re-evaluate loop. Eliminates manual babysitting.
**Key features:**
- Auto-loop: evaluate, synthesize feedback, dispatch fix, re-evaluate
- Max 3 iterations per chapter
- Regression detection (fix one thing, break another)
- Near-miss protocol (fails by small margin)
- Parallel batch mode with systemic issue detection
- Escalation report with 4 options for orchestrator

### 20. book-auto (Autonomous Entry Point)
**Phase:** All
**Role:** One command, one book. Dispatches the book-orchestrator agent.
**Key features:**
- Single invocation: `/book-auto [language] [idea]`
- 200-turn autonomous execution
- 3 human checkpoints (foundation, manuscript, delivery)
- Zero manual skill invocation between checkpoints

---

## V4.1.1 Skills

### 21. entity-tracker (Entity State)
**Phase:** 2.7 (BUILD) + 3.7 / 5.5 (UPDATE)
**Role:** Builds and maintains ENTITY_STATE.yaml -- persistent, structured state for all manuscript entities.
**Key features:**
- Two modes: BUILD (from foundation/outline) and UPDATE (incremental after chapter batches)
- Tracks: characters (physical, traits, knowledge, location log), locations, timeline, objects (Chekhov tracking), world rules, organizations
- 5 extraction passes per chapter: character scan, temporal scan, entity scan, object scan, knowledge flow
- Conflict detection without resolution (flags contradictions as UNRESOLVED)
- Source-mandatory: every entry requires chapter:paragraph citation
- Consumed by: continuity-guardian (audits), prose-craft (knowledge check), dialogue-polish (voice markers), book-editor (patches), chaos-engine (trait-based chaos), hook-craft (Chekhov objects), beta-reader (coherence data)
