# Case study: an audit that disagreed with the reader panel

*Data de Devolução* was a **1,910-word, single-chapter Portuguese engineering smoke test**. This English case study records what happened; it is not a translated manuscript or a claim of publication readiness.

| Observation | What it establishes |
| --- | --- |
| Claude drafted the chapter; Codex ran the reader personas. | Two configured model families participated in the exercise. |
| All three reader personas used the same judge model. | The panel was model feedback, not independent human research. |
| The chapter passed its first panel and received an internal 10/10 process signal. | The process signals were favorable at that point; literary quality was not established. |
| The later full-prose audit returned MAJOR REWRITE. | An ending/premise gap remained despite the earlier signal. |
| Frozen-response replay stopped the corrected runner at audit with exit code 4. | A saved real rejection now blocks completion; no new live generation was implied. |

The audit identified a distinction between disappearance and death that the ending had not adequately resolved. This finding prompted two corrections: later phases now receive the actual canonical prose, and the audit's semantic status controls whether the project can advance.

The canonical chapter's SHA-256 was identical before and after the blocking replay:

```text
63b3e9f4b3663d96b2eb21c55a5135e9422bf5c1b8e99cc6c0a5452c6f3ddcea
```

The beta preserves the manuscript and asks the author to revise it. A new audit must return `pass` before the runner continues. A high internal score should never override a concrete editorial objection.

See the [validation record](../../docs/validation.md) and the separate [scripted reader demonstration](../reader-demo/README.md).
