"""Remake Readiness score (0-100): how much of a video's structure shotxray
could actually measure, so the rebuild brief is grounded in real data.

The score is a completeness measure, NOT a quality judgement. A brilliant
video with no embedded captions scores lower on the captions component —
the report always says exactly which points were lost and why.
"""

from __future__ import annotations

from dataclasses import dataclass, field

GRADE_BANDS = [(90, "A"), (75, "B"), (60, "C"), (40, "D"), (0, "F")]


@dataclass
class ScoreComponent:
    name: str
    earned: int
    possible: int
    note: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "earned": self.earned,
            "possible": self.possible,
            "note": self.note,
        }


@dataclass
class ReadinessScore:
    total: int
    grade: str
    components: list[ScoreComponent] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "grade": self.grade,
            "components": [c.to_dict() for c in self.components],
        }


def grade_for(total: int) -> str:
    for floor, grade in GRADE_BANDS:
        if total >= floor:
            return grade
    return "F"


def score_readiness(
    *,
    has_duration: bool,
    has_resolution: bool,
    has_fps: bool,
    has_codec: bool,
    shot_count: int,
    shots_have_visuals: bool,
    has_audio: bool,
    has_silence_map: bool,
    caption_cues: int,
) -> ReadinessScore:
    components: list[ScoreComponent] = []

    meta = sum([has_duration, has_resolution, has_fps, has_codec])
    components.append(ScoreComponent(
        "Metadata", meta * 6 + (1 if meta == 4 else 0), 25,
        "duration, resolution, fps and codec all readable"
        if meta == 4 else f"only {meta}/4 metadata fields readable",
    ))

    shots_pts = 25 if shot_count >= 1 else 0
    components.append(ScoreComponent(
        "Shot detection", shots_pts, 25,
        f"{shot_count} shot(s) detected with clean boundaries"
        if shot_count >= 1 else "no shots detected",
    ))

    visuals_pts = 20 if shots_have_visuals else 0
    components.append(ScoreComponent(
        "Per-shot visuals", visuals_pts, 20,
        "thumbnail + dominant colour + brightness for every shot"
        if shots_have_visuals else "thumbnails/colours could not be extracted",
    ))

    audio_pts = (8 if has_audio else 0) + (7 if has_silence_map else 0)
    components.append(ScoreComponent(
        "Audio profile", audio_pts, 15,
        "loudness + silence map measured" if audio_pts == 15
        else ("audio present but silence map missing" if has_audio
              else "no audio stream — nothing to profile"),
    ))

    captions_pts = 15 if caption_cues > 0 else 0
    components.append(ScoreComponent(
        "Captions", captions_pts, 15,
        f"{caption_cues} embedded caption cue(s) found" if caption_cues > 0
        else "no embedded captions in the file (transcription is out of scope)",
    ))

    total = sum(c.earned for c in components)
    return ReadinessScore(total=total, grade=grade_for(total), components=components)
