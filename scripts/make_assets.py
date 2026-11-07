"""Generate assets/demo.png (terminal-demo hero) and assets/social-preview.png.

Run: python3 scripts/make_assets.py  (from the repo root)
Uses only Pillow + DejaVu fonts already on the system.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

BG = (12, 12, 13)
CARD = (24, 24, 27)
BORDER = (39, 39, 42)
FG = (244, 244, 245)
MUTED = (161, 161, 170)
GREEN = (74, 222, 128)
YELLOW = (250, 204, 21)
BLUE = (96, 165, 250)
RED = (248, 113, 113)
ACCENT = (96, 165, 250)


def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _rounded(draw: ImageDraw.ImageDraw, box, radius, **kw):
    draw.rounded_rectangle(box, radius=radius, **kw)


def make_demo() -> None:
    """Terminal-style hero: 1200x675, dark, with a shot timeline."""
    W, H = 1200, 675
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # Window
    x0, y0, x1, y1 = 60, 60, W - 60, H - 60
    _rounded(d, [x0, y0, x1, y1], 18, fill=CARD, outline=BORDER, width=1)
    # Title bar dots
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([x0 + 28 + i * 28, y0 + 22, x0 + 42 + i * 28, y0 + 36], fill=col)
    d.text((x0 + 130, y0 + 20), "shotxray — analyze", font=_font(MONO, 22), fill=MUTED)

    lines = [
        ("$ ", GREEN, "shotxray analyze trailer.mp4", FG),
        ("Video:  ", MUTED, "trailer.mp4 (6.0s, 1280x720, 30.0 fps)", FG),
        ("Shots:  ", MUTED, "3 (medium, avg 2.0s, 20.0 cuts/min)", FG),
        ("Audio:  ", MUTED, "yes — 1.0s silence", FG),
        ("Score:  ", MUTED, "85/100 (B)", YELLOW),
        ("Report: ", MUTED, "shotxray-report/ (json, md, html, brief)", FG),
    ]
    font = _font(MONO, 26)
    bold = _font(MONO_BOLD, 26)
    y = y0 + 78
    for prompt, pcol, text, tcol in lines:
        d.text((x0 + 32, y), prompt, font=bold, fill=pcol)
        d.text((x0 + 32 + d.textlength(prompt, font=bold), y), text, font=font, fill=tcol)
        y += 46

    # Shot timeline
    ty = y + 22
    d.text((x0 + 32, ty), "SHOT TIMELINE", font=_font(MONO_BOLD, 20), fill=MUTED)
    bar_y = ty + 38
    bar_h = 46
    segments = [
        ("Shot 1 · 0:00–0:02", YELLOW, "#ffff00"),
        ("Shot 2 · 0:02–0:04", BLUE, "#0100ff"),
        ("Shot 3 · 0:04–0:06", RED, "#fe0000"),
    ]
    seg_w = (x1 - x0 - 64) // 3
    for i, (label, col, hexcol) in enumerate(segments):
        sx = x0 + 32 + i * seg_w
        _rounded(d, [sx, bar_y, sx + seg_w - 8, bar_y + bar_h], 8, fill=col)
        d.text((sx + 6, bar_y + bar_h + 12), label, font=_font(MONO, 19), fill=FG)
        d.text((sx + 6, bar_y + bar_h + 38), hexcol, font=_font(MONO, 19), fill=MUTED)

    d.text((x0 + 32, y1 - 30), "Reverse-engineer any video, shot by shot — locally.",
           font=_font(MONO, 22), fill=MUTED)
    img.save(ASSETS / "demo.png")
    print("wrote", ASSETS / "demo.png")


def make_social_preview() -> None:
    """GitHub social preview: 1280x640."""
    W, H = 1280, 640
    img = Image.new("RGB", (W, H), (10, 10, 12))
    d = ImageDraw.Draw(img)

    # Three colour blocks on the right, like film strips.
    strip_w = 150
    for i, col in enumerate([YELLOW, BLUE, RED]):
        x = W - 70 - strip_w
        y = 90 + i * 150
        _rounded(d, [x, y, x + strip_w, y + 130], 14, fill=col)
        d.text((x + 18, y + 48), f"SHOT {i + 1}", font=_font(MONO_BOLD, 26), fill=(10, 10, 12))

    d.text((70, 88), "shotxray", font=_font(SANS_BOLD, 110), fill=FG)
    d.text((70, 218), "Reverse-engineer any video,", font=_font(SANS, 52), fill=FG)
    d.text((70, 282), "shot by shot — locally.", font=_font(SANS, 52), fill=FG)
    d.text((70, 372), "Shot detection · colour & pacing · audio map · rebuild brief",
           font=_font(MONO, 26), fill=MUTED)
    d.text((70, 420), "No cloud · No API key · No LLM · Python + ffmpeg",
           font=_font(MONO, 26), fill=ACCENT)
    # Score chip
    _rounded(d, [70, 500, 330, 556], 12, outline=BORDER, width=1)
    d.text((90, 514), "Remake Readiness  85/100 (B)", font=_font(MONO_BOLD, 24), fill=YELLOW)
    d.text((70, 590), "github.com/BidyutRoy2/shotxray", font=_font(MONO, 22), fill=MUTED)
    img.save(ASSETS / "social-preview.png")
    print("wrote", ASSETS / "social-preview.png")


def make_standalone_preview() -> None:
    """Run the analyzer on the sample video and embed its thumbnails as data
    URIs, so preview.html opens standalone (no local files needed)."""
    import re
    import subprocess
    import sys
    import tempfile

    with tempfile.TemporaryDirectory(prefix="shotxray-preview-") as tmp:
        env = dict(__import__("os").environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        subprocess.run(
            [sys.executable, "-m", "shotxray", "analyze",
             str(ROOT / "examples" / "sample-video.mp4"), "-o", tmp],
            check=True, capture_output=True, env=env,
        )
        html_text = (Path(tmp) / "report.html").read_text(encoding="utf-8")
        thumbs = Path(tmp) / "thumbs"

        def _embed(match: re.Match) -> str:
            rel = match.group(1)
            data = (thumbs / Path(rel).name).read_bytes()
            b64 = base64.b64encode(data).decode()
            return f'src="data:image/png;base64,{b64}"'

        html_text = re.sub(r'src="(thumbs/[^"]+)"', _embed, html_text)
    (ASSETS / "preview.html").write_text(html_text, encoding="utf-8")
    print("wrote", ASSETS / "preview.html")


if __name__ == "__main__":
    ASSETS.mkdir(parents=True, exist_ok=True)
    make_demo()
    make_social_preview()
    make_standalone_preview()
