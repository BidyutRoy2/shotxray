# Security Policy

## Supported versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a vulnerability

shotxray is a local CLI: it reads video files you point it at and shells out
to `ffmpeg`/`ffprobe`. The most likely security issues are therefore:

- **Command injection** through a crafted filename or video metadata reaching
  a shell (shotxray passes arguments as a list, never through a shell — but
  if you find a path that does, that is a bug).
- **Path traversal** in report output (thumbnails / report files written
  outside the requested `--out` directory).
- **Denial of service** through a crafted video that makes analysis hang or
  consume unbounded memory/disk.

If you find one of these — or anything else — please report it via a
**private** GitHub Security Advisory on this repo, or open an issue titled
"SECURITY:" with minimal detail and ask for a private contact. Do **not**
open a public issue with a working exploit.

Please include: shotxray version, ffmpeg version, OS, and the smallest
reproduction you can make. We will acknowledge within 7 days and aim to fix
confirmed issues in the next patch release.

## What shotxray does not do (by design)

- No network access of any kind: no uploads, no downloads, no telemetry.
- No execution of code found inside a video file; only ffmpeg/ffprobe read it.
- No credentials, tokens, or secrets are handled anywhere in the tool.
