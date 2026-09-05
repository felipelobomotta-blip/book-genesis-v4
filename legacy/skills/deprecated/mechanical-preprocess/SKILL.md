---
name: mechanical-preprocess
description: Bash-first mechanical pattern cleanup pipeline — handles em-dash removal, forbidden words, and repetitive structures at scale BEFORE AI agents touch the text. Processes 30+ chapters efficiently.
---

# Mechanical Preprocess

## PURPOSE

AI agents are bad at processing entire manuscripts for mechanical fixes. Context windows overflow, attention drifts, and the agent "forgets" the rules by chapter 15. This skill solves that by splitting the work:

- **Bash handles the 80%** — pattern matching, counting, safe replacements
- **AI handles the 20%** — judgment calls on ambiguous cases, reviewing diffs

This is the ONLY skill in the pipeline that uses bash scripting as its primary tool. It exists because some problems are engineering problems, not language problems.

## WHEN TO RUN

- **After:** All chapters have been through prose-craft (complete draft exists)
- **Before:** dialogue-polish, chaos-engine, or any AI-based editing pass
- **Trigger:** Orchestrator calls this once when the full manuscript draft is ready
- **Re-run:** After any major rewrite pass that may reintroduce mechanical patterns

## REQUIRED INPUTS

1. **Chapter files** — all chapter drafts in `chapters/` directory (e.g., `chapters/chapter-01.md` through `chapters/chapter-[N].md`)
2. **voice-dna.md** — for:
   - Forbidden word list
   - Em-dash policy (max per chapter, allowed contexts)
   - Any other mechanical rules (e.g., max semicolons per chapter, banned constructions)
3. **foundation.md** — for genre context (affects which patterns are acceptable)

## PROCESS

### PHASE 1: SCAN (Pure bash -- no AI)

Run these scans against every chapter file. All commands use standard Unix tools (grep, wc, awk, sed).

**1.1 Em-Dash Census**

```bash
# Count em-dashes per chapter (both spaced and unspaced variants)
for f in chapters/chapter-*.md; do
  echo "$(basename $f): $(grep -oP '(\x{2014}| — )' "$f" | wc -l) em-dashes"
done
```

Categorize each em-dash by context:
- **Independent clause separator** — `[complete sentence] — [complete sentence]` (TARGET FOR REMOVAL)
- **Parenthetical aside** — `word — aside — continuation` (TARGET: convert to commas or restructure)
- **Dialogue interruption** — `"I was going to—"` (KEEP — this is correct usage)
- **List/appositive** — `three things — money, power, fame — were gone` (EVALUATE case by case)

**1.2 Pattern #11 Census (Formulaic Constructions)**

```bash
# "not because X but because Y"
grep -cnP 'not because.*but because' chapters/chapter-*.md

# "the kind of X that Y"
grep -cnP 'the kind of \w+ that' chapters/chapter-*.md

# "not as X but as Y"
grep -cnP 'not as \w+ but as' chapters/chapter-*.md

# "there was something X about Y"
grep -cnP 'there was something \w+ about' chapters/chapter-*.md

# "it was the sort of X that Y"
grep -cnP 'it was the (sort|kind|type) of' chapters/chapter-*.md

# "as if X were Y" (excessive simile construction)
grep -cnP 'as if .{5,40} were' chapters/chapter-*.md

# Doubled constructions "X and X" where both are abstract
grep -cnP '(grief|loss|pain|joy|love|fear|hope|shame|guilt|rage) and (grief|loss|pain|joy|love|fear|hope|shame|guilt|rage)' chapters/chapter-*.md
```

**1.3 Forbidden Word Census**

Extract the forbidden word list from voice-dna.md and scan:

```bash
# For each forbidden word in the list
for word in "palpable" "tangible" "visceral" "whilst" "gaze" "orbs" "ministrations" "utilize" "plethora" "myriad" "ubiquitous" "dichotomy" "juxtaposition" "paradigm" "trajectory"; do
  echo "--- $word ---"
  grep -cnP "\b${word}\b" chapters/chapter-*.md
done
```

Note: The actual forbidden word list comes from voice-dna.md. The list above is a default fallback. Always prioritize the project-specific list.

**1.4 Repetition Scan**

```bash
# Sentence-start repetition: same first word in consecutive sentences
# (catches "She did X. She did Y. She did Z." patterns)
# Extract first word of each sentence per chapter
for f in chapters/chapter-*.md; do
  grep -oP '(?<=\. |^)[A-Z][a-z]+' "$f" | uniq -cd | sort -rn | head -20
done

# Paragraph-start repetition
for f in chapters/chapter-*.md; do
  grep -oP '(?<=\n\n)[A-Z][a-z]+' "$f" | uniq -cd | sort -rn | head -10
done

# Word frequency outliers (words appearing 3x+ per 1000 words beyond normal frequency)
for f in chapters/chapter-*.md; do
  total=$(wc -w < "$f")
  echo "=== $(basename $f) ($total words) ==="
  tr '[:upper:]' '[:lower:]' < "$f" | tr -cs '[:alpha:]' '\n' | sort | uniq -c | sort -rn | \
    awk -v total="$total" '$1 > (total/1000)*3 && length($2) > 4 {print}'
done
```

**1.5 Adverb Density**

```bash
# Count -ly adverbs per chapter
for f in chapters/chapter-*.md; do
  total=$(wc -w < "$f")
  adverbs=$(grep -oP '\b\w+ly\b' "$f" | wc -l)
  echo "$(basename $f): $adverbs adverbs in $total words ($(echo "scale=1; $adverbs*1000/$total" | bc)/1000 words)"
done
```

Target: fewer than 15 adverbs per 1000 words for literary fiction. Adjust per genre.

**1.6 Scan Report**

Compile all counts into `evaluations/mechanical-scan-report.md`:

```markdown
# Mechanical Scan Report

## Em-Dash Count
| Chapter | Total | Clause Sep | Parenthetical | Dialogue | Other |
|---------|-------|------------|---------------|----------|-------|
| ch-01   | 14    | 8          | 4             | 2        | 0     |

## Pattern #11 Count
| Chapter | not-because | kind-of-that | not-as-but-as | something-about | sort-of | as-if-were | doubled-abstract |
|---------|-------------|-------------|---------------|-----------------|---------|------------|-----------------|
| ch-01   | 2           | 1           | 0             | 3               | 1       | 4          | 0               |

## Forbidden Words
| Word       | ch-01 | ch-02 | ... | Total |
|------------|-------|-------|-----|-------|
| palpable   | 1     | 0     |     | 1     |

## Repetition Flags
[per chapter list of repeated sentence starts and high-frequency words]

## Adverb Density
| Chapter | Adverbs | Words | Rate/1000 | Status    |
|---------|---------|-------|-----------|-----------|
| ch-01   | 32      | 3200  | 10.0      | OK        |
| ch-05   | 58      | 3100  | 18.7      | OVER      |

## Summary
- Total em-dashes needing removal: [N]
- Total Pattern #11 instances: [N]
- Total forbidden words: [N]
- Chapters with adverb overuse: [list]
```

### PHASE 2: MECHANICAL REPLACE (Bash sed/awk -- safe patterns only)

Only replace patterns that are ALWAYS wrong. If there is ANY ambiguity, leave it for Phase 3.

**2.1 Safe Em-Dash Replacements**

Target: em-dashes between two independent clauses where a period is always better.

```bash
# Pattern: [sentence ending word] — [Capital letter beginning new sentence]
# This is almost always an independent clause separator
sed -E 's/([a-z]+[.!?]?) — ([A-Z])/\1. \2/g'
```

Do NOT auto-replace:
- Em-dashes in dialogue (between quotation marks)
- Em-dashes that create parenthetical asides (paired dashes)
- Em-dashes after fragments (not independent clauses)

**2.2 Safe Forbidden Word Replacements**

Only replace words that have a SINGLE obvious substitute:
- "utilize" -> "use"
- "whilst" -> "while"
- "upon" -> "on" (in most contexts)
- "commence" -> "begin" or "start"
- "endeavor" -> "try"

Do NOT auto-replace words that need context to choose the right substitute (e.g., "palpable" could become "obvious," "thick," "heavy," "unmistakable" depending on context).

**2.3 Safe Structural Fixes**

```bash
# Double spaces -> single space
sed 's/  / /g'

# Straight quotes -> curly quotes (if project uses curly)
# Multiple consecutive blank lines -> two blank lines max
sed '/^$/N;/^\n$/d'
```

**2.4 Diff Generation**

For EVERY change, generate a diff:

```bash
diff -u chapters/chapter-01.md chapters/chapter-01.md.cleaned > diffs/chapter-01.diff
```

### PHASE 3: AI QUALITY REVIEW (Agent reviews diffs only)

This is where the AI agent enters. It does NOT read full chapters. It reads ONLY the diffs from Phase 2.

**3.1 Diff Review Instructions for AI Agent**

For each diff file:
1. Read the before/after context (3 lines surrounding each change)
2. For each change, classify:
   - `APPROVE` — change is correct and improves the text
   - `REVERT` — change damaged meaning, rhythm, or voice
   - `MODIFY` — change direction is right but execution needs adjustment (provide the correct version)
3. For `REVERT` changes, restore the original text
4. For `MODIFY` changes, apply the agent's corrected version

**3.2 Ambiguous Pattern Review**

The AI agent also receives the list of patterns that bash COULD NOT safely replace:
- Em-dashes in ambiguous contexts
- Forbidden words that need context-dependent substitutes
- Pattern #11 instances (these almost always need creative rewriting, not mechanical replacement)

For each ambiguous item, the agent:
1. Reads the surrounding paragraph (not the full chapter)
2. Decides: fix, leave, or flag for Writer attention
3. Applies fixes or adds to the manual review list

**3.3 Adverb Review**

For chapters flagged OVER on adverb density:
- Agent reviews adverbs in context
- Removes adverbs that weaken the verb ("walked slowly" -> "shuffled")
- Keeps adverbs that are genuinely necessary or part of character voice
- Target: bring density below threshold

### PHASE 4: APPLY AND REPORT

**4.1 Apply Approved Changes**

```bash
# For each chapter with approved changes
patch chapters/chapter-01.md < diffs/chapter-01.approved.diff
```

**4.2 Final Report**

Save to `evaluations/mechanical-preprocess-report.md`:

```markdown
# Mechanical Preprocess Report

## Overview
- **Chapters processed:** [N]
- **Total changes proposed:** [N]
- **Approved:** [N] ([%])
- **Reverted:** [N] ([%])
- **Modified:** [N] ([%])
- **Remaining manual items:** [N]

## Per-Chapter Results
### Chapter [N]
- Em-dashes: [before] -> [after] (removed [N])
- Pattern #11: [before] -> [after] (rewritten [N])
- Forbidden words: [before] -> [after] (replaced [N])
- Adverbs: [before rate] -> [after rate]
- Manual items remaining: [list]

## Before/After Totals
| Metric              | Before | After  | Reduction |
|---------------------|--------|--------|-----------|
| Em-dashes           | [N]    | [N]    | [%]       |
| Pattern #11         | [N]    | [N]    | [%]       |
| Forbidden words     | [N]    | [N]    | [%]       |
| Avg adverb rate     | [N]    | [N]    | [%]       |

## Manual Review Queue
Items that need Writer or Editor judgment:
1. [Chapter N, line ~X]: [description of issue]
```

## RULES

1. **Bash first, AI second.** Never send a full chapter to the AI agent for mechanical fixes. The scan and safe-replace phases MUST run in bash.
2. **Safe means SAFE.** If a replacement could EVER be wrong in context, it is not safe. Move it to Phase 3.
3. **Preserve voice.** Mechanical cleanup must not flatten character voice. If a "forbidden word" is part of a character's speech pattern (defined in voice-dna.md), it is NOT forbidden in that character's dialogue.
4. **Diffs, not full text.** The AI agent in Phase 3 reviews diffs with surrounding context. Never feed it full chapters for mechanical review — that is how attention drift causes missed fixes.
5. **Idempotent.** Running this skill twice on the same file should produce no additional changes. If it does, the Phase 2 patterns are too aggressive.
6. **Back up first.** Before Phase 2, copy all chapter files to `chapters/backup-preprocess/`. If anything goes wrong, restore from backup.
7. **Never touch dialogue interruptions.** Em-dashes inside quotation marks where a character is cut off ("I was going to--") are CORRECT and must never be removed.
8. **Report everything.** Every change, every revert, every manual flag goes in the report. The Writer and Editor need full transparency on what was changed mechanically.
