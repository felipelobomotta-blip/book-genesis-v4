# ADR 0011 — Immutable History and Transactional Publication

## Decision

Each phase response is written first to `work/phase-attempts/<phase>/<sequence>/`. It is published only after every output required by that response is valid. Incomplete attempts remain in that directory with `STATUS.txt`; they do not alter project state, published artifacts, or a gate.

Before publication, the runner writes `work/phase-publication.json`. The journal holds a closed list of permitted targets and their previous bytes, including `PROJECT_STATE.yaml`. `runner.phases.recover_pending_publication(project)` restores that journal idempotently and is called before a resumed run decides phase or state. The marker is removed only after artifacts, state, and gate advancement have all finished.

Every chapter attempt creates a record in `manuscript/chapters/history/chapter-NN/manifest.json`, schema `book-genesis.chapter-history/v1`. The manifest contains `chapter`, `accepted` (or `null`), and `attempts`. An attempt records `attempt_id`, `sequence`, `status`, `draft_path`, `verdict_path`, and `sha256`. Paths are POSIX-relative to the project. Drafts and verdicts are never overwritten; `chapter-NN.md` remains the canonical snapshot of the most recently accepted attempt.

## Compatibility

Older projects without a manifest continue to use `chapter-NN.md` and legacy evaluation names. Score readers use the manifest when it exists and fall back to the legacy layout only when it does not.

## Consequences and limits

A pending rewrite is recorded in `work/rewrite-chapter-NN.pending`; the accepted chapter is not deleted before a replacement is accepted. Resume discovers the checkpoint and completes the pending attempt. The score links model-reader signals only to the verdict for the accepted draft and does not represent immediate model memory as delayed human memory.

The journal reduces mixed artifacts when the process fails between replacements. It does not guarantee recovery from power loss, filesystem caching, or hardware failure without `fsync` or transactional semantics provided by the underlying volume.
