# Agent context — shotxray for coding agents

Give an agent this file plus a `report.json` and it can reason about a video
without watching it.

## What shotxray is

A zero-dependency Python CLI that reverse-engineers a video file shot by
shot, locally, using ffmpeg/ffprobe. It never uploads anything and never
needs an API key. Its output is deterministic for a given file + threshold.

## How to use it from an agent session

```bash
# Analyse and get the machine-readable report
shotxray analyze <video> -o <out-dir> --format json

# Read <out-dir>/report.json (schema: docs/report-format.md)
# Read <out-dir>/brief.md for the human remake guide
```

The `SKILL.md` in `skills/shotxray/` is the agent-facing contract: install
it in the agent's skills directory and invoke it with "analyse this video".

## What the numbers mean (so the agent does not over-claim)

- `shots[]` are cut boundaries from luma-based scene detection. A cut
  between two similarly-bright shots can be missed — see
  `docs/shot-detection.md`. Never claim a shot list is exhaustive without
  that caveat.
- `dominant_color` is the average colour of the mid-shot frame (1×1 pixel
  average). It describes the frame's overall cast, not any object in it.
- `pacing.label` is derived from average shot length only: fast-cut <2s,
  medium ≤6s, slow >6s, single-shot for one shot.
- `audio.segments` are stretches of non-silence, not speech. Silence
  detection finds pauses, not content — do not label a segment "speech" or
  "music" from this data alone.
- `captions` come only from an embedded subtitle stream. No captions means
  "none embedded", never "the video has no words".
- `score.total` (Remake Readiness) measures how much structure could be
  measured, not how good the video is. A 60/100 video can be brilliant;
  it just has no captions and no audio stream.

## Safe patterns

- Analyse files the user points at. Do not download videos from platforms
  on the user's behalf without being asked, and respect creators' rights.
- Quote timestamps and colours from `report.json`; do not invent shot
  descriptions the data does not support.
- When the brief says "what shotxray cannot tell you", repeat that limit
  instead of filling it in from a guess.
