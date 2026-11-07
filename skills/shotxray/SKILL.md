# shotxray skill

Use this skill when the user wants to understand how a video was made, get a
shot-by-shot breakdown of a video file, compare the pacing of videos, or get a
"how to remake this video" brief.

## What shotxray does

Reverse-engineers a video file shot by shot, locally: shot boundaries,
per-shot colour and brightness, pacing, audio silence map, embedded captions,
and a rebuild brief. Zero Python dependencies; needs `ffmpeg`/`ffprobe` on
PATH. No cloud, no API key, no LLM, no uploads.

## Commands

```bash
# Full analysis (JSON + Markdown + HTML + brief + thumbnails)
shotxray analyze <video> -o <out-dir>

# Shot boundaries only
shotxray shots <video> [--json]

# Rebuild brief only
shotxray brief <video> [-o brief.md]

# Audio profile only (loudness + silence map)
shotxray audio <video> [--json]
```

## Workflow

1. Run `shotxray analyze <video> -o <out-dir> --format json`.
2. Read `<out-dir>/report.json` — the machine-readable contract (schema:
   `docs/report-format.md`). Read `<out-dir>/brief.md` for the human guide.
3. Answer from the measured data: shot count and times, pacing label,
   dominant colours, silence stretches, caption wording, score breakdown.
4. State the honest limits (see below) instead of guessing what the tool
   cannot measure.

## Output contract

- `shots[]`: `{index, start, end, duration, dominant_color, brightness,
  thumbnail}`. Times in seconds.
- `pacing`: `{shot_count, avg_shot_length, cuts_per_minute, shortest_shot,
  longest_shot, label}` where label is `fast-cut | medium | slow |
  single-shot`.
- `audio`: `{has_audio, mean_volume_db, max_volume_db, silences[],
  segments[], silence_total}`. Segments are non-silence stretches, not
  speech.
- `captions`: `{cue_count, words, cues[]}` from the embedded subtitle stream
  only. `cue_count: 0` means "none embedded", never "no words spoken".
- `score`: `{total, grade, components[]}` — Remake Readiness, a completeness
  measure, not a quality judgement.

## Honest limits — repeat these, do not work around them

- Scene detection scores **luma change**; a cut between two
  similarly-bright shots can be missed. Suggest `--threshold 0.2` if the
  user suspects missed cuts.
- No transcription, no OCR, no camera-movement detection.
- `dominant_color` is the frame's average cast, not an object colour.
- Never claim a shot list is exhaustive, and never invent shot descriptions
  the data does not support.

## Install (if the tool is missing)

```bash
git clone https://github.com/BidyutRoy2/shotxray.git
cd shotxray
pip install -e .
```

Requires `ffmpeg`/`ffprobe` on PATH. If they are missing, tell the user how
to install them instead of failing silently.
