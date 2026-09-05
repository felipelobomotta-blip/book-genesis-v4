# Genesis Score

The Genesis Score is an internal summary of model-reader and revision-process signals from a completed Book Genesis run. It is designed to make the runner’s signals visible, not to certify literary quality.

## Formula

The score ranges from 0.0 to 10.0:

| Component | Weight | What it records |
|---|---:|---|
| Reader panel | 40% | blind model-reader votes that would turn the page; if no panel ran, accepted-version judge results |
| First-draft acceptance | 30% | chapters accepted without a revision cycle |
| Chapters accepted | 20% | chapters with an accepted verdict linked to the canonical chapter |
| Memorable | 10% | accepted-version verdicts with a specific immediate `remember` item |

```text
score = 10 × (0.40 × panel + 0.30 × first_draft + 0.20 × accepted + 0.10 × remembered)
```

Each component is a fraction from 0 to 1. The runner reads chapter results from `RUN_REPORT.md` and checks attempt history where present. A canonical chapter changed after acceptance does not retain the old verdict merely because a report file exists.

## What it means

The score tells you about this run’s documented process: whether configured model readers continued, whether revisions were needed, whether accepted versions remain linked, and whether an immediate reading retained a detail. It can help identify a run worth reading more closely.

It does **not** measure human enjoyment, delayed human memory, originality, publication readiness, safety, professional editorial quality, market timing, or sales. “10/10” means the formula’s model-process components all reached their maximum. It does not mean the manuscript is a 10/10 book.

Provider independence also depends on the author’s configuration. A different writer and judge family is preferred when available; a single-family run is allowed and recorded as a warning. Multiple panel personas using the same underlying model are not multiple human readers or independent model families.

## Relationship to the audit

The score is downstream of the manuscript-level audit. The audit must declare `audit_status: pass` before the session completes. `revise` and `major_rewrite` block the session at Audit, so Score and Package do not run. A good chapter-panel result cannot override a manuscript-level audit failure.

## Historical note

Earlier repository documents described a floor-based 7- or 10-dimension numeric score, an 8.5 gate, benchmark calibration, and commercial-viability indices. Those approaches are historical material in `legacy/`; they are not implemented as current approval gates and must not be interpreted as validation studies.
