# Comparison — where shotxray sits

The week shotxray was built, GitHub trending was dominated by tools that
study how something works and rebuild it: `rea` (+3,859 stars/day),
`craft-anything` (+3,066/day) and the new `rea-video`, which reverse-engineers
videos shot by shot. shotxray is the small, local member of that family —
for video files on your disk, with no model and no upload.

| Tool | Object studied | Method | Needs | Output |
|---|---|---|---|---|
| **shotxray** | Your video files | ffmpeg scene detection + measured structure | ffmpeg only | Shot list, pacing, audio map, rebuild brief |
| rea-video | Videos (AI) | Model-based shot analysis | Model / API access | Shot-by-shot remake plan |
| rea | Any app (binary, JS, Electron, .NET) | Agent + native reverse-engineering tools | Agent, Ghidra/Hopper | Evidence-backed "how it works" |
| craft-anything | Any app or game | Inspect first, agent rebuilds second | Agent | Rebuilt app in your stack |
| appstudy | A website's public surface | Static crawl of sitemap/nav/forms/CTAs | Python only | Rebuild brief (no code/assets) |
| Manual ffprobe + ffmpeg | Your video files | Hand-assembled commands | Your time | Raw numbers |

## When to pick shotxray

- You want the structure of **one specific file**, now, offline.
- You want a **deterministic, repeatable** shot list (same file + threshold =
  same output) to hand to an agent or a script.
- You do not want to upload footage, pay per minute, or manage an API key.

## When not to

- You need **transcription** (speech-to-text) — out of scope; use a speech
  model and feed the transcript in alongside the shot list.
- You need **camera-movement or semantic analysis** ("this is a drone shot")
  — that needs a vision model, not a scene-change score.
- You are analysing **someone else's video to copy it frame-for-frame**.
  shotxray measures structure; what you do with it is your responsibility.
  Studying a video to learn its pacing is normal craft. Re-uploading a
  near-identical copy is not.
