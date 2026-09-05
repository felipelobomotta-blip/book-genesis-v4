# Imagination Edition — narrated product videos

Editable Remotion source for the English Book Genesis 5 walkthrough and vertical cut. The finished downloads are linked in the [video guide](../../docs/video-walkthrough.md).

| Composition | Picture | Timeline | Output |
| --- | --- | --- | --- |
| `BookGenesisWalkthrough` | 1920 × 1080, 30 fps | 1,797 frames / 59.9 s | Landscape walkthrough |
| `BookGenesisShort` | 1080 × 1920, 30 fps | 984 frames / 32.8 s | Vertical social cut |

The MP4 containers include a small AAC encoder tail. Their measured durations are 59.947 s and 32.853 s.

## Preview and render

This optional marketing project uses Node.js and Remotion; it adds no dependencies to the Python runner. The recorded build used Node 24.13.0, Remotion 4.0.520, and Windows. The included lockfile fixes the dependency tree.

From this directory:

```bash
npm ci
npm run studio -- --no-open
npm run render:walkthrough
npm run render:short
```

Open the local URL printed by Studio. The render commands write to `out/`. Remotion needs a compatible Chrome executable; it can download one, or you can pass an existing path:

```bash
npm run render:walkthrough -- --browser-executable="/path/to/chrome" --crf=20
```

The included narration, screenshots, and browser clips let you render without model credentials or new provider calls. `narration.json` contains the voice script; `src/timing.json` contains the measured scene durations and audio paths. The full narration subtitles are in `public/captions/` as SRT and WebVTT. On-screen captions are short highlights, not a verbatim transcript.

## What was recorded

- `public/capture-pages/`: actual Rich CLI output and capture evidence from `new`, `resume`, `--help`, and `export`, using deterministic fake provider responses. The start shot shows the resulting brief; the setup shot shows command help, not the credential wizard.
- `public/capture-*.png`: browser screenshots of that exported terminal output. Font size and background were set for readability; console text was not rewritten.
- `public/reader/index.html`: the existing English scripted reader fixture built by the repository's reader builder.
- `public/reader-*.mp4`: actual browser interactions with that reader: selecting rejected and accepted versions, changing the comparison baseline, opening the diff, and navigating chapters in the landscape clip.
- `public/voice/`: synthetic English narration using Microsoft Zira Desktop. This is not a recording or imitation of the founder.
- `public/hero.png`: existing AI-generated launch artwork from the marketing kit.

The footage carries “Scripted sample · edited for time.” It demonstrates the interface, not live generation speed, literary quality, human-reader findings, or sales performance. Provider calls can send prompts and manuscript text to the selected provider; local project storage does not imply local inference.

Export includes accepted canonical chapters. A working project can be exported before completion, with a partial label.

## Regenerate or replace assets

Install the Python repository first, then run `python scripts/capture_cli.py` to regenerate the Rich HTML and the reader fixture. It uses a new temporary project and fake responses, and does not call a real provider. The script leaves its temporary fixture directory available for inspection. Take new PNG screenshots of the resulting HTML and record any new reader interactions before replacing the matching media files.

Optional Windows narration regeneration: run `scripts/generate_voice.ps1` in a PowerShell session with the Microsoft Zira Desktop voice and FFprobe installed. It rewrites the WAVs and timing JSON. If wording or durations change, update the checkpoint scene timings and subtitles before rendering again. You can also record your own English narration and update the paths and durations directly.

Final video binaries are attached to the GitHub release rather than stored in Git. Rebuilds on another OS or with different fonts may differ visually.

## Verification record

Both compositions passed TypeScript checking and completed H.264/AAC renders. FFmpeg decoded both complete files without errors; FFprobe verified the dimensions, frame counts, and audio tracks. Scene stills and the real reader interactions were inspected. See [the media verification record](verification.json) for measured metadata. These checks verify the video delivery, not manuscript quality or production readiness of the beta.
