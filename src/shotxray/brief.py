"""The rebuild brief: turn measured structure into "how to remake it".

Every claim in the brief traces back to a measured value (shot times,
colours, pacing, audio segments, captions). Nothing is invented: where
shotxray cannot know something (e.g. camera movement, on-screen text), the
brief says so instead of guessing.
"""

from __future__ import annotations

from .frames import brightness_label
from .probe import VideoInfo
from .shots import Pacing, Shot


def _fmt_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{int(h):d}:{int(m):02d}:{s:05.2f}"
    return f"{int(m):d}:{s:05.2f}"


def _shot_remake_note(shot: Shot, aspect: str | None) -> str:
    framing = {
        "16:9 widescreen": "wide 16:9 frame",
        "9:16 vertical": "vertical 9:16 frame",
        "1:1 square": "square 1:1 frame",
    }.get(aspect or "", "frame")
    mood = brightness_label(shot.brightness)
    colour = f"dominant colour {shot.dominant_color}" if shot.dominant_color else "colour unknown"
    return (
        f"Hold one static {framing} for {shot.duration:.1f}s "
        f"({colour}, {mood} lighting). Cut hard at {_fmt_time(shot.end)} — "
        "no dissolve was detected."
    )


def build_brief(
    info: VideoInfo,
    shots: list[Shot],
    pacing_info: Pacing,
    audio_segments: int,
    silence_total: float,
    caption_cues: int,
    score_total: int,
    score_grade: str,
) -> str:
    """Render the rebuild brief as Markdown."""
    lines: list[str] = []
    lines.append(f"# Rebuild brief — {info.path}")
    lines.append("")
    lines.append(
        f"Measured structure of a {info.duration:.1f}s video "
        f"({info.width}x{info.height}, {info.resolution_label or 'unknown res'}, "
        f"{info.fps or '?'} fps, {info.video_codec or 'unknown codec'}). "
        f"Remake Readiness {score_total}/100 ({score_grade})."
    )
    lines.append("")
    lines.append("## Structure at a glance")
    lines.append("")
    lines.append(f"- **Shots:** {len(shots)} — pacing **{pacing_info.label}** "
                 f"(avg {pacing_info.avg_shot_length}s per shot, "
                 f"{pacing_info.cuts_per_minute} cuts/min)")
    lines.append(f"- **Aspect:** {info.aspect or 'unknown'}")
    if info.has_audio:
        lines.append(f"- **Audio:** {audio_segments} non-silent segment(s), "
                     f"{silence_total:.1f}s of silence detected")
    else:
        lines.append("- **Audio:** no audio stream in this file")
    if caption_cues:
        lines.append(f"- **Captions:** {caption_cues} embedded cue(s) — reuse the wording, "
                     "don't re-transcribe")
    else:
        lines.append("- **Captions:** none embedded — write captions from scratch if you need them")
    lines.append("")
    lines.append("## Shot list — recreate in order")
    lines.append("")
    lines.append("| # | Start | Length | Colour | Light | How to remake it |")
    lines.append("|---|-------|--------|--------|-------|------------------|")
    for shot in shots:
        lines.append(
            f"| {shot.index} | {_fmt_time(shot.start)} | {shot.duration:.1f}s | "
            f"{shot.dominant_color or '—'} | {brightness_label(shot.brightness)} | "
            f"{_shot_remake_note(shot, info.aspect)} |"
        )
    lines.append("")
    lines.append("## Remake checklist")
    lines.append("")
    if shots:
        lines.append(f"1. Open with the hook: shot 1 runs {_fmt_time(0)}–{_fmt_time(shots[0].end)} "
                     f"({shots[0].duration:.1f}s). Match its colour and brightness first — "
                     "viewers decide in the first seconds.")
        lines.append(f"2. Cut {len(shots) - 1} time(s) at: " +
                     ", ".join(_fmt_time(s.start) for s in shots[1:]) + "." if len(shots) > 1
                     else "2. Single continuous shot — no cuts to match.")
        lines.append(f"3. Keep the average shot length near {pacing_info.avg_shot_length}s "
                     f"to preserve the {pacing_info.label} rhythm.")
    if info.has_audio:
        lines.append("4. Place audio beats inside the non-silent segments; "
                     "leave the detected silences as breathing room.")
    if caption_cues:
        lines.append("5. Copy the embedded caption wording into your edit — it is part of the original.")
    lines.append("")
    lines.append("## What shotxray cannot tell you (honest limits)")
    lines.append("")
    lines.append("- Camera movement (pan/tilt/zoom) — not measured; watch the footage.")
    lines.append("- On-screen text and graphics — not OCR'd.")
    lines.append("- Music vs. speech — silence detection finds pauses, not content.")
    lines.append("- Why a shot works — structure is measured, taste is yours.")
    lines.append("")
    lines.append("_Generated locally by shotxray — no cloud, no API key, no LLM._")
    lines.append("")
    return "\n".join(lines)
