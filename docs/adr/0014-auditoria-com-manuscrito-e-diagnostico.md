# ADR 0014 — Auditing the Manuscript and Using One Numeric Calculation

Phases 4, 5, and 6 previously received planning artifacts but no chapters. A successful call could therefore produce criticism and a synopsis without having received the manuscript. The Phase 5 template also requested absolute scores and an 8.5 approval threshold, conflicting with the internal-signal calculation in `runner/score.py`.

The three post-draft phases now receive every canonical chapter planned by the outline, in order. A missing or empty chapter stops the run before a model call. There is no silent truncation: provider context limits remain real limits and can prevent long works from completing.

Phase 5 produces a qualitative editorial diagnostic with textual evidence and uncertainty, without a second numeric score or commercial approval. The only numeric Genesis Score is calculated by the runner from model-reader verdicts and revision records. Independence between models depends on configuration. None of these signals substitutes for human reading.

The editorial package is a presentation draft with open issues, not a readiness certificate. The historical path `artifacts/09-genesis-score-codex.md` remains compatible, with its content identified as a diagnostic.
