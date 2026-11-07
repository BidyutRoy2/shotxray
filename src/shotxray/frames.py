"""Per-shot visuals: thumbnails, dominant colour, brightness.

All frames are pulled with ffmpeg; the colour/brightness math is plain
Python on raw pixels, so there are no image-library dependencies.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .errors import AnalysisError
from .probe import check_ffmpeg


def _run_ffmpeg(args: list[str], what: str) -> subprocess.CompletedProcess:
    ffmpeg, _ = check_ffmpeg()
    proc = subprocess.run([ffmpeg, "-hide_banner", "-v", "error"] + args,
                          capture_output=True, timeout=300)
    if proc.returncode != 0:
        detail = (proc.stderr or b"").decode(errors="replace").strip().splitlines()
        hint = detail[-1] if detail else "unknown error"
        raise AnalysisError(f"{what} failed: {hint}")
    return proc


def extract_thumbnail(path: str, timestamp: float, out_path: str, width: int = 320) -> str:
    """Save one frame as PNG at *timestamp*. Returns the written path."""
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    _run_ffmpeg(
        ["-ss", f"{timestamp:.3f}", "-i", path,
         "-frames:v", "1", "-vf", f"scale={width}:-1", "-y", out_path],
        f"thumbnail extraction at {timestamp:.2f}s",
    )
    return out_path


def dominant_color(path: str, timestamp: float) -> str:
    """Average colour of the frame at *timestamp*, as ``#rrggbb``.

    The frame is scaled to 1x1 pixel, so the single pixel *is* the average.
    """
    proc = _run_ffmpeg(
        ["-ss", f"{timestamp:.3f}", "-i", path,
         "-frames:v", "1", "-vf", "scale=1:1",
         "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
        f"dominant-colour read at {timestamp:.2f}s",
    )
    raw = proc.stdout
    if len(raw) < 3:
        raise AnalysisError(f"could not read pixels at {timestamp:.2f}s")
    r, g, b = raw[0], raw[1], raw[2]
    return f"#{r:02x}{g:02x}{b:02x}"


def brightness(path: str, timestamp: float) -> int:
    """Mean luma (0-255) of the frame at *timestamp*."""
    proc = _run_ffmpeg(
        ["-ss", f"{timestamp:.3f}", "-i", path,
         "-frames:v", "1", "-vf", "scale=1:1",
         "-pix_fmt", "gray", "-f", "rawvideo", "-"],
        f"brightness read at {timestamp:.2f}s",
    )
    raw = proc.stdout
    if len(raw) < 1:
        raise AnalysisError(f"could not read luma at {timestamp:.2f}s")
    return raw[0]


def brightness_label(value: int | None) -> str:
    if value is None:
        return "unknown"
    if value < 40:
        return "very dark"
    if value < 90:
        return "dark"
    if value < 170:
        return "balanced"
    if value < 220:
        return "bright"
    return "very bright"
