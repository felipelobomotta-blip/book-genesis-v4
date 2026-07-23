# Independent Evaluator Protocol

Use this protocol for Literary Barrier and final Genesis Score evaluations. Goal: reduce self-grading, threshold anchoring, and evidence-free praise.

## Blind Inputs

Give evaluators only:

- manuscript files or declared sample
- stable foundation and architecture facts needed for continuity
- scoring rubric
- market position when Market is being scored

Do not give evaluators:

- writer self-reports
- revision rationale
- desired pass threshold
- previous numeric scores
- another evaluator's verdict

## Role Boundaries

- Writer drafts. Writer never issues final score.
- Evaluator diagnoses and scores. Evaluator never edits manuscript.
- Revision editor receives evidence-backed tickets, then edits.
- Fresh evaluator verifies revisions without reading previous numeric scores.
- Orchestrator aggregates reports and applies pass thresholds after scoring.

## Independence Grades

- `A`: three or more fresh evaluator contexts; at least two model families when available.
- `B`: three or more fresh evaluator contexts using same model family.
- `C`: evaluation occurs in writer or revision context, or prior scores leak into evaluation.

Grade C is diagnostic only. Do not describe Grade C results as independent critical validation.

## Required Evaluator Output

Each evaluator must provide:

- score per dimension
- strongest passage with location and reason
- weakest passage with location and reason
- evidence for every score above 8.0
- blocking defect and smallest viable intervention
- confidence: low, medium, or high
- coverage: full manuscript or named sample
- explicit conflicts of evidence

## Aggregation

1. Calculate median score per dimension.
2. Use lowest dimension median as floor.
3. Keep disagreement visible; never hide a weak evaluator behind average enthusiasm.
4. When evaluator spread reaches 1.5 points on any dimension, dispatch another blind evaluator or mark confidence low.
5. Apply score calibration only after raw independent reports are frozen.
6. Apply project threshold only after calibrated scores exist.

## Integrity Failure

Mark evaluation `DEGRADED` when:

- evaluator edited text being scored
- evaluator saw required target before scoring
- claims lack textual or structural evidence
- only excerpts were read but report claims full-manuscript coverage
- missing output was treated as a passing score

Degraded evaluation can create revision tickets. It cannot approve publication readiness.
