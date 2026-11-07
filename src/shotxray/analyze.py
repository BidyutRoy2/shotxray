"""The analysis pipeline: probe -> shots -> visuals -> audio -> captions -> score.

One function, ``analyze_video``, runs the whole pipeline and returns a
plain dict (JSON-serialisable) so the CLI, the reports and the tests all
read the same data.
"""

from __future__ import annotations

import os
from pathlib import Path

from .audio import analyse_audio
from .brief import build_brief
from .captions import extract_captions
from .errors import ShotXrayError
from .frames import brightness, dominant_color, extract_thumbnail
from .probe import probe
from .score import score_readiness
from .shots import detect_shots, pacing

DEFAULT_THRESHOLD = 0.35


def analyze_video(
    path: str,
    threshold: float = DEFAULT_THRESHOLD,
    with_thumbs: bool = True,
    out_dir: str | None = None,
) -> dict:
    """Run the full pipeline on *path* and return the report dict.

    Thumbnails (when requested) are written to ``<out_dir>/thumbs/`` and
    referenced by filename in the report.
    """
    if not os.path.isfile(path):
        raise ShotXrayError(f"no such file: {path!r}")
    info = probe(path)
    if info.duration is None or info.duration <= 0:
        raise ShotXrayError(f"could not determine the duration of {path!r}")

    shots = detect_shots(path, info.duration, threshold=threshold)
    pacing_info = pacing(shots, info.duration)

    thumbs_dir = Path(out_dir) / "thumbs" if out_dir else None
    visuals_ok = True
    for shot in shots:
        try:
            shot.dominant_color = dominant_color(path, shot.mid)
            shot.brightness = brightness(path, shot.mid)
        except ShotXrayError:
            visuals_ok = False
        if with_thumbs and thumbs_dir is not None:
            try:
                thumb_name = f"shot-{shot.index:02d}.png"
                extract_thumbnail(path, shot.mid, str(thumbs_dir / thumb_name))
                shot.thumbnail = f"thumbs/{thumb_name}"
            except ShotXrayError:
                visuals_ok = False
                shot.thumbnail = None

    audio = analyse_audio(path, info.duration) if info.has_audio else None
    captions = extract_captions(path, info.subtitle_codec) if info.has_subtitles else None

    score = score_readiness(
        has_duration=info.duration is not None,
        has_resolution=bool(info.width and info.height),
        has_fps=info.fps is not None,
        has_codec=info.video_codec is not None,
        shot_count=len(shots),
        shots_have_visuals=visuals_ok,
        has_audio=bool(audio and audio.has_audio),
        has_silence_map=bool(audio and audio.has_audio),
        caption_cues=captions.cue_count if captions else 0,
    )

    brief = build_brief(
        info, shots, pacing_info,
        audio_segments=len(audio.segments) if audio else 0,
        silence_total=audio.silence_total if audio else 0.0,
        caption_cues=captions.cue_count if captions else 0,
        score_total=score.total,
        score_grade=score.grade,
    )

    return {
        "tool": "shotxray",
        "version": _version(),
        "info": info.to_dict(),
        "shots": [s.to_dict() for s in shots],
        "pacing": pacing_info.to_dict(),
        "audio": audio.to_dict() if audio else {"has_audio": False},
        "captions": captions.to_dict() if captions else {"cue_count": 0, "cues": []},
        "score": score.to_dict(),
        "brief": brief,
    }


def _version() -> str:
    from . import __version__

    return __version__
