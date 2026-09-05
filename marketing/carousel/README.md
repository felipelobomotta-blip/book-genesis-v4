# Book Genesis 5 carousel assets

This folder contains final-ready English marketing assets for **Book Genesis 5 - Imagination Edition**.

## Outputs

- `assets/book-genesis-5-imagination-edition-carousel.pdf` - six-page square carousel.
- `assets/book-genesis-5-slide-01.png` through `assets/book-genesis-5-slide-06.png` - individual square PNG slides.
- `build_carousel.py` - editable ReportLab source.

## Claims used

The carousel states only the recorded beta boundaries: 279 local regression tests, one 1,910-word smoke story, model evaluation only, and human validation still pending. It does not promise a bestseller, publication readiness, or human-reader validation.

## Rebuild

Install ReportLab and put Poppler's `pdftoppm` command on PATH. These are optional marketing build tools, not runtime dependencies.

```bash
python -m pip install reportlab
python marketing/carousel/build_carousel.py
```
