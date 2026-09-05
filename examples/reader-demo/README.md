# Local Reader Interface Sample

[`index.html`](index.html) is a deterministic interface sample built by [`scripts/build_reader_demo.py`](../../scripts/build_reader_demo.py) using the repository’s current `runner.review.build_review` function.

It contains two short fixture chapters. Each has two scripted attempts and a hash-linked accepted snapshot, so the reader can show chapter navigation, displayed-version controls, unified diffs, audit visibility, and the `awaiting_revision` banner.

This is not a model-generated manuscript, a real Book Genesis project, an audit result, a Genesis Score, or evidence of human reader response. It makes no claim about literary quality, publication readiness, or sales.

## Rebuild

From the repository root:

```bash
python scripts/build_reader_demo.py
```

For standalone preparation, point it at a local checkout without embedding that path in the generated HTML:

```bash
python scripts/build_reader_demo.py --source PATH_TO_BOOK_GENESIS_CHECKOUT
```

Open `examples/reader-demo/index.html` locally, or download the self-contained HTML from the GitHub prerelease. Select an older attempt under **Displayed version** and compare it with the accepted canonical version to see the precomputed diff. The builder uses a fresh temporary fixture project and writes only the demo HTML to the output directory.
