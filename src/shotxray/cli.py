"""Command-line interface for shotxray."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .analyze import analyze_video
from .audio import analyse_audio
from .brief import _fmt_time
from .errors import ShotXrayError
from .probe import probe
from .report import to_html, to_json, to_markdown
from .shots import detect_shots, pacing


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shotxray",
        description="Reverse-engineer any video, shot by shot — locally. "
                    "No cloud, no API key, no LLM.",
    )
    parser.add_argument("--version", action="version", version=f"shotxray {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="full analysis: shots, visuals, audio, captions, brief")
    p_analyze.add_argument("video", help="video file to analyse (mp4, mov, mkv, webm, avi, …)")
    p_analyze.add_argument("-o", "--out", default="shotxray-report",
                           help="output directory (default: shotxray-report)")
    p_analyze.add_argument("--format", choices=["all", "json", "md", "html"], default="all",
                           help="which report files to write (default: all)")
    p_analyze.add_argument("--threshold", type=float, default=0.35,
                           help="scene-change threshold 0-1 (default 0.35; lower = more shots)")
    p_analyze.add_argument("--no-thumbs", action="store_true",
                           help="skip extracting per-shot thumbnails")

    p_shots = sub.add_parser("shots", help="list shot boundaries only")
    p_shots.add_argument("video", help="video file to analyse")
    p_shots.add_argument("--threshold", type=float, default=0.35)
    p_shots.add_argument("--json", action="store_true", help="print JSON instead of a table")

    p_brief = sub.add_parser("brief", help="print the rebuild brief (how to remake it)")
    p_brief.add_argument("video", help="video file to analyse")
    p_brief.add_argument("-o", "--out", help="write the brief to this file instead of stdout")
    p_brief.add_argument("--threshold", type=float, default=0.35)

    p_audio = sub.add_parser("audio", help="audio profile: loudness + silence map")
    p_audio.add_argument("video", help="video file to analyse")
    p_audio.add_argument("--json", action="store_true", help="print JSON instead of text")

    return parser


def _cmd_analyze(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = analyze_video(
        args.video, threshold=args.threshold,
        with_thumbs=not args.no_thumbs, out_dir=str(out_dir),
    )
    written: list[str] = []
    if args.format in ("all", "json"):
        (out_dir / "report.json").write_text(to_json(data), encoding="utf-8")
        written.append("report.json")
    if args.format in ("all", "md"):
        (out_dir / "report.md").write_text(to_markdown(data), encoding="utf-8")
        written.append("report.md")
    if args.format in ("all", "html"):
        (out_dir / "report.html").write_text(to_html(data), encoding="utf-8")
        written.append("report.html")
    (out_dir / "brief.md").write_text(data["brief"], encoding="utf-8")
    written.append("brief.md")

    info = data["info"]
    print(f"Video:  {info['path']} ({info['duration']:.1f}s, "
          f"{info['width']}x{info['height']}, {info['fps'] or '?'} fps)")
    print(f"Shots:  {len(data['shots'])} ({data['pacing']['label']}, "
          f"avg {data['pacing']['avg_shot_length']}s, "
          f"{data['pacing']['cuts_per_minute']} cuts/min)")
    print(f"Audio:  {'yes' if data['audio'].get('has_audio') else 'no audio stream'}"
          + (f" — {data['audio'].get('silence_total')}s silence"
             if data['audio'].get('has_audio') else ""))
    print(f"Score:  {data['score']['total']}/100 ({data['score']['grade']})")
    print(f"Report: {out_dir}/ ({', '.join(written)})")
    return 0


def _cmd_shots(args: argparse.Namespace) -> int:
    info = probe(args.video)
    shots = detect_shots(args.video, info.duration or 0.0, threshold=args.threshold)
    if args.json:
        print(json.dumps(
            {"video": args.video, "duration": info.duration,
             "shots": [s.to_dict() for s in shots],
             "pacing": pacing(shots, info.duration or 0.0).to_dict()},
            indent=2))
        return 0
    print(f"{args.video} — {len(shots)} shot(s), {info.duration:.1f}s")
    print(f"{'#':>3}  {'start':>9}  {'end':>9}  {'len':>6}")
    for shot in shots:
        print(f"{shot.index:>3}  {_fmt_time(shot.start):>9}  {_fmt_time(shot.end):>9}  "
              f"{shot.duration:>5.1f}s")
    return 0


def _cmd_brief(args: argparse.Namespace) -> int:
    data = analyze_video(args.video, threshold=args.threshold, with_thumbs=False)
    if args.out:
        Path(args.out).write_text(data["brief"], encoding="utf-8")
        print(f"Brief written to {args.out}")
    else:
        print(data["brief"])
    return 0


def _cmd_audio(args: argparse.Namespace) -> int:
    info = probe(args.video)
    if not info.has_audio:
        print("No audio stream in this file.")
        return 0
    profile = analyse_audio(args.video, info.duration or 0.0)
    if args.json:
        print(json.dumps(profile.to_dict(), indent=2))
        return 0
    print(f"Mean volume: {profile.mean_volume_db} dB, max: {profile.max_volume_db} dB")
    print(f"Silence: {profile.silence_total}s in {len(profile.silences)} stretch(es)")
    for s in profile.silences:
        print(f"  silence {_fmt_time(s.start)} – {_fmt_time(s.end)} ({s.duration}s)")
    print(f"Non-silent segments: {len(profile.segments)}")
    for seg in profile.segments:
        print(f"  audio   {_fmt_time(seg.start)} – {_fmt_time(seg.end)} ({seg.duration}s)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            return _cmd_analyze(args)
        if args.command == "shots":
            return _cmd_shots(args)
        if args.command == "brief":
            return _cmd_brief(args)
        if args.command == "audio":
            return _cmd_audio(args)
        parser.print_help()
        return 2
    except ShotXrayError as exc:
        print(f"shotxray: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
