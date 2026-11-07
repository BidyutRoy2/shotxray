# Release notes — shotxray v0.1.0

**Reverse-engineer any video, shot by shot — locally. No cloud, no API key, no LLM.**

## What it does

Point shotxray at a video file and it measures the structure that matters to
anyone who wants to understand — or remake — that video:

- **Shot detection** — every cut, found with ffmpeg's scene-change filter
- **Per-shot visuals** — thumbnail, dominant colour, brightness for each shot
- **Pacing** — average shot length, cuts/minute, fast-cut / medium / slow
- **Audio profile** — loudness plus a silence map (pauses, dead air)
- **Captions** — embedded subtitle streams extracted, never invented
- **Rebuild brief** — a shot-by-shot "how to remake it" guide (`brief.md`)
- **Remake Readiness score** — 0–100 with a per-component breakdown, so you
  can see exactly what was measured and what was missing

Reports come as JSON, Markdown, and a dark-mode-aware HTML page with a
colour-coded shot timeline. Zero Python dependencies; ffmpeg is the only
external tool.

## How to install

```bash
git clone https://github.com/BidyutRoy2/shotxray.git
cd shotxray
pip install -e .
shotxray analyze examples/sample-video.mp4
```

Requires `ffmpeg` and `ffprobe` on your PATH
([ffmpeg.org](https://ffmpeg.org/download.html)).

## How to create this release on GitHub (1 minute)

1. Upload these files to a new repo named `shotxray` on github.com/BidyutRoy2.
2. Go to **Releases → Draft a new release**.
3. Tag: `v0.1.0` · Title: `shotxray v0.1.0 — Reverse-engineer any video, shot by shot`
4. Paste the text above as the release body.
5. Publish.
