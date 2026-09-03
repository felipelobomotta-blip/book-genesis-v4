# Genesis Score Codex

## Purpose

Genesis Score Codex is the single scoring contract for `book-genesis-codex`.
It must be used consistently across prompts, adapters, examples, reports, and manual review.

The score exists to answer one question:

> Is this manuscript ready to survive contact with demanding readers, skeptical agents, and the market it claims to serve?

When the user sets a literary quality target, the score also records whether the manuscript cleared the calibrated Literary Barrier threshold.

## Order Of Operations

The score only happens after Phase 4: Adversarial Audit.

If Phase 5: Literary Barrier Revision Loop is active, final scoring happens after that loop either approves the manuscript or records a blocker.

If the adversarial audit concludes `MAJOR REWRITE`, the score may be recorded provisionally but the manuscript is not eligible for approval.

## Dimensions

The score uses 10 dimensions:

1. Originality
2. Theme
3. Characters
4. Prose
5. Pacing
6. Emotion
7. Coherence
8. Market
9. Voice
10. Opening

## What Each Dimension Measures

### Originality

- novelty of premise, lens, or execution
- freedom from stale imitation

### Theme

- depth of the central question
- resonance beyond plot mechanics

### Characters

- wound, desire, need, contradiction, and memory value

### Prose

- sentence quality
- precision
- texture
- avoidance of cliche and explanatory drag

### Pacing

- tension control
- variation
- forward pull

### Emotion

- whether the book actually lands its intended feeling

### Coherence

- internal logic
- continuity
- causal integrity

### Market

- comp clarity
- audience legibility
- packaging viability

### Voice

- recognizability
- distinctiveness
- durability over pages

### Opening

- first-page grip
- first-chapter promise
- whether the ending ultimately justifies that promise

## Scoring Rules

- baseline assumption is competence, not excellence
- any score above 8.0 must cite evidence
- any score above 9.0 must cite multiple pieces of evidence
- evidence must be textual, structural, or reader-impact based
- internal scores carry a default +0.8 inflation risk; report calibrated scores when comparing against an external-facing threshold
- do not let market clarity compensate for literary weakness when the stated goal is critical literary quality

## Calculation

Floor Score = minimum dimension score
Weighted Average = weighted mean of the 10 dimensions

Suggested weights:

- Originality: 1.1
- Theme: 1.0
- Characters: 1.2
- Prose: 1.0
- Pacing: 1.0
- Emotion: 1.1
- Coherence: 0.9
- Market: 0.8
- Voice: 1.1
- Opening: 0.8

## Approval Gate

Approval requires all of the following:

- Floor Score >= 8.5
- Weighted Average >= 9.0
- no dimension below 8.0
- evidence present for every dimension
- adversarial audit not marked `MAJOR REWRITE`
- if a Literary Barrier target is active, calibrated Literary Barrier Score > target

## Revision Logic

If the manuscript fails:

1. identify the weakest dimension
2. define the concrete intervention
3. verify that the intervention does not damage stronger dimensions
4. rescore after revision

## Output Contract

The final report saved to `artifacts/09-genesis-score-codex.md` must include:

- project and runtime context
- Dimension Scores table
- calibrated Dimension Scores table when no external human critique is attached
- Floor Score
- Weighted Average
- Literary Barrier Score and threshold when active
- Gate Verdict
- weakest dimension
- required intervention or approval note
