---
name: reader-persona
description: Builds 3-5 reader personas representing the book's target audience segments. Each persona has reading habits, emotional triggers, deal-breakers, discovery channels, and comp title preferences. Used by writer (voice calibration), evaluator (4-reader simulation), and packager (marketing targeting).
---

# READER PERSONA — Audience Architecture V3.7

Writers who write "for everyone" write for no one. This skill creates concrete, detailed reader profiles so every agent in the pipeline knows exactly WHO they are writing for. The personas inform:

- **Architect:** Pacing decisions, what the reader's patience threshold is
- **Writer:** Vocabulary level, what to explain vs. assume, emotional calibration
- **Evaluator:** Whether the manuscript serves its actual audience (4-reader simulation)
- **Packager:** Marketing angle, comp titles, pitch framing, discovery channel targeting
- **Chaos Engine:** Which persona to CHALLENGE (the comfortable one) and which to PROTECT (the one on the edge of abandoning)

---

## WHEN TO RUN

- **After:** Research phase is complete (`bestseller-dna.md`, market analysis exist)
- **After:** Foundation document exists (genre, theme, engagement type defined)
- **Before:** Any writing begins
- **Trigger:** Orchestrator calls this once during project setup
- **Re-run:** Only if the book's genre, thesis, or target audience fundamentally changes

---

## REQUIRED INPUTS

1. **`foundation.md`** — for:
   - Genre classification
   - Engagement type ranking (primary/secondary/tertiary)
   - Premise and theme
   - Protagonist archetype and tone
   - Emotional residue target
2. **`research/bestseller-dna.md`** (if available) — for:
   - Comparable titles and their audiences
   - Market positioning
   - Genre conventions and reader expectations
3. **`STATE.yaml`** — for project metadata, genre declaration
4. **Any market research** in `research/` directory

---

## OUTPUT

A single file: **`reader-personas.md`** in the book's root directory.

---

## BUILDING THE PERSONAS

### Step 1: Audience Landscape Analysis

Before creating individual personas, establish the audience landscape.

**1.1 Genre Audience Mapping**

Based on the genre declared in `foundation.md`, identify:
- Core demographic (age range, gender skew if applicable, education level)
- Reading frequency (books per year)
- Discovery channels (BookTok, Goodreads, book clubs, literary reviews, podcast recommendations, airport bookstores)
- Purchase triggers (cover, blurb, recommendation, author loyalty, topic interest)
- Deal-breakers (content they will not tolerate, pacing they will abandon)

**1.2 Comp Title Audience Extraction**

For each comp title in `bestseller-dna.md`:
- Who read it? (Check Goodreads demographics, BookTok audience, Amazon review patterns)
- What did positive reviewers praise?
- What did negative reviewers criticize?
- What adjacent books do these readers also read?

**1.3 Engagement Type to Reader Translation**

From `foundation.md`'s engagement type ranking:

| Engagement Type | Reader Behavior | Reading Pace | Recommendation Trigger |
|-----------------|----------------|--------------|----------------------|
| **Empathy-primary** | Wants emotional connection, character depth, vulnerability | Slower, savors | "How it made me feel" |
| **Fascination-primary** | Wants to be surprised, challenged, unable to predict | Faster, chases plot | "You won't believe what happens" |
| **Self-insertion** | Wants to see themselves in the protagonist | Moderate | "This is literally me" |
| **Intellectual** | Wants to learn, think, argue | Variable | "This changed how I think about X" |
| **Aspiration/Identity** | Wants to feel elevated by reading it | Variable | The book's cultural status |

Map the primary/secondary engagement types to specific reader behaviors. The PRIMARY engagement type determines the PRIMARY persona.

### Step 2: Create 3-5 Personas

**Mandatory personas (3):**

1. **PRIMARY READER** (~60% of audience) — The book's core reader. Most likely to buy, finish, and recommend. Maps to the primary engagement type.
2. **STRETCH READER** (~25% of audience) — Does NOT typically read this genre. Something about THIS book could pull them in. Maps to a different engagement type.
3. **HOSTILE READER** (~15% of audience) — Predisposed to dislike this book. Picked it up because of hype, a book club, or a gift. Looking for reasons to put it down.

**Optional personas (1-2):**

4. **NICHE READER** — A specific subculture or community that would adopt this book for reasons other than its primary appeal (e.g., therapists recommending a trauma memoir, educators assigning a literary novel, book clubs picking a discussion-rich text).
5. **GENERATIONAL READER** — A reader from a different age bracket than the primary, who connects with the book through a different lens (e.g., a parent reading a coming-of-age story through the lens of their own child).

Add niche personas only when the book has genuine crossover potential beyond its core genre. Do not pad to 5 for the sake of completeness.

### Step 3: Fill ALL Fields Per Persona

### Step 4: Derive Writer Instructions

### Step 5: Save as `reader-personas.md`

---

## PERSONA TEMPLATE — PRIMARY READER

```markdown
## PRIMARY READER: [Name]

### Demographics & Identity
- **Age:** [specific, e.g., 34]
- **Gender:** [if relevant to reading habits]
- **Location:** [urban/suburban/rural, region]
- **Education:** [level and field]
- **Occupation:** [specific job, not category]
- **Reading frequency:** [books per year]
- **Reading format:** [physical, ebook, audio, mix]

### Reading Psychology
- **Why they read:** [escape, learning, emotional processing, entertainment — be specific]
- **How they describe their taste:** [in their own words, e.g., "I like dark stuff but nothing too depressing"]
- **What hooks them (first page test):** [what makes them keep reading past page 1]
- **What makes them abandon (deal-breakers):** [specific triggers that make them put the book down]
- **Emotional triggers:** [what scenes/moments hit hardest for THIS reader]
- **Re-read triggers:** [what makes them come back to a book]
- **Reading speed:** [fast skimmer, moderate, slow savorer]
- **Patience for slow sections:** [high/medium/low — how many pages before they skip ahead]
- **Relationship to discomfort:** [do they read to be challenged or comforted?]

### Emotional Profile
- **What they want to FEEL:** [the emotional experience they are seeking]
- **What they want to AVOID feeling:** [emotions that would make them close the book]

### Genre Relationship
- **Three books they loved (and why):**
  1. **[Title]** — [specific reason, in their voice: "I couldn't stop thinking about X"]
  2. **[Title]** — [specific reason]
  3. **[Title]** — [specific reason]
- **Three books they hated (and why):**
  1. **[Title]** — [specific reason, in their voice: "Too slow, nothing happened for 100 pages"]
  2. **[Title]** — [specific reason]
  3. **[Title]** — [specific reason]
- **What they love about the genre:** [specific elements]
- **What they're tired of in the genre:** [cliches they'll reject]
- **Crossover interests:** [other genres they read]

### Discovery & Purchase
- **Where they find books:** [specific platforms/sources, ranked]
- **What makes them BUY:** [cover, blurb, first chapter, reviews, recommendation]
- **What makes them RECOMMEND:** [the specific trigger — emotional impact, surprise, relatability, status]
- **How they recommend:** [word of mouth, link sharing, gift buying, book club pick]
- **Price sensitivity:** [hardcover buyer, waits for paperback, ebook only, library]

### Social Sharing Behavior
- **Platforms:** [where they talk about books]
- **What they share:** [quotes, reviews, aesthetic photos, hot takes]

### The ONE Thing They Need from Chapter 1
[Specific, actionable: "A character they recognize — someone whose internal experience mirrors their own overthinking." NOT vague: "A good hook."]

### What Would Make Them Give a 5-Star Review
[The specific experience that would make them rave, in their voice]

### What Would Make Them Abandon at Chapter 3
[The specific failure that would lose them]

### This Persona's Test
[ONE specific question the evaluator asks when simulating this reader:]
- "Would [Name] finish this book?"
- OR "Would [Name] recommend this to a friend?"
- OR "What would [Name] highlight/screenshot?"
- OR "Where would [Name] abandon this?"
[Pick the most diagnostic question for this persona.]
```

---

## PERSONA TEMPLATE — STRETCH READER

Use the same template as Primary Reader, plus these additional fields:

```markdown
### Why They Don't Usually Read This Genre
[Specific objection: "I find literary fiction pretentious" or "Self-help feels preachy"]

### What Would Pull Them In
[The specific element of THIS book that bridges their objection: "The humor undercuts the literary weight" or "The framework is genuinely new, not recycled advice"]

### The Bridge
[Which element of the book connects their usual taste to this book? A thriller reader pulled into literary fiction by the plot structure. A romance reader pulled into memoir by the love story. Be specific.]
```

---

## PERSONA TEMPLATE — HOSTILE READER

Use the same template as Primary Reader, plus these additional fields:

```markdown
### Their Objection Before Reading
[What they expect to dislike: "Another trauma memoir" or "Self-help snake oil" or "Overhyped literary fiction"]

### What Would Confirm Their Bias
[The specific failure: "If the prose is trying too hard" or "If the advice is obvious" or "If the protagonist is a victim with no agency"]

### What Would Convert Them
[The specific moment/quality that would override their skepticism: "A moment of genuine humor that shows the author doesn't take themselves too seriously" or "A framework they haven't encountered that actually works"]

### The Conversion Point
[By which chapter must the conversion happen? If the Hostile Reader isn't converted by Chapter [N], they are lost. Give a specific chapter number.]
```

---

## PERSONA TEMPLATE — NICHE READER (optional)

Use the same template as Primary Reader, plus:

```markdown
### Professional/Community Context
[Why this community would adopt the book — therapeutic use, educational use, discussion value]

### How They Encounter This Book
[Different discovery channel than primary — conference recommendation, professional newsletter, syllabus, colleague]

### What They Extract
[What they take from the book that the primary reader doesn't — frameworks, case studies, discussion prompts, clinical insight]
```

---

## HOW THE PIPELINE USES PERSONAS

### Writer (Voice Calibration)
- Calibrates prose complexity, pacing, and emotional beats to the PRIMARY persona
- When there is a conflict between what two personas need, the PRIMARY wins
- The Writer checks: "Would [Primary Name] understand this sentence? Would it bore [Stretch Name]? Would it confirm [Hostile Name]'s bias?"

### Evaluator (4-Reader Simulation)
- Simulates EACH persona reading the manuscript
- Reports where each would engage, disengage, or abandon
- Uses each persona's specific TEST question as the evaluation lens
- The Hostile Reader simulation is the most important — if the book survives the Hostile Reader, it survives everyone

### Packager (Marketing Targeting)
- Targets the editorial package (query letter, cover brief, blurb) to the PRIMARY persona's discovery channel and purchase triggers
- Uses the Stretch Reader's bridge to identify crossover marketing angles
- Uses the Hostile Reader's conversion point to identify the book's strongest selling argument

### Chaos Engine (Challenge Calibration)
- Knows which persona to CHALLENGE: the one who is too comfortable (usually Primary)
- Knows which persona to PROTECT: the one on the edge of abandoning (usually Stretch or Hostile)
- Disruptions should push the Primary out of their comfort zone WITHOUT losing the Stretch Reader

---

## WRITER INSTRUCTIONS (derived from personas)

After building all personas, generate actionable instructions for downstream agents.

### Chapter 1 Requirements

```markdown
## Chapter 1 Must Deliver:
- **For Primary Reader:** [specific need] by page [X]
- **For Stretch Reader:** [bridge element] by page [X]
- **For Hostile Reader:** [conversion seed] by page [X]
```

### Pacing Guidelines

```markdown
## Pacing Calibrated to Reader Patience:
- **Maximum consecutive pages of introspection:** [N] (Primary Reader's patience limit)
- **Action/event frequency:** at least one per [N] pages (Stretch Reader's attention span)
- **Intellectual density:** [calibration] (match Primary Reader's vocabulary and concept tolerance)
```

### Content Boundaries

```markdown
## Content Boundaries:
- **Explicit content:** [what the Primary Reader expects/tolerates]
- **Violence/darkness:** [threshold before losing the Primary Reader]
- **Humor level:** [what the Primary Reader expects]
- **Political/social content:** [how much the Primary Reader wants — overt, subtle, absent]
```

### Shareability Instructions

```markdown
## What Each Reader Would Share:
- **Primary Reader shares:** [type of moment — emotional quote, plot twist, relatable scene]
- **Stretch Reader shares:** [what surprised them about liking this book]
- **Hostile Reader shares (if converted):** ["I didn't expect to like this, but..." — the most powerful recommendation type]
```

### Deal-Breaker Watchlist

```markdown
## Agent Watchlist — These Will Lose Readers:
1. [Specific thing Primary Reader will not tolerate]
2. [Specific thing Stretch Reader will bail on]
3. [Specific thing that confirms Hostile Reader's bias]
4. [Specific AI-writing pattern that breaks immersion for ALL personas]
```

---

## OUTPUT FORMAT

Save to `reader-personas.md` in the project root directory.

```markdown
# Reader Personas — [Book Title]

Generated: [date]
Based on: foundation.md, bestseller-dna.md, market research

---

## Audience Landscape
[Phase 1 summary — 2-3 paragraphs covering genre audience, comp title insights,
and engagement type mapping]

---

## Primary Reader: [Name]
[Full profile]

---

## Stretch Reader: [Name]
[Full profile + bridge fields]

---

## Hostile Reader: [Name]
[Full profile + conversion fields]

---

## [Optional] Niche Reader: [Name]
[Full profile + context fields]

---

## [Optional] Generational Reader: [Name]
[Full profile + lens fields]

---

## Writer Instructions
[All derived instructions: Ch.1 requirements, pacing, content boundaries,
shareability, deal-breaker watchlist]

---

## Quick Reference Card

| Persona  | Needs from Ch.1 | Deal-Breaker | Shares Because | Test Question |
|----------|-----------------|--------------|----------------|---------------|
| Primary  | [one line]      | [one line]   | [one line]     | [one line]    |
| Stretch  | [one line]      | [one line]   | [one line]     | [one line]    |
| Hostile  | [one line]      | [one line]   | [one line]     | [one line]    |
| [Niche]  | [one line]      | [one line]   | [one line]     | [one line]    |
```

---

## RULES

1. **Personas are PEOPLE, not demographics.** "Women 25-40 who read literary fiction" is not a persona. "Mariana, 32, a burned-out therapist who reads on the subway and needs books that make her feel less alone" is a persona.

2. **Ground in data.** Every persona claim should trace back to comp title audience data, Goodreads patterns, or genre conventions from the research phase. Do not invent audiences.

3. **The Hostile Reader is not a strawman.** Their objections must be REAL and FAIR. If you cannot articulate a genuine reason someone would dislike this book, the persona is dishonest.

4. **Loved/Hated books must be REAL titles.** Do not invent fictional comp titles. Use actual published books that this reader would plausibly have read.

5. **The conversion point is a chapter number.** Not "eventually" or "by the end." Hostile Readers have a specific patience threshold. Name it.

6. **Writer Instructions are PRESCRIPTIVE.** Not "consider the reader's patience" but "no more than 3 consecutive pages of introspection before an event or dialogue exchange."

7. **Update if the book changes.** If the Architect significantly revises the foundation or outline after personas are created, flag that personas may need recalibration.

8. **One persona per engagement type.** The Primary Reader should map to the primary engagement type. The Stretch Reader should map to a different engagement type. This ensures the book serves multiple reader motivations.

9. **The PRIMARY persona drives conflicts.** When two personas need contradictory things (e.g., Primary wants slow emotional scenes, Stretch wants faster pacing), the Primary wins. Document the trade-off explicitly so the Writer knows what they are sacrificing and for whom.

10. **Personas are NOT demographics — they are psychographics.** Two 30-year-old women can be radically different readers. Age, gender, and location are context. Reading psychology, emotional triggers, and deal-breakers are the actual persona.

11. **Every persona must have at least ONE unique deal-breaker.** If all three personas would abandon for the same reason, you have one persona wearing three masks. Differentiate.

12. **3 personas minimum, 5 maximum.** Do not pad. Add the 4th and 5th only when the book has genuine crossover potential that demands a distinct persona to represent it. Three well-built personas beat five shallow ones.
