# Examples

## `sample-video.mp4` — try it now

A 6-second, 1280x720, 30 fps video synthesised with ffmpeg: three hard-cut
colour scenes (yellow 2s, blue 2s, red 2s) plus a sine tone that is silent
between 2s and 3s. It exists so you can see a full analysis without finding
a video first.

```bash
shotxray analyze examples/sample-video.mp4
```

Expected output:

```
Video:  examples/sample-video.mp4 (6.0s, 1280x720, 30.0 fps)
Shots:  3 (medium, avg 2.0s, 20.0 cuts/min)
Audio:  yes — 1.0s silence
Score:  85/100 (B)
```

(85, not 100: the file has no embedded captions, so the 15 caption points
are honestly missing — see the score breakdown in the report.)

## The reports it produces

- [`sample-report.md`](sample-report.md) — the human-readable report
- [`sample-report.json`](sample-report.json) — the machine-readable report
- [`sample-brief.md`](sample-brief.md) — the rebuild brief

## Regenerating the sample video

```bash
ffmpeg -y -f lavfi -i color=c=yellow:s=1280x720:r=30:d=2 \
  -f lavfi -i color=c=blue:s=1280x720:r=30:d=2 \
  -f lavfi -i color=c=red:s=1280x720:r=30:d=2 \
  -f lavfi -i "aevalsrc='sin(2*PI*440*t)*(lt(t,2)+gt(t,3))':duration=6" \
  -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]" \
  -map "[v]" -map "3:a" -c:v libx264 -pix_fmt yuv420p -c:a aac \
  -shortest examples/sample-video.mp4
```

The colours are chosen with very different luma on purpose — ffmpeg's scene
detector scores brightness change, so a red→green cut of equal luminance
would be invisible to it. See `docs/shot-detection.md`.
