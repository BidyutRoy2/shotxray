"""Embedded captions / subtitles.

Only reads a subtitle stream that is already in the file (e.g. mov_text in
mp4, srt/ass in mkv). shotxray does NOT transcribe speech — that would need
a speech model. A video without embedded captions honestly reports none.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field

from .probe import check_ffmpeg

_CUE_RE = re.compile(
    r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})"
)


@dataclass
class Cue:
    start: str
    end: str
    text: str

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "text": self.text}


@dataclass
class CaptionTrack:
    codec: str | None
    cues: list[Cue] = field(default_factory=list)

    @property
    def cue_count(self) -> int:
        return len(self.cues)

    @property
    def words(self) -> int:
        return sum(len(c.text.split()) for c in self.cues)

    def to_dict(self) -> dict:
        return {
            "codec": self.codec,
            "cue_count": self.cue_count,
            "words": self.words,
            "cues": [c.to_dict() for c in self.cues],
        }


def _srt_timestamp_to_seconds(raw: str) -> float:
    h, m, rest = raw.replace(",", ".").split(":")
    s, ms = rest.split(".")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse_srt(text: str) -> list[Cue]:
    """Parse SRT text into cues. Tolerant of numbering and blank-line quirks."""
    cues: list[Cue] = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        # First line may be a cue number; the timing line is the one with "-->".
        timing_idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if timing_idx is None:
            continue
        match = _CUE_RE.search(lines[timing_idx])
        if not match:
            continue
        text_lines = lines[timing_idx + 1:]
        if not text_lines:
            continue
        cues.append(Cue(
            start=match.group(1).replace(",", "."),
            end=match.group(2).replace(",", "."),
            text=" ".join(text_lines),
        ))
    return cues


def extract_captions(path: str, codec: str | None) -> CaptionTrack | None:
    """Extract the first subtitle stream as SRT. None when there is none."""
    ffmpeg, _ = check_ffmpeg()
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-v", "error", "-i", path,
         "-map", "0:s:0", "-f", "srt", "-"],
        capture_output=True, text=True, timeout=300,
    )
    if proc.returncode != 0 or not (proc.stdout or "").strip():
        return None
    cues = parse_srt(proc.stdout)
    if not cues:
        return None
    return CaptionTrack(codec=codec, cues=cues)
