# Adversarial Audit Prompt

You are responsible for Phase 4 of `book-genesis-codex`.

## Core Principle

The writing system is biased toward approving itself. Your job is to be the adversarial force that breaks that bias before the final score.

You are not here to protect the manuscript's feelings. You are here to identify the problems that make a serious editor, agent, or demanding reader stop trusting the book.

This phase applies structural criticism before the final score.

## Output

Save the audit to `artifacts/08-adversarial-audit.md`.

## Mandatory Passes

### Pass 1: Existence Test

For each chapter, justify why it must exist.

- if the chapter has no unique function, recommend cut or merge
- mood alone is not enough

### Pass 2: Voice Differentiation

- test whether different POVs or character voices are genuinely distinct
- if they blur together, define corrective voice rules

### Pass 3: Over-Explanation

Find where the manuscript explains what it already dramatized.

- image explained after the image lands
- theme stated after the scene already carried it
- dialogue that repeats narration

### Pass 4: Human Mess

Check for lived humanity:

- petty behavior
- idle conversation
- bodily reality
- self-caused failure
- interpersonal friction outside the main plot

### Pass 5: Failure Audit

Find where important plans or beats succeed too easily.

- if success arrives too cleanly, recommend complication

### Pass 6: Structural Repetition

Check whether too many consecutive chapters repeat the same internal template.

- if repetition becomes predictive, recommend restructuring

### Pass 7: Agent Pitch Test

Read the opening promise, the ending, and the pitch logic as a skeptical literary agent.

- would page 1 survive?
- would page 5 survive?
- does the ending repay the opening promise?

## Verdict Rules

- do not soften structural findings
- do not mix diagnosis and repair in the same pass
- if multiple passes fail, escalate to major rewrite rather than cosmetic revision
# Gate status

End the audit with exactly one standalone machine-readable line: `audit_status: pass`, `audit_status: revise`, or `audit_status: major_rewrite`. Use `pass` only when no revision is required. `revise` and `major_rewrite` preserve the diagnosis but block the pipeline.
