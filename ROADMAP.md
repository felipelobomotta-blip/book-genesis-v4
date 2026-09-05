# Roadmap

Book Genesis is a technical beta. This roadmap separates delivered behavior from work that must be validated before broader claims are appropriate.

## Implemented in the current beta

- Guided `new` and `resume` session with progress, author notes, `q` checkpoints, and `--yes` non-interactive mode.
- Seven-stage local runner: intake, foundation, architecture, drafting, adversarial audit, internal score, and editorial package.
- Chapter-level drafting, blind model reading, revision comparison, chapter 1 panel, draft history, and canonical snapshot linkage.
- Phase output validation, staged publication journal, and interrupted-publication recovery.
- Semantic audit gate: `revise` and `major_rewrite` block Phase 4, preserve the audit, and stop Score and Package.
- Provider setup, configurable adapters, manual mode, local review HTML, Markdown export, EPUB export, and an installable wheel.
- Offline local regression suite. The final verification recorded 279 passing tests on Windows/Python 3.11; remote CI is configured but was not run as part of that verification.

## Next: validate the beta with authors

### New-author onboarding study

**Goal:** find out whether a person who did not help build the project can install it, connect a provider, create a story, resume it, inspect it, and export it.

**Acceptance criteria:**

- Recruit at least 10 target authors with varied terminal familiarity.
- Record task completion, time, help requested, setup failure, and the exact stopping point.
- Publish anonymized findings and the resulting onboarding fixes.
- Do not describe setup as “easy” until observed completion supports that claim.

### Human-reader comparison

**Goal:** test whether the workflow improves reader response versus a competent direct generation baseline.

**Acceptance criteria:**

- Pre-register prompts, selection rules, reader allocation, and success measures.
- Use blind assignment and include every eligible output, not only favored examples.
- Measure continuation, comprehension, and delayed recall with real readers.
- Publish methods, sample size, exclusions, and limitations; do not convert a small pilot into a bestseller claim.

## Next: validate long-form reliability

### Multi-chapter continuity runs

**Goal:** establish how the architecture holds across longer works and real provider context limits.

**Acceptance criteria:**

- Run at least six projects across several genres with 12 or more chapters each.
- Trace character knowledge, timeline events, objects, and unresolved plot threads against the final manuscript.
- Record provider context failures, timeouts, recovery outcomes, and costs.
- Define and test a bounded audit strategy before claiming robust book-length audit coverage.

### Editorial recovery workflow

**Goal:** make a blocked audit understandable and useful without hiding its severity.

**Acceptance criteria:**

- Test at least 20 `revise` and `major_rewrite` reports with authors and editors.
- Confirm people can identify required changes, preserve their work, revise, and request a fresh audit.
- Only propose assisted structural repair after it has a clear provenance model and does not overwrite author work.

## Next: release engineering

### Repeatable distribution

**Acceptance criteria:**

- Run the existing Windows/Linux Python 3.10/3.12 CI matrix in the remote repository.
- Test a wheel install and `book-genesis --help`, `review`, and `export` on clean machines.
- Publish signed or reproducible release notes only after the version and verification evidence are current.

### Community foundations

**Acceptance criteria:**

- Maintain issue templates and discussion prompts for bug reports, provider compatibility, genre profiles, and writing-process feedback.
- Add contributor examples that require no paid provider calls.
- Establish a transparent process for prompt, safety, and documentation changes.

## Deliberately not promised

No roadmap item claims automatic bestseller production, publication readiness, universal model isolation, or automatic repair of an editorially blocked manuscript. Those claims would need much stronger evidence than a codebase, a model score, or a single successful run.
