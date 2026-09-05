# Book Genesis 5 — Imagination Edition press kit

## One-line summary

Book Genesis 5 is an MIT-licensed, open-source writing runner that turns an idea into an inspectable manuscript workflow with drafts, model-reader feedback, a semantic audit gate, local review, and export.

## Positioning draft

Book Genesis is presented as a writing workflow in which an idea becomes a project with a brief, outline, chapter attempts, reader feedback, a manuscript audit, local review, and exportable manuscript files. Its public beta materials frame the creator as responsible for the premise, decisions, revision, voice, and publication choice.

**Book Genesis 5 — Imagination Edition** uses the line “Creativity comes first. Your story. Your choices.” This is proposed brand copy for the launch, not a statement of authorship, ownership, or legal rights.

The recorded beta verification includes a limited one-chapter smoke run: early model-reader signals were positive, while the full-prose audit returned `MAJOR REWRITE` for a structural gap. The current runner uses that outcome as a regression case: `revise` and `major_rewrite` leave the project in `awaiting_revision` and block downstream Score and Package steps.

## What is new in v5.0.0-beta.1

- Guided author checkpoints around brief, outline, and first chapter.
- Durable history and canonical-text integrity for chapter attempts and verdicts.
- Recovery journal for interrupted artifact publication.
- Local responsive reader report with version comparisons and audit visibility.
- Markdown and EPUB export from canonical chapters.
- Semantic audit gate that blocks downstream scoring and packaging on revision verdicts.
- Regression coverage for adapters, paths with spaces, resource packaging, timeouts, recovery, review, and export.

## Evidence and limits

279 automated tests passed **locally** on Windows/Python 3.11 before remote CI. A limited real-provider smoke run generated one Portuguese story of 1,910 words. This is engineering evidence, not evidence of literary quality, commercial success, human-reader validation, or long-book reliability.

Book Genesis does not promise a bestseller, replace an editor, decide publication readiness, or predict sales.

## Q&A

**What is Book Genesis?**

An open-source Python CLI that turns an idea into a project with documented writing artifacts, editorial signals, a manuscript audit, a local review report, and exports.

**Does it write a book for someone?**

It can orchestrate model-assisted drafting, but the author remains responsible for the premise, choices, revisions, voice, and decision to publish.

**Why call the reading blind?**

The model reader receives prose rather than the outline and writer notes, so it can respond to the chapter as a reader. It remains a model signal, not a human study.

**What happens when the audit rejects a manuscript?**

The audit report is kept, project state becomes `awaiting_revision`, and downstream Score and Package steps do not run. The author revises and resumes for a later audit.

**What has been tested?**

The beta’s recorded local verification includes 279 passing automated tests on Windows/Python 3.11 before remote CI and one limited real-provider, one-chapter smoke run.

**What is the role of Astra?**

Engineering update developed with assistance from Astra in Codex, with independent review and recorded tests. This does not make Astra a required runtime provider or imply OpenAI endorsement.

## Suggested launch copy

These are proposed marketing lines. They are not previously spoken or approved quotations. If used publicly, attribute only after Felipe Lobo reviews and adopts the exact wording. Do not alter them to imply guarantees.

> “Creativity comes first. Your story. Your choices.”

> “The first draft is not the finish line. It is where the real decisions begin.”

> “A report is not approval. If the story misses its promise, the process should be able to say so.”

> “I am not building a machine that replaces authors. I am building a process creators can inspect and challenge.”

## Asset-use notes

Use official Book Genesis image files and the exact product name, **Book Genesis 5 — Imagination Edition**, in coverage or launch material. Keep the artwork legible and unmodified in proportion. Do not imply that Felipe Lobo, Astra, Codex, or OpenAI endorses a third party, provider, product, or claim.

## Contact route

Use the repository’s GitHub issue tracker as the public contact route until a project owner provides a separate contact address.

## Asset inventory

See [launch artwork](assets/README.md) for four English images and their exact dimensions, and [the carousel](carousel/README.md) for the six-page PDF, six PNGs, and editable source.
