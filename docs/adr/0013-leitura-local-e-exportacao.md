# ADR 0013 — Local Reading, History, and Canonical Export

**Status:** Accepted, 2026-09-04.

`book-genesis review` produces self-contained local HTML and does not send the manuscript to a service. The reader uses an editorial-width layout, fixed chapter navigation, accessible version controls, and precomputed unified diffs. Text is escaped; only Markdown headings and paragraphs are rendered. Its content policy blocks network access and permits only the local script by hash. Output is restricted to `review/`; paths, reports, and manifests crossing symbolic links are refused.

History uses `book-genesis.chapter-history/v1`, accepts only POSIX-relative paths within the project, and verifies that the accepted attempt hash also matches the canonical chapter before it calls an attempt accepted. Malformed or altered history appears as a warning, never as an invented approval. Older projects display numbered drafts with unknown provenance or acceptance.

`book-genesis export` uses canonical chapters, declares partial coverage, and creates local Markdown or EPUB 3. The EPUB writes `mimetype` first and uncompressed, followed by container, OPF, navigation, and XHTML. Exports never replace state, manuscript, drafts, or an existing file without `--overwrite`.
