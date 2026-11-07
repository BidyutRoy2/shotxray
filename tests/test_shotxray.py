"""Tests for shotxray.

Test videos are synthesised with ffmpeg (colour scenes + a sine tone with a
deliberate 1s silence), so every assertion is about real decoded media —
no fixtures pretending to be video.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from shotxray.analyze import analyze_video  # noqa: E402
from shotxray.audio import analyse_audio  # noqa: E402
from shotxray.brief import build_brief  # noqa: E402
from shotxray.captions import parse_srt  # noqa: E402
from shotxray.errors import ProbeError, ShotXrayError  # noqa: E402
from shotxray.frames import brightness, dominant_color  # noqa: E402
from shotxray.probe import probe  # noqa: E402
from shotxray.report import to_html, to_json, to_markdown  # noqa: E402
from shotxray.score import grade_for, score_readiness  # noqa: E402
from shotxray.shots import Shot, detect_shots, pacing  # noqa: E402

HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True, text=True)


@unittest.skipUnless(HAS_FFMPEG, "ffmpeg/ffprobe required for media tests")
class MediaTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = Path(tempfile.mkdtemp(prefix="shotxray-test-"))
        cls.video_a = cls.tmp / "three-scenes.mp4"
        cls.video_b = cls.tmp / "one-scene.mp4"
        cls.video_c = cls.tmp / "with-captions.mp4"

        # A: 3 hard-cut colour scenes (white 2s, black 2s, red 2s) + a sine tone
        # that is silent between 2s and 3s. Total 6s, 320x180, 30fps.
        # NOTE: the colours are chosen with very different luma on purpose —
        # ffmpeg's scene detector scores luma change, so red->(0,128,0) green
        # (near-identical luma) would be invisible to it. See docs/shot-detection.md.
        _run([
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", "color=c=white:s=320x180:r=30:d=2",
            "-f", "lavfi", "-i", "color=c=black:s=320x180:r=30:d=2",
            "-f", "lavfi", "-i", "color=c=red:s=320x180:r=30:d=2",
            "-f", "lavfi", "-i",
            "aevalsrc='sin(2*PI*440*t)*(lt(t,2)+gt(t,3))':duration=6",
            "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]",
            "-map", "[v]", "-map", "3:a",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
            "-shortest", str(cls.video_a),
        ])
        # B: one continuous blue scene, 3s, no audio.
        _run([
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=30:d=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(cls.video_b),
        ])
        # C: one scene, 4s, with 2 embedded caption cues.
        srt = cls.tmp / "subs.srt"
        srt.write_text(
            "1\n00:00:00,500 --> 00:00:01,500\nHello world\n\n"
            "2\n00:00:02,000 --> 00:00:03,500\nSecond line here\n",
            encoding="utf-8",
        )
        _run([
            "ffmpeg", "-y", "-v", "error",
            "-f", "lavfi", "-i", "color=c=red:s=320x180:r=30:d=4",
            "-i", str(srt),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:s", "mov_text",
            "-shortest", str(cls.video_c),
        ])

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_probe_metadata(self):
        info = probe(str(self.video_a))
        self.assertAlmostEqual(info.duration or 0, 6.0, delta=0.2)
        self.assertEqual((info.width, info.height), (320, 180))
        self.assertAlmostEqual(info.fps or 0, 30.0, delta=0.5)
        self.assertEqual(info.video_codec, "h264")
        self.assertTrue(info.has_audio)
        self.assertFalse(info.has_subtitles)

    def test_shot_detection_three_scenes(self):
        info = probe(str(self.video_a))
        shots = detect_shots(str(self.video_a), info.duration or 0)
        self.assertEqual(len(shots), 3)
        starts = [s.start for s in shots]
        for got, want in zip(starts, [0.0, 2.0, 4.0]):
            self.assertAlmostEqual(got, want, delta=0.25)
        self.assertAlmostEqual(shots[-1].end, 6.0, delta=0.25)

    def test_single_scene_is_one_shot(self):
        info = probe(str(self.video_b))
        shots = detect_shots(str(self.video_b), info.duration or 0)
        self.assertEqual(len(shots), 1)
        self.assertEqual(shots[0].start, 0.0)
        self.assertAlmostEqual(shots[0].end, 3.0, delta=0.25)

    def test_dominant_colours_match_scenes(self):
        # Mid-shot frames: white scene ~1s, black ~3s, red ~5s.
        white = dominant_color(str(self.video_a), 1.0)
        black = dominant_color(str(self.video_a), 3.0)
        red = dominant_color(str(self.video_a), 5.0)
        w = tuple(int(white[i:i + 2], 16) for i in (1, 3, 5))
        k = tuple(int(black[i:i + 2], 16) for i in (1, 3, 5))
        r = tuple(int(red[i:i + 2], 16) for i in (1, 3, 5))
        self.assertTrue(all(c > 200 for c in w), w)
        self.assertTrue(all(c < 40 for c in k), k)
        self.assertGreater(r[0], r[1] + 50)
        self.assertGreater(r[0], r[2] + 50)

    def test_brightness_in_range(self):
        value = brightness(str(self.video_a), 1.0)
        self.assertGreaterEqual(value, 0)
        self.assertLessEqual(value, 255)

    def test_audio_profile_finds_deliberate_silence(self):
        info = probe(str(self.video_a))
        profile = analyse_audio(str(self.video_a), info.duration or 0)
        self.assertTrue(profile.has_audio)
        self.assertIsNotNone(profile.mean_volume_db)
        self.assertGreaterEqual(len(profile.silences), 1)
        sil = profile.silences[0]
        self.assertAlmostEqual(sil.start, 2.0, delta=0.5)
        self.assertAlmostEqual(sil.end, 3.0, delta=0.5)
        self.assertGreaterEqual(len(profile.segments), 2)

    def test_captions_extracted(self):
        from shotxray.captions import extract_captions

        info = probe(str(self.video_c))
        self.assertTrue(info.has_subtitles)
        track = extract_captions(str(self.video_c), info.subtitle_codec)
        self.assertIsNotNone(track)
        assert track is not None
        self.assertEqual(track.cue_count, 2)
        self.assertEqual(track.cues[0].text, "Hello world")

    def test_full_pipeline(self):
        out = self.tmp / "report-a"
        data = analyze_video(str(self.video_a), out_dir=str(out))
        self.assertEqual(len(data["shots"]), 3)
        self.assertEqual(data["pacing"]["label"], "medium")
        self.assertEqual(data["score"]["total"], 85)  # all but captions (none embedded)
        self.assertEqual(data["score"]["grade"], "B")
        self.assertTrue((out / "thumbs" / "shot-01.png").exists())
        self.assertTrue((out / "thumbs" / "shot-03.png").exists())
        self.assertIn("Shot list", data["brief"])

    def test_renderers_agree(self):
        out = self.tmp / "report-c"
        data = analyze_video(str(self.video_c), out_dir=str(out))
        self.assertEqual(data["score"]["total"], 85)  # captions yes, audio no
        md = to_markdown(data)
        html_doc = to_html(data)
        payload = json.loads(to_json(data))
        self.assertIn(f"Shots ({len(data['shots'])})", md)
        self.assertIn("Remake Readiness", md)
        self.assertIn("shot-01", html_doc)
        self.assertIn("timeline", html_doc)
        self.assertEqual(payload["score"]["total"], data["score"]["total"])
        self.assertEqual(len(payload["shots"]), len(data["shots"]))

    def test_cli_analyze_end_to_end(self):
        out = self.tmp / "cli-report"
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parent.parent / "src"))
        proc = subprocess.run(
            [sys.executable, "-m", "shotxray", "analyze", str(self.video_a),
             "-o", str(out)],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name in ("report.json", "report.md", "report.html", "brief.md"):
            self.assertTrue((out / name).exists(), name)
        self.assertIn("3", proc.stdout)
        self.assertIn("85/100", proc.stdout)

    def test_cli_shots_json(self):
        env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parent.parent / "src"))
        proc = subprocess.run(
            [sys.executable, "-m", "shotxray", "shots", str(self.video_a), "--json"],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(len(payload["shots"]), 3)

    def test_probe_rejects_non_video(self):
        text_file = self.tmp / "not-a-video.txt"
        text_file.write_text("hello", encoding="utf-8")
        with self.assertRaises(ProbeError):
            probe(str(text_file))

    def test_missing_file_error(self):
        with self.assertRaises(ShotXrayError):
            analyze_video(str(self.tmp / "does-not-exist.mp4"))


class UnitTestCase(unittest.TestCase):
    def test_score_all_present_is_100(self):
        score = score_readiness(
            has_duration=True, has_resolution=True, has_fps=True, has_codec=True,
            shot_count=5, shots_have_visuals=True,
            has_audio=True, has_silence_map=True, caption_cues=3,
        )
        self.assertEqual(score.total, 100)
        self.assertEqual(score.grade, "A")

    def test_score_nothing_is_zero(self):
        score = score_readiness(
            has_duration=False, has_resolution=False, has_fps=False, has_codec=False,
            shot_count=0, shots_have_visuals=False,
            has_audio=False, has_silence_map=False, caption_cues=0,
        )
        self.assertEqual(score.total, 0)
        self.assertEqual(score.grade, "F")

    def test_grade_bands(self):
        self.assertEqual(grade_for(90), "A")
        self.assertEqual(grade_for(89), "B")
        self.assertEqual(grade_for(60), "C")
        self.assertEqual(grade_for(40), "D")
        self.assertEqual(grade_for(39), "F")

    def test_pacing_labels(self):
        single = pacing([Shot(index=1, start=0.0, end=10.0)], 10.0)
        self.assertEqual(single.label, "single-shot")
        fast = pacing([Shot(index=i + 1, start=float(i), end=float(i + 1)) for i in range(10)], 10.0)
        self.assertEqual(fast.label, "fast-cut")
        slow = pacing([Shot(index=1, start=0.0, end=8.0), Shot(index=2, start=8.0, end=16.0)], 16.0)
        self.assertEqual(slow.label, "slow")

    def test_srt_parser(self):
        cues = parse_srt(
            "1\n00:00:01,000 --> 00:00:02,000\nFirst cue\n\n"
            "2\n00:00:03,500 --> 00:00:04,000\nSecond\nline two\n"
        )
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[1].text, "Second line two")
        self.assertEqual(cues[0].start, "00:00:01.000")

    def test_brief_is_honest_about_limits(self):
        from shotxray.probe import VideoInfo

        info = VideoInfo(path="demo.mp4", duration=6.0, width=320, height=180,
                         fps=30.0, video_codec="h264", has_audio=True)
        shots = [Shot(index=1, start=0.0, end=2.0, dominant_color="#ff0000", brightness=80),
                 Shot(index=2, start=2.0, end=6.0, dominant_color="#00ff00", brightness=120)]
        brief = build_brief(info, shots, pacing(shots, 6.0),
                            audio_segments=2, silence_total=1.0,
                            caption_cues=0, score_total=85, score_grade="B")
        self.assertIn("Shot list", brief)
        self.assertIn("cannot tell you", brief)
        self.assertIn("#ff0000", brief)


if __name__ == "__main__":
    unittest.main()
