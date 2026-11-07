# Shot detection — how it works, and where it fails

## Method

shotxray runs ffmpeg once with the `select` filter:

```
ffmpeg -i video.mp4 -vf "select='gt(scene,0.35)',showinfo" -an -f null -
```

For every frame, ffmpeg computes a **scene score** (0–1) for how much the
frame changed from the previous one. Any frame scoring above the threshold
starts a new shot. Shot 1 always starts at `0.0`; the last shot ends at the
video duration. Detections closer than 0.1s apart are merged (encoder noise,
not real cuts).

The default threshold is **0.35**. Lower it to catch subtler cuts
(`--threshold 0.2`); raise it if one long take is being split into pieces
(`--threshold 0.5`).

## What the score actually measures

The scene score is based on the **luma (brightness) difference** between
consecutive frames. That has two honest consequences:

1. **A hard cut between two shots of similar brightness can be missed.**
   The classic case: a cut from a red frame to a green frame of the same
   luminance scores near zero, because the detector never looks at colour.
   If you suspect missed cuts, re-run with a lower threshold — or check the
   timeline in `report.html` against the footage.
2. **Slow dissolves and fades score low.** A 2-second cross-dissolve changes
   a little per frame, so no single frame crosses the threshold. The
   boundary is reported at (or just after) the dissolve instead of at its
   start. shotxray never claims a dissolve is a hard cut; the brief says
   "no dissolve was detected" only for cuts the detector actually found.

## What it does not do

- No camera-movement detection (pan/tilt/zoom). A static shot and a slow
  pan of the same scene look identical to the detector.
- No content understanding: it cannot tell a jump cut from a match cut, or
  a B-roll insert from an A-roll continuation.
- No ML. The detector is deterministic: the same file and threshold always
  give the same shot list, which is what makes the output usable as an
  agent-readable contract.

## Verifying a shot list

If a shot list looks wrong, the fastest check is the thumbnails: open
`report.html` and look at the first frame of each shot. A missed cut shows
up as one "shot" whose thumbnail obviously contains two different scenes.
Re-run with `--threshold 0.2` and compare.

## Test evidence

The test suite (`tests/test_shotxray.py`) synthesises a 3-scene video with
hard cuts at 2.0s and 4.0s and asserts the detector returns exactly those
boundaries (±0.25s). The colours are chosen with very different luma
(white/black/red) precisely because of the limitation above — a fixture
that accidentally relies on invisible cuts would be testing nothing.
