# Watch Book Genesis 5 in action

## Assets and destinations

| Video | Format | Duration | Release asset |
| --- | --- | --- | --- |
| Main walkthrough | 1920 × 1080 landscape MP4 | 59.9 seconds | [Watch / download](https://github.com/felipelobomotta-blip/book-genesis-v4/releases/download/v5.0.0-beta.1/book-genesis-5-walkthrough-en.mp4) |
| Vertical cut | 1080 × 1920 vertical MP4 | 32.8 seconds | [Watch / download](https://github.com/felipelobomotta-blip/book-genesis-v4/releases/download/v5.0.0-beta.1/book-genesis-5-vertical-en.mp4) |

Release: [Book Genesis 5 — Imagination Edition · v5.0.0-beta.1](https://github.com/felipelobomotta-blip/book-genesis-v4/releases/tag/v5.0.0-beta.1)

Repository: [github.com/felipelobomotta-blip/book-genesis-v4](https://github.com/felipelobomotta-blip/book-genesis-v4)

## Description

Book Genesis 5 — Imagination Edition is an open-source CLI for developing an idea through a guided writing workflow: a brief, outline, chapter drafts, blind model-reader feedback, a manuscript audit, a local reader, and Markdown or EPUB export.

To try the beta, install Python 3.10 or later, clone the repository, install the local checkout, and connect a supported model route. Then start with an idea:

```bash
git clone https://github.com/felipelobomotta-blip/book-genesis-v4.git
cd book-genesis-v4
python -m pip install -e .
book-genesis setup
book-genesis new --idea "A night-shift archivist discovers that returned library books remember their readers." --language en --path books/returned-books
```

The guided session stops after the brief, outline, and a blind read of chapter one. Press Enter to continue, write a note to redirect the work, or press `q` and later run:

```bash
book-genesis resume books/returned-books
book-genesis review books/returned-books --open
book-genesis export books/returned-books --format epub
```

The local reader supports chapter navigation, attempt history, version comparison, and the audit report. Export writes accepted canonical chapters; incomplete projects are labeled as partial.

Book Genesis is a controlled beta. It is not a promise of a bestseller, publication readiness, human-reader validation, or effortless terminal onboarding. The author remains responsible for the creative direction, revisions, and publication decision.

## Video provenance note

This walkthrough uses edited-time sequences to make the workflow legible. Its terminal and reader shots are recorded from a scripted English interface fixture, clearly labeled in the video; they are not a live provider generation or a literary-quality demonstration. The narration is synthetic English narration prepared for this video. The audio uses the broader phrase “working manuscript”; the product’s technical behavior is more precise: it exports accepted canonical chapters and labels incomplete exports as partial.

## Scene timing (reference)

```text
00:00 The idea
00:08 Requirements and model route
00:14 Start a guided project
00:21 Brief, outline, and chapter-one checkpoints
00:32 Local reader and version comparison
00:42 Export accepted canonical chapters
00:49 Open-source beta
```

## Links

- Repository: https://github.com/felipelobomotta-blip/book-genesis-v4
- Release: https://github.com/felipelobomotta-blip/book-genesis-v4/releases/tag/v5.0.0-beta.1
- Quick start: https://github.com/felipelobomotta-blip/book-genesis-v4/blob/master/docs/quickstart.md
- Validation and limits: https://github.com/felipelobomotta-blip/book-genesis-v4/blob/master/docs/validation.md


## Reuse the video

[Download the video kit ZIP](https://github.com/felipelobomotta-blip/book-genesis-v4/releases/download/v5.0.0-beta.1/book-genesis-5-video-kit-en.zip) for both MP4s, posters, English SRT/WebVTT subtitles, and posting copy. [Edit the Remotion source](../video-demo/imagination/README.md) or use the [platform copy](../marketing/video-social-copy.md).

The existing [full marketing kit](../marketing/README.md) includes launch images, a carousel, a press kit, and the 14-day calendar.
