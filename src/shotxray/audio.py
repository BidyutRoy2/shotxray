"""Audio profile: loudness + silence map.

Silence detection is the honest, measurable half of "what does the audio
do": pauses between speech, dead air at the start/end, and music-vs-talk
segmentation — all from ffmpeg's silencedetect, no speech recognition.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

from .errors import AnalysisError
from .probe import check_ffmpeg

_SILENCE_START = re.compile(r"silence_start:\s*([0-9.]+)")
_SILENCE_END = re.compile(r"silence_end:\s*([0-9.]+)\s*\|\s*silence_duration:\s*([0-9.]+)")
_MEAN_VOL = re.compile(r"mean_volume:\s*(-?[0-9.]+)\s*dB")
_MAX_VOL = re.compile(r"max_volume:\s*(-?[0-9.]+)\s*dB")


@dataclass
class Silence:
    start: float
    end: float

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 2)

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "duration": self.duration}


@dataclass
class AudioSegment:
    """A stretch of non-silence (speech, music, or noise)."""

    start: float
    end: float

    @property
    def duration(self) -> float:
        return round(self.end - self.start, 2)

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "duration": self.duration}


@dataclass
class AudioProfile:
    has_audio: bool
    mean_volume_db: float | None = None
    max_volume_db: float | None = None
    silences: list[Silence] = field(default_factory=list)
    segments: list[AudioSegment] = field(default_factory=list)

    @property
    def silence_total(self) -> float:
        return round(sum(s.duration for s in self.silences), 2)

    @property
    def silence_share(self) -> float | None:
        return None  # filled by analyse_audio() once duration is known

    def to_dict(self) -> dict:
        return {
            "has_audio": self.has_audio,
            "mean_volume_db": self.mean_volume_db,
            "max_volume_db": self.max_volume_db,
            "silences": [s.to_dict() for s in self.silences],
            "segments": [s.to_dict() for s in self.segments],
            "silence_total": self.silence_total,
        }


def _segments_from_silences(silences: list[Silence], duration: float) -> list[AudioSegment]:
    """Invert the silence list into non-silence segments."""
    segments: list[AudioSegment] = []
    cursor = 0.0
    for s in silences:
        if s.start - cursor >= 0.2:
            segments.append(AudioSegment(start=round(cursor, 3), end=round(s.start, 3)))
        cursor = max(cursor, s.end)
    if duration - cursor >= 0.2:
        segments.append(AudioSegment(start=round(cursor, 3), end=round(duration, 3)))
    return segments


def analyse_audio(path: str, duration: float, noise_db: int = -40, min_silence: float = 0.3) -> AudioProfile:
    """Build the audio profile for *path* (no audio stream → has_audio=False)."""
    ffmpeg, _ = check_ffmpeg()

    vol = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", path, "-vn",
         "-af", "volumedetect", "-f", "null", "-"],
        capture_output=True, text=True, timeout=600,
    )
    stderr = vol.stderr or ""
    if "Stream map" not in stderr and "Audio:" not in stderr and vol.returncode != 0:
        # No audio stream at all: ffmpeg reports "does not contain any stream".
        return AudioProfile(has_audio=False)

    mean = _MEAN_VOL.search(stderr)
    maxv = _MAX_VOL.search(stderr)
    if mean is None and maxv is None:
        return AudioProfile(has_audio=False)

    sil = subprocess.run(
        [ffmpeg, "-hide_banner", "-i", path, "-vn",
         "-af", f"silencedetect=noise={noise_db}dB:d={min_silence}",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=600,
    )
    if sil.returncode != 0:
        raise AnalysisError("silence detection failed")

    silences: list[Silence] = []
    open_start: float | None = None
    for line in (sil.stderr or "").splitlines():
        m_start = _SILENCE_START.search(line)
        if m_start:
            open_start = float(m_start.group(1))
            continue
        m_end = _SILENCE_END.search(line)
        if m_end and open_start is not None:
            silences.append(Silence(start=round(open_start, 3), end=round(float(m_end.group(1)), 3)))
            open_start = None
    # A silence running to the end of the file has no silence_end line.
    if open_start is not None and duration:
        silences.append(Silence(start=round(open_start, 3), end=round(duration, 3)))

    profile = AudioProfile(
        has_audio=True,
        mean_volume_db=float(mean.group(1)) if mean else None,
        max_volume_db=float(maxv.group(1)) if maxv else None,
        silences=silences,
        segments=_segments_from_silences(silences, duration or 0.0),
    )
    return profile
