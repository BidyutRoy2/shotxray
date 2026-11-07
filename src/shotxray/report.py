"""Report renderers: Markdown, JSON and a dark-mode-aware HTML report.

All renderers read the same dict from :func:`shotxray.analyze.analyze_video`,
so the three formats can never disagree with each other.
"""

from __future__ import annotations

import html as html_lib
import json

from .brief import _fmt_time
from .frames import brightness_label


def to_json(data: dict) -> str:
    payload = {k: v for k, v in data.items() if k != "brief"}
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def to_markdown(data: dict) -> str:
    info = data["info"]
    score = data["score"]
    pacing_info = data["pacing"]
    audio = data["audio"]
    captions = data["captions"]

    lines: list[str] = []
    lines.append(f"# Shot report — {info['path']}")
    lines.append("")
    lines.append(
        f"**{info['duration']:.1f}s** · {info['width']}x{info['height']} "
        f"({info['resolution_label'] or '?'}) · {info['fps'] or '?'} fps · "
        f"{info['video_codec'] or '?'} · {info['format_name'] or '?'}"
    )
    lines.append("")
    lines.append(f"## Remake Readiness: {score['total']}/100 ({score['grade']})")
    lines.append("")
    lines.append("| Component | Score | Note |")
    lines.append("|-----------|-------|------|")
    for comp in score["components"]:
        lines.append(f"| {comp['name']} | {comp['earned']}/{comp['possible']} | {comp['note']} |")
    lines.append("")
    lines.append(f"## Shots ({len(data['shots'])}) — pacing: {pacing_info['label']}")
    lines.append("")
    lines.append(
        f"Average shot {pacing_info['avg_shot_length']}s · "
        f"{pacing_info['cuts_per_minute']} cuts/min · "
        f"shortest {pacing_info['shortest_shot']}s · longest {pacing_info['longest_shot']}s"
    )
    lines.append("")
    lines.append("| # | Start | End | Length | Colour | Light |")
    lines.append("|---|-------|-----|--------|--------|-------|")
    for shot in data["shots"]:
        lines.append(
            f"| {shot['index']} | {_fmt_time(shot['start'])} | {_fmt_time(shot['end'])} | "
            f"{shot['duration']:.1f}s | {shot['dominant_color'] or '—'} | "
            f"{brightness_label(shot['brightness'])} |"
        )
    lines.append("")
    lines.append("## Audio")
    lines.append("")
    if audio.get("has_audio"):
        lines.append(f"- Mean volume: {audio.get('mean_volume_db')} dB, "
                     f"max: {audio.get('max_volume_db')} dB")
        lines.append(f"- Silence: {audio.get('silence_total')}s total in "
                     f"{len(audio.get('silences', []))} stretch(es)")
        lines.append(f"- Non-silent segments: {len(audio.get('segments', []))}")
        for seg in audio.get("segments", [])[:10]:
            lines.append(f"  - {_fmt_time(seg['start'])} – {_fmt_time(seg['end'])} "
                         f"({seg['duration']}s)")
    else:
        lines.append("- No audio stream in this file.")
    lines.append("")
    lines.append("## Captions")
    lines.append("")
    if captions.get("cue_count"):
        lines.append(f"- {captions['cue_count']} embedded cue(s), "
                     f"{captions.get('words', 0)} words")
        for cue in captions.get("cues", [])[:5]:
            lines.append(f"  - [{cue['start']}] {cue['text']}")
    else:
        lines.append("- No embedded captions in this file.")
    lines.append("")
    lines.append("## Rebuild brief")
    lines.append("")
    lines.append("See `brief.md` for the full shot-by-shot remake guide.")
    lines.append("")
    lines.append("_Generated locally by shotxray — no cloud, no API key, no LLM._")
    lines.append("")
    return "\n".join(lines)


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Shot report — {title}</title>
<style>
:root {{ color-scheme: light dark; --bg: #ffffff; --fg: #1a1a1a; --muted: #666; --card: #f4f4f5; --border: #e4e4e7; --accent: #2563eb; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg: #0c0c0d; --fg: #f4f4f5; --muted: #a1a1aa; --card: #18181b; --border: #27272a; --accent: #60a5fa; }} }}
* {{ box-sizing: border-box; }}
body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; background: var(--bg); color: var(--fg); margin: 0; padding: 0 16px 48px; }}
main {{ max-width: 860px; margin: 0 auto; }}
h1 {{ font-size: 1.6rem; margin: 28px 0 4px; }}
h2 {{ font-size: 1.15rem; margin-top: 32px; border-bottom: 1px solid var(--border); padding-bottom: 6px; }}
.meta {{ color: var(--muted); }}
.score {{ font-size: 2.2rem; font-weight: 800; }}
.score small {{ font-size: 1rem; color: var(--muted); font-weight: 400; }}
.timeline {{ display: flex; height: 26px; border-radius: 6px; overflow: hidden; margin: 12px 0; border: 1px solid var(--border); }}
.timeline div {{ height: 100%; }}
.timeline div + div {{ border-left: 2px solid var(--bg); }}
table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
th, td {{ text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--border); }}
th {{ color: var(--muted); font-weight: 600; }}
.swatch {{ display: inline-block; width: 14px; height: 14px; border-radius: 4px; border: 1px solid var(--border); vertical-align: -2px; margin-right: 6px; }}
.shots {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; margin-top: 12px; }}
.shot {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }}
.shot img {{ width: 100%; display: block; aspect-ratio: 16/9; object-fit: cover; background: #000; }}
.shot .body {{ padding: 10px 12px; font-size: 0.9rem; }}
.shot .body b {{ font-size: 1rem; }}
.pill {{ display: inline-block; font-size: 0.75rem; padding: 2px 8px; border-radius: 999px; background: var(--border); margin-left: 6px; }}
footer {{ color: var(--muted); font-size: 0.85rem; margin-top: 36px; }}
</style>
</head>
<body>
<main>
<h1>Shot report</h1>
<p class="meta">{title} &middot; {meta_line}</p>
<p><span class="score">{score_total}<small>/100 · grade {grade}</small></span></p>
<h2>Shot timeline</h2>
<div class="timeline">{timeline}</div>
<p class="meta">{shot_count} shots &middot; pacing: {pacing_label} (avg {avg_shot}s, {cpm} cuts/min)</p>
<h2>Shots</h2>
<div class="shots">{shot_cards}</div>
<h2>Score breakdown</h2>
<table><tr><th>Component</th><th>Score</th><th>Note</th></tr>{score_rows}</table>
<h2>Audio</h2>
<p>{audio_line}</p>
<h2>Captions</h2>
<p>{captions_line}</p>
<footer>Generated locally by shotxray — no cloud, no API key, no LLM.</footer>
</main>
</body>
</html>
"""


def to_html(data: dict) -> str:
    info = data["info"]
    score = data["score"]
    pacing_info = data["pacing"]
    audio = data["audio"]
    captions = data["captions"]
    duration = info["duration"] or 1.0

    timeline_parts = []
    for shot in data["shots"]:
        width = max(shot["duration"] / duration * 100, 1.5)
        colour = shot["dominant_color"] or "#888888"
        timeline_parts.append(
            f'<div style="width:{width:.1f}%;background:{colour}" '
            f'title="Shot {shot["index"]}: {_fmt_time(shot["start"])}–{_fmt_time(shot["end"])}"></div>'
        )

    cards = []
    for shot in data["shots"]:
        img = (f'<img src="{html_lib.escape(shot["thumbnail"])}" alt="Shot {shot["index"]} frame">'
               if shot.get("thumbnail") else '<img alt="No thumbnail">')
        colour = shot["dominant_color"] or "—"
        cards.append(
            f'<div class="shot">{img}<div class="body">'
            f'<b>Shot {shot["index"]}</b>'
            f'<span class="pill">{_fmt_time(shot["start"])} – {_fmt_time(shot["end"])}</span><br>'
            f'{shot["duration"]:.1f}s &middot; '
            f'<span class="swatch" style="background:{colour}"></span>{colour} &middot; '
            f'{brightness_label(shot["brightness"])}</div></div>'
        )

    score_rows = "".join(
        f"<tr><td>{html_lib.escape(c['name'])}</td><td>{c['earned']}/{c['possible']}</td>"
        f"<td>{html_lib.escape(c['note'])}</td></tr>"
        for c in score["components"]
    )

    if audio.get("has_audio"):
        audio_line = (
            f"Mean volume {audio.get('mean_volume_db')} dB, max {audio.get('max_volume_db')} dB. "
            f"{audio.get('silence_total')}s of silence in {len(audio.get('silences', []))} stretch(es); "
            f"{len(audio.get('segments', []))} non-silent segment(s)."
        )
    else:
        audio_line = "No audio stream in this file."

    if captions.get("cue_count"):
        captions_line = (f"{captions['cue_count']} embedded caption cue(s), "
                         f"{captions.get('words', 0)} words.")
    else:
        captions_line = "No embedded captions in this file."

    meta_line = (
        f"{info['duration']:.1f}s &middot; {info['width']}x{info['height']} "
        f"({info['resolution_label'] or '?'}) &middot; {info['fps'] or '?'} fps &middot; "
        f"{info['video_codec'] or '?'}"
    )
    return _HTML_TEMPLATE.format(
        title=html_lib.escape(str(info["path"])),
        meta_line=meta_line,
        score_total=score["total"],
        grade=score["grade"],
        timeline="".join(timeline_parts),
        shot_count=len(data["shots"]),
        pacing_label=pacing_info["label"],
        avg_shot=pacing_info["avg_shot_length"],
        cpm=pacing_info["cuts_per_minute"],
        shot_cards="".join(cards),
        score_rows=score_rows,
        audio_line=audio_line,
        captions_line=captions_line,
    )
