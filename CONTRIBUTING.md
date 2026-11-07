# Contributing to shotxray

Thanks for considering a contribution. shotxray is a small tool with a
deliberate scope — local, zero-dependency, honest about what it measures —
so the most useful contributions are the ones that keep it that way.

## How to contribute

1. Fork the repo and create a branch from `main`.
2. Make your change. Keep new code in `src/shotxray/` and tests in `tests/`.
3. Run the test suite: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
   (tests synthesise their own videos with ffmpeg — no fixtures needed).
4. If you change CLI behaviour, update `README.md` and `docs/usage.md`.
5. Open a pull request using the template in `.github/PULL_REQUEST_TEMPLATE.md`.

## Ground rules

- **Zero Python dependencies.** The runtime is stdlib only. ffmpeg/ffprobe are
  the only external tools, and they must stay optional-to-install, never
  vendored. If a feature needs a new library, it is probably out of scope.
- **No network code.** shotxray never uploads, downloads, phones home, or
  requires an account or API key. Keep it that way.
- **Honest output.** If a measurement is impossible (no captions, no audio,
  a cut the detector cannot see), say so in the report — never invent data
  to fill the gap.
- **Original work only.** Do not copy code, prompts, or text from other
  projects. Clean-room implementations of documented ffmpeg behaviour are
  fine; copied code is not.
- **Tests for behaviour, not for show.** Every new analysis feature needs a
  test that runs against a synthesised video and asserts on real decoded
  output.

## Reporting bugs

Use the bug-report template (`.github/ISSUE_TEMPLATE/bug_report.yml`) and
include: the shotxray version (`shotxray --version`), your ffmpeg version
(`ffmpeg -version`), the command you ran, and — if you can share it — a
minimal video that reproduces the problem. If the video is private, describe
its properties instead (duration, resolution, codec, how the cuts look).

## Feature requests

Use the feature-request template. The best requests name a concrete video
workflow ("I edit wedding videos and need…") rather than a vague capability.
