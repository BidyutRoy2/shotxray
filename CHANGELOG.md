# Changelog

All notable changes to shotxray will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-11-07

### Added

- `shotxray analyze` — full pipeline: ffprobe metadata, scene-change shot
  detection, per-shot thumbnails, dominant colour and brightness, audio
  loudness + silence map, embedded-caption extraction, Remake Readiness
  score (0–100), and a rebuild brief (`brief.md`).
- `shotxray shots` — shot boundaries as a table or JSON.
- `shotxray brief` — the rebuild brief on stdout or to a file.
- `shotxray audio` — audio profile (loudness + silence map) as text or JSON.
- Report renderers: JSON (`report.json`), Markdown (`report.md`) and a
  dark-mode-aware HTML report (`report.html`) with a colour-coded shot
  timeline and per-shot thumbnails.
- Tunable scene threshold (`--threshold`, default 0.35).
- Zero Python dependencies (stdlib only); ffmpeg/ffprobe are the only
  external tools.
- `skills/shotxray/SKILL.md` so coding agents can drive the tool.
- Docs: `docs/usage.md`, `docs/shot-detection.md`, `docs/report-format.md`,
  `docs/comparison.md`, `docs/agent-context.md`.
- Examples: a 6-second sample video plus the exact reports it produces.
