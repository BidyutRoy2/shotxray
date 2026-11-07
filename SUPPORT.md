# Support

## Getting help

- **First stop:** the [README](README.md) and the guides in [`docs/`](docs/)
  — `usage.md` covers every command, `shot-detection.md` explains the
  detector and its limits, `report-format.md` documents the JSON output.
- **Bugs and feature requests:** open a GitHub Issue using the templates in
  `.github/ISSUE_TEMPLATE/`.
- **Questions / discussion:** open an Issue with the "question" label and a
  clear title; include your command, shotxray version, and ffmpeg version.

## Before you report a problem

1. Check you have ffmpeg and ffprobe on PATH: `ffmpeg -version`.
2. Check the version: `shotxray --version`.
3. Try the sample video — if it works and yours doesn't, the difference is
   in the file: `shotxray analyze examples/sample-video.mp4`.
4. Try a lower scene threshold if shots are missed:
   `shotxray analyze video.mp4 --threshold 0.2`.

## Scope of support

shotxray is maintained by one person in their spare time. Issues with a
minimal reproduction (or a clear description of the video's properties) get
answered fastest. Feature requests are welcome; the ground rules in
[CONTRIBUTING.md](CONTRIBUTING.md) (zero dependencies, no network, honest
output) decide what gets built.
