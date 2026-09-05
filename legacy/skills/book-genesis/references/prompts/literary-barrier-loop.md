# Literary Barrier Revision Loop

You are responsible for Phase 5 of `book-genesis-codex`.

## Goal

Raise the manuscript until its calibrated literary critical score is above the target threshold, defaulting to 8.5 when the user does not specify another number.

This phase exists because a manuscript can pass ordinary structure checks and still fail as literature. The loop targets the ceiling: voice, residue, risk, character contradiction, thematic pressure, and reader memory.

## Inputs

Read:

- `artifacts/08-adversarial-audit.md`
- all manuscript chapters
- foundation and architecture artifacts
- the latest Genesis Score report if one already exists
- prior files in `evaluations/` if this is not the first loop

## Calibration Rule

Internal evaluation is biased upward. Before deciding that the book cleared the barrier:

1. score each critical lens from 1 to 10
2. subtract 0.8 from each lens score unless there is external human critique attached in `evaluations/`
3. use the lowest calibrated lens as the Literary Barrier Score

Do not claim the threshold was reached unless the calibrated floor is above the target.

## Critical Lenses

Score and diagnose these lenses separately:

1. Line: sentence quality, rhythm, precision, image pressure, absence of generic polish
2. Voice: recognizability, durability over pages, resistance to synthetic sameness
3. Character: contradiction, memory, self-sabotage, behavior under pressure
4. Structure: chapter necessity, escalation, reversals, payoff, reread architecture
5. Theme: lived inquiry, subtext, moral/intellectual pressure, no lecture residue
6. Emotion: earned feeling, aftertaste, embodied reaction, non-obvious residue
7. Originality: premise, execution, lens, refusal of stale genre defaults

## Loop

Repeat until the calibrated Literary Barrier Score is above target or a blocker is explicit:

1. Identify the lowest scoring lens.
2. Name the exact passages or structural zones causing the ceiling.
3. Choose the smallest revision class that can raise the ceiling:
   - structural revision
   - connective revision
   - character deepening
   - voice recalibration
   - line edit
   - cut or merge
4. Revise the manuscript files directly.
5. Save a revision note in `evaluations/literary-barrier-loop.md`.
6. Rescore all lenses, including any lens that might have been damaged.

## Revision Rules

- Preserve the strongest passages unless they are structurally false.
- Do not add decorative lyricism to chase a literary score.
- Prefer concrete pressure over abstract explanation.
- Prefer scene behavior over thematic statement.
- Prefer one strange true detail over three polished generic sentences.
- If a chapter cannot justify its existence, cut or merge it.
- If a character behaves correctly too often, introduce cost, evasion, contradiction, or self-caused damage.
- If prose sounds smooth but forgettable, add specificity, asymmetry, silence, interruption, or a harder image.

## Stop Conditions

Stop with approval only when:

- calibrated Literary Barrier Score > target
- no critical lens below target
- no Phase 4 finding remains unresolved at major severity
- the revision report cites textual or structural evidence

Stop with blocker only when:

- the manuscript lacks enough draft material to evaluate
- the next improvement requires author decision, lived material, external research, or human critique
- further revision would be speculative churn

## Output

Save or update `evaluations/literary-barrier-loop.md` with:

- target threshold
- iteration number
- lens scores before and after calibration
- lowest lens
- revision actions taken
- passages changed
- strengths preserved
- current verdict: `CONTINUE`, `APPROVED`, or `BLOCKED`
