# ADR 0015 — Semantic Audit Gate

## Decision

The adversarial-audit artifact must contain exactly one standalone line: `audit_status: pass`, `audit_status: revise`, or `audit_status: major_rewrite`.

Only `pass` advances from Phase 4 to Score and Package. For `revise` and `major_rewrite`, the runner publishes `artifacts/08-adversarial-audit.md`, keeps Phase 4 as the current phase, blocks its gate, and writes `status: awaiting_revision` to `PROJECT_STATE.yaml`. Accepted drafts and a high panel signal do not override this manuscript-level editorial decision.

## Audit context

The audit receives complete canonical chapters and the relevant project artifacts. It evaluates the manuscript as a whole; it does not repeat a blind verdict on one chapter or infer editorial approval from process signals.

## Recovery

The block is intentionally recoverable but not automatic:

1. Read `artifacts/08-adversarial-audit.md` and identify the blockers it describes.
2. Revise the manuscript outside the runner while preserving artifacts and project state as a record of what occurred.
3. Run `book-genesis resume <project-folder>` so Phase 4 runs again.
4. The project proceeds to Score and Package only if the new audit declares `audit_status: pass`.

There is no automatic repair command. `revise` and `major_rewrite` do not promise that one editing round will be sufficient; both require a newly passing audit before later phases are released.
