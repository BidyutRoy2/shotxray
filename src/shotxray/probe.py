"""Video metadata via ffprobe (stdlib only).

Everything here is read-only: shotxray never modifies the input video.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from fractions import Fraction

from .errors import FFmpegMissingError, ProbeError

SUPPORTED_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".flv", ".wmv",
    ".mpg", ".mpeg", ".3gp", ".ts", ".m2ts",
}


def check_ffmpeg() -> tuple[str, str]:
    """Return (ffmpeg, ffprobe) paths or raise a helpful error."""
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        missing = [n for n, p in (("ffmpeg", ffmpeg), ("ffprobe", ffprobe)) if not p]
        raise FFmpegMissingError(
            f"shotxray needs {', '.join(missing)} on your PATH. Install it from "
            "https://ffmpeg.org/download.html "
            "(macOS: brew install ffmpeg · Ubuntu/Debian: sudo apt install ffmpeg · "
            "Windows: winget install ffmpeg)."
        )
    return ffmpeg, ffprobe


def _parse_fps(raw: str | None) -> float | None:
    if not raw or raw in ("0/0", "N/A"):
        return None
    try:
        value = float(Fraction(raw))
    except (ValueError, ZeroDivisionError):
        return None
    return value if value > 0 else None


def _parse_float(raw) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value


@dataclass
class VideoInfo:
    """Everything ffprobe knows about a video file."""

    path: str
    duration: float | None = None
    width: int | None = None
    height: int | None = None
    fps: float | None = None
    video_codec: str | None = None
    audio_codec: str | None = None
    subtitle_codec: str | None = None
    bitrate: int | None = None
    format_name: str | None = None
    has_audio: bool = False
    has_subtitles: bool = False
    has_video: bool = False
    creation_time: str | None = None
    streams: list[dict] = field(default_factory=list)
    chapters: list[dict] = field(default_factory=list)

    @property
    def aspect(self) -> str | None:
        if not self.width or not self.height:
            return None
        ratio = self.width / self.height
        if abs(ratio - 16 / 9) < 0.05:
            return "16:9 widescreen"
        if abs(ratio - 9 / 16) < 0.05:
            return "9:16 vertical"
        if abs(ratio - 1.0) < 0.05:
            return "1:1 square"
        if abs(ratio - 4 / 3) < 0.05:
            return "4:3 classic"
        if abs(ratio - 21 / 9) < 0.1:
            return "21:9 ultrawide"
        return f"{self.width}:{self.height}"

    @property
    def resolution_label(self) -> str | None:
        if not self.height:
            return None
        if self.height >= 2160:
            return "4K"
        if self.height >= 1440:
            return "1440p"
        if self.height >= 1080:
            return "1080p"
        if self.height >= 720:
            return "720p"
        if self.height >= 480:
            return "480p"
        return f"{self.height}p"

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "video_codec": self.video_codec,
            "audio_codec": self.audio_codec,
            "subtitle_codec": self.subtitle_codec,
            "bitrate": self.bitrate,
            "format_name": self.format_name,
            "has_audio": self.has_audio,
            "has_subtitles": self.has_subtitles,
            "has_video": self.has_video,
            "creation_time": self.creation_time,
            "aspect": self.aspect,
            "resolution_label": self.resolution_label,
            "chapters": self.chapters,
        }


def probe(path: str) -> VideoInfo:
    """Run ffprobe and return structured metadata for *path*.

    Raises ProbeError when the file cannot be read as a video.
    """
    _, ffprobe = check_ffmpeg()
    cmd = [
        ffprobe, "-v", "error",
        "-print_format", "json",
        "-show_format", "-show_streams", "-show_chapters",
        path,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError as exc:  # pragma: no cover - guarded by check_ffmpeg
        raise FFmpegMissingError("ffprobe disappeared from PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise ProbeError(f"ffprobe timed out reading {path!r}") from exc

    if proc.returncode != 0 or not proc.stdout.strip():
        detail = (proc.stderr or "").strip().splitlines()
        hint = detail[-1] if detail else "unknown error"
        raise ProbeError(f"ffprobe could not read {path!r}: {hint}")

    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ProbeError(f"ffprobe returned unreadable output for {path!r}") from exc

    info = VideoInfo(path=path)
    fmt = data.get("format") or {}
    info.format_name = fmt.get("format_name")
    info.duration = _parse_float(fmt.get("duration"))
    info.bitrate = int(_parse_float(fmt.get("bit_rate")) or 0) or None
    info.creation_time = (fmt.get("tags") or {}).get("creation_time")
    info.chapters = [
        {"start": _parse_float(c.get("start_time")), "title": (c.get("tags") or {}).get("title")}
        for c in data.get("chapters") or []
    ]
    info.streams = data.get("streams") or []

    for stream in info.streams:
        kind = stream.get("codec_type")
        if kind == "video" and not info.has_video:
            info.has_video = True
            info.width = stream.get("width")
            info.height = stream.get("height")
            info.video_codec = stream.get("codec_name")
            info.fps = _parse_fps(stream.get("avg_frame_rate")) or _parse_fps(stream.get("r_frame_rate"))
            if info.duration is None:
                info.duration = _parse_float(stream.get("duration"))
        elif kind == "audio" and not info.has_audio:
            info.has_audio = True
            info.audio_codec = stream.get("codec_name")
        elif kind == "subtitle" and not info.has_subtitles:
            info.has_subtitles = True
            info.subtitle_codec = stream.get("codec_name")

    if not info.has_video:
        raise ProbeError(
            f"{path!r} has no video stream — shotxray analyses video files "
            "(mp4, mov, mkv, webm, avi, …). Audio-only files are not supported."
        )
    return info
