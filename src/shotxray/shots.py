"""Shot-boundary detection via ffmpeg's scene-change filter.

Method (deterministic, no ML): ffmpeg's ``select`` filter scores every frame
for how much it changed from the previous one (``scene`` score 0..1). Any
frame scoring above the threshold starts a new shot. Hard cuts score close
to 1.0; dissolves and fades score lower, so the threshold is user-tunable.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

from .errors import AnalysisError
from .probe import check_ffmpeg

_SHOWINFO_RE = re.compile(r"pts_time:([0-9]+(?:\.[0-9]+)?)")
DEFAULT_THRESHOLD = 0.35


@dataclass
class Shot:
    """One continuous shot (no cut inside it)."""

    index: int  # 1-based
    start: float  # seconds
    end: float  # seconds
    mid: float = 0.0  # middle timestamp, used for thumbnails
    dominant_color: str | None = None  # "#rrggbb"
    brightness: int | None = None  # 0-255 mean luma at mid-frame
    thumbnail: str | None = None  # filename of the extracted frame

    def __post_init__(self) -> None:
        self.mid = round((self.start + self.end) / 2, 3)

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 3)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start": self.start,
            "end": self.end,
            "duration": self.duration,
            "dominant_color": self.dominant_color,
            "brightness": self.brightness,
            "thumbnail": self.thumbnail,
        }


@dataclass
class Pacing:
    """How fast the video cuts."""

    shot_count: int
    avg_shot_length: float
    cuts_per_minute: float
    shortest_shot: float
    longest_shot: float
    label: str  # "fast-cut" | "medium" | "slow" | "single-shot"

    def to_dict(self) -> dict:
        return {
            "shot_count": self.shot_count,
            "avg_shot_length": self.avg_shot_length,
            "cuts_per_minute": self.cuts_per_minute,
            "shortest_shot": self.shortest_shot,
            "longest_shot": self.longest_shot,
            "label": self.label,
        }


def _label_pacing(avg_shot_length: float, shot_count: int) -> str:
    if shot_count <= 1:
        return "single-shot"
    if avg_shot_length < 2.0:
        return "fast-cut"
    if avg_shot_length <= 6.0:
        return "medium"
    return "slow"


def detect_shots(path: str, duration: float, threshold: float = DEFAULT_THRESHOLD) -> list[Shot]:
    """Return the shot list for *path*.

    Shot 1 always starts at 0.0. Every later shot starts at a detected
    scene change. The last shot ends at *duration*.
    """
    ffmpeg, _ = check_ffmpeg()
    if not (0.0 < threshold <= 1.0):
        raise AnalysisError(f"scene threshold must be between 0 and 1, got {threshold}")

    cmd = [
        ffmpeg, "-hide_banner", "-i", path,
        "-vf", f"select='gt(scene,{threshold})',showinfo",
        "-an", "-f", "null", "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip().splitlines()
        hint = detail[-1] if detail else "unknown error"
        raise AnalysisError(f"scene detection failed for {path!r}: {hint}")

    starts: list[float] = []
    for line in (proc.stderr or "").splitlines():
        if "showinfo" not in line:
            continue
        match = _SHOWINFO_RE.search(line)
        if match:
            starts.append(float(match.group(1)))

    # First selected frame is ~0.0 (ffmpeg scores it 1.0). Normalise.
    starts = sorted({round(t, 3) for t in starts if t >= 0})
    if not starts or starts[0] > 0.05:
        starts.insert(0, 0.0)
    else:
        starts[0] = 0.0

    # Drop detections closer than 0.1s apart (encoder noise, not real cuts).
    cleaned: list[float] = []
    for t in starts:
        if not cleaned or t - cleaned[-1] >= 0.1:
            cleaned.append(t)
    starts = cleaned

    total = duration if duration and duration > 0 else (starts[-1] + 1.0)
    shots: list[Shot] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else total
        end = min(end, total)
        if end <= start:  # degenerate detection at the very end of the file
            continue
        shots.append(Shot(index=len(shots) + 1, start=round(start, 3), end=round(end, 3)))
    if not shots:  # pragma: no cover - defensive; a video always has frame 0
        shots.append(Shot(index=1, start=0.0, end=round(total, 3)))
    return shots


def pacing(shots: list[Shot], duration: float) -> Pacing:
    """Summarise cutting rhythm from a shot list."""
    lengths = [s.duration for s in shots]
    avg = round(sum(lengths) / len(lengths), 2) if lengths else 0.0
    cuts = max(len(shots) - 1, 0)
    cpm = round(cuts / (duration / 60), 1) if duration and duration > 0 else 0.0
    return Pacing(
        shot_count=len(shots),
        avg_shot_length=avg,
        cuts_per_minute=cpm,
        shortest_shot=round(min(lengths), 2) if lengths else 0.0,
        longest_shot=round(max(lengths), 2) if lengths else 0.0,
        label=_label_pacing(avg, len(shots)),
    )
