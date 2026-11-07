# Usage

## Install

shotxray needs Python 3.10+ and `ffmpeg`/`ffprobe` on your PATH.

```bash
git clone https://github.com/BidyutRoy2/shotxray.git
cd shotxray
pip install -e .
```

Verify: `shotxray --version` → `shotxray 0.1.0`. If ffmpeg is missing,
shotxray tells you how to install it instead of failing cryptically.

> The package is not on PyPI yet, so there is no `pip install shotxray`
> quickstart. Source install (above) is the only install path for v0.1.0.

## Commands

### `shotxray analyze VIDEO [-o DIR] [--format all|json|md|html] [--threshold N] [--no-thumbs]`

The full pipeline. Writes into `DIR` (default `shotxray-report/`):

| File | Contents |
|---|---|
| `report.json` | Machine-readable everything (see `report-format.md`) |
| `report.md` | Human-readable report |
| `report.html` | Dark-mode-aware HTML report with timeline + thumbnails |
| `brief.md` | Rebuild brief — how to remake the video |
| `thumbs/shot-NN.png` | One mid-shot frame per shot |

`--format json` (or `md`/`html`) writes only that report plus `brief.md`.
`--no-thumbs` skips frame extraction (faster; the HTML report then has no
images). `--threshold` tunes shot sensitivity — see `shot-detection.md`.

Exit code is `0` on success, `1` on a handled error (missing file, unreadable
video, ffmpeg failure) with the reason on stderr.

### `shotxray shots VIDEO [--threshold N] [--json]`

Shot boundaries only. The table form prints `# / start / end / length`.
`--json` prints `{"video", "duration", "shots": [...], "pacing": {...}}`.

### `shotxray brief VIDEO [-o FILE] [--threshold N]`

Prints the rebuild brief to stdout, or writes it to `FILE`. Runs the full
pipeline internally (thumbnails skipped), so it costs the same as `analyze`.

### `shotxray audio VIDEO [--json]`

Loudness (`volumedetect`) and the silence map (`silencedetect`) only.
Prints `No audio stream in this file.` and exits `0` when there is none.

## Workflows

**Study one video before remaking it:**

```bash
shotxray analyze reference.mp4 -o ref-report
# read ref-report/brief.md, then open ref-report/report.html
```

**Compare pacing across a folder:**

```bash
for f in clips/*.mp4; do
  shotxray shots "$f" --json > "reports/$(basename "$f" .mp4).json"
done
# each JSON has pacing.avg_shot_length and pacing.cuts_per_minute
```

**Feed an agent the structure:**

```bash
shotxray analyze video.mp4 -o report --format json
# hand report/report.json to your coding agent with skills/shotxray/SKILL.md
```

## Performance notes

- Scene detection is one ffmpeg pass over the video; a 10-minute 1080p file
  typically analyses in well under a minute on a laptop.
- Thumbnails cost one ffmpeg invocation per shot — negligible next to the
  detection pass.
- Nothing is uploaded. The largest cost is disk: reports are a few KB plus
  ~50–150 KB per thumbnail.
