#!/usr/bin/env python3
"""Draws the Haier fork's wallpapers from code, so they are original and anyone can rebuild them.

    python3 -m venv /tmp/wp && /tmp/wp/bin/pip install numpy pillow
    /tmp/wp/bin/python tools/wallpapers/make_wallpapers.py            # writes themes/*/wallpaper.jpg

Every picture is 1920x1080, dark, and kept under 300 KB (themes/README.md). The top left, where the
clock sits, and the bottom third, where the dock band sits, stay the darkest parts of each picture.
The random seeds are fixed, so a rebuild gives the same pictures. Released under the repo's MIT licence.
"""
import io
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

W, H = 1920, 1080
ROOT = Path(__file__).resolve().parents[2]
LIMIT = 300 * 1024

ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)


def rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


def vertical(stops):
    """A top-to-bottom gradient through (position 0..1, colour) stops."""
    t = np.arange(H, dtype=np.float32) / (H - 1)
    out = np.zeros((H, 3), np.float32)
    for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
        m = (t >= p0) & (t <= p1)
        f = ((t[m] - p0) / max(p1 - p0, 1e-6))[:, None]
        out[m] = rgb(c0) * (1 - f) + rgb(c1) * f
    return np.repeat(out[:, None, :], W, axis=1)


def glow(img, cx, cy, radius, colour, strength):
    """Adds a soft round light, falling off like a Gaussian."""
    d2 = ((xs - cx) ** 2 + (ys - cy) ** 2) / (radius ** 2)
    img += np.exp(-d2)[..., None] * rgb(colour) * strength


def ridge(seed, base, amp, waves):
    """A hill line: a few sines with seeded phases, one y value per column."""
    rng = np.random.default_rng(seed)
    x = np.arange(W, dtype=np.float32)
    y = np.full(W, base, np.float32)
    for k in range(waves):
        freq = (k + 1) * 0.0016 * (1.6 ** k)
        y += amp / (1.7 ** k) * np.sin(x * freq + rng.uniform(0, 2 * math.pi))
    return y


def fill_below(img, line, colour, soft=1.2):
    """Paints everything under `line` in `colour`, with an anti-aliased edge."""
    a = np.clip((ys - line[None, :]) / soft + 0.5, 0, 1)[..., None]
    img[:] = img * (1 - a) + rgb(colour) * a
    return a


def shade_for_text(img, top_left=0.55, bottom=0.6):
    """Darkens the clock corner and the dock band so white text keeps its contrast."""
    corner = np.exp(-(((xs - 0) / 900) ** 2 + ((ys - 0) / 380) ** 2))
    low = np.clip((ys - H * 0.62) / (H * 0.38), 0, 1) ** 1.3
    k = 1 - top_left * corner - bottom * low
    img *= np.clip(k, 0.25, 1)[..., None]


def finish(img, name, seed):
    """Dithers (the TV decodes to RGB 565, which bands smooth gradients), then saves under the limit."""
    rng = np.random.default_rng(seed)
    img = img + rng.uniform(-1.6, 1.6, img.shape).astype(np.float32)
    pic = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    path = ROOT / "themes" / name / "wallpaper.jpg"
    for q in (88, 84, 80, 76, 72, 68):
        buf = io.BytesIO()
        pic.save(buf, "JPEG", quality=q, optimize=True, progressive=False, subsampling=2)
        if buf.tell() <= LIMIT:
            break
    else:
        sys.exit(f"{name}: still over {LIMIT} bytes at quality {q}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(buf.getvalue())
    print(f"{path.relative_to(ROOT)}: {buf.tell() // 1024} KB at quality {q}")


def cosy_valley():
    """Night over a valley of hills, a crescent moon, and one cottage with its lights on."""
    img = vertical([(0, "#04060D"), (0.45, "#0A0E1F"), (0.68, "#1A1631"), (1, "#0B0A14")])
    rng = np.random.default_rng(7)
    # Stars, thinning towards the horizon.
    for _ in range(420):
        x, y = rng.uniform(0, W), rng.uniform(0, H * 0.58) ** 1.08
        b = rng.uniform(40, 150) * (1 - y / (H * 0.7))
        r = 1.1 if rng.random() < 0.9 else 1.9
        x0, x1, y0, y1 = int(x - 4), int(x + 5), int(y - 4), int(y + 5)
        if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
            continue
        d2 = (xs[y0:y1, x0:x1] - x) ** 2 + (ys[y0:y1, x0:x1] - y) ** 2
        img[y0:y1, x0:x1] += np.exp(-d2 / (r * r))[..., None] * np.array([0.9, 0.95, 1.0]) * b
    # Moon: a halo, then a disc with a second disc taken out of it for the crescent.
    mx, my = 1480, 210
    glow(img, mx, my, 230, "#3A4060", 0.35)
    disc = np.clip(46 - np.sqrt((xs - mx) ** 2 + (ys - my) ** 2), 0, 1)
    bite = np.clip(44 - np.sqrt((xs - mx - 20) ** 2 + (ys - my + 10) ** 2), 0, 1)
    moon = (disc * (1 - bite))[..., None]
    img[:] = img * (1 - moon) + rgb("#E9E3C8") * moon
    # Hills, far (lighter, bluer) to near (almost black).
    layers = [
        (11, 640, 46, 4, "#161B33"),
        (12, 700, 52, 4, "#10142A"),
        (13, 770, 60, 3, "#0B0E1E"),
        (14, 860, 70, 3, "#06080F"),
    ]
    lines = [ridge(seed, base, amp, waves) for seed, base, amp, waves, _ in layers]
    for line, layer in zip(lines[:2], layers):
        fill_below(img, line, layer[4])
    # Far-off windows on the second ridge: a few warm points.
    for fx in (380, 455, 1040, 1720):
        fy = lines[1][fx] + 14
        glow(img, fx, fy, 3.2, "#FFB257", 0.9)
        glow(img, fx, fy, 16, "#FF9A3C", 0.10)
    # The cottage, on the second ridge to the right of centre, above where the dock band sits.
    cx = 1350
    gy = float(lines[1][cx - 60:cx + 60].max()) + 4
    house = np.zeros((H, W), np.float32)
    body = (xs > cx - 58) & (xs < cx + 58) & (ys > gy - 62) & (ys < gy + 40)
    roof = (ys > gy - 62 - 46 + np.abs(xs - cx) * 0.62) & (ys <= gy - 60) & (np.abs(xs - cx) < 76)
    chimney = (xs > cx + 22) & (xs < cx + 38) & (ys > gy - 112) & (ys < gy - 70)
    house[body | roof | chimney] = 1
    img[:] = img * (1 - house[..., None]) + rgb("#05060C") * house[..., None]
    for wx in (cx - 30, cx + 30):
        win = (np.abs(xs - wx) < 11) & (ys > gy - 40) & (ys < gy - 18)
        img[win] = rgb("#FFC46E")
        glow(img, wx, gy - 29, 42, "#FF9840", 0.22)
    door = (np.abs(xs - cx) < 9) & (ys > gy - 26) & (ys < gy + 40)
    img[door] = rgb("#2A1708")
    # A thread of chimney smoke.
    for i in range(40):
        t = i / 40
        glow(img, cx + 30 + 40 * t + 10 * math.sin(t * 7), gy - 118 - 150 * t, 10 + 18 * t, "#2A2E44", 0.05 * (1 - t))
    # The nearer hills go over the cottage's base, so it sits in the valley.
    for line, layer in zip(lines[2:], layers[2:]):
        fill_below(img, line, layer[4])
    shade_for_text(img, top_left=0.35, bottom=0.45)
    finish(img, "haier-cosy-valley", 1)


def hearth():
    """An abstract fireside: a low amber glow from the bottom right and a few drifting embers."""
    img = vertical([(0, "#070405"), (0.6, "#0C0606"), (1, "#120806")])
    glow(img, 1600, 1180, 760, "#7A2A0C", 0.85)
    glow(img, 1500, 1120, 380, "#C4501A", 0.40)
    glow(img, 1720, 1080, 180, "#FF8A2E", 0.22)
    glow(img, 300, 1300, 700, "#3A1206", 0.35)
    rng = np.random.default_rng(23)
    for _ in range(70):
        x = rng.normal(1450, 260)
        y = H - abs(rng.normal(0, 380)) - 80
        if not (0 < x < W and 0 < y < H):
            continue
        r = rng.uniform(1.4, 3.6)
        colour = "#FFB15A" if rng.random() < 0.6 else "#FF7A2A"
        glow(img, x, y, r, colour, rng.uniform(0.35, 0.9) * (y / H))
        glow(img, x, y, r * 7, colour, 0.035)
    shade_for_text(img, top_left=0.3, bottom=0.45)
    finish(img, "haier-hearth", 2)


def tide():
    """Deep blue water at night: soft layered swells and a faint band of moonlight."""
    img = vertical([(0, "#03060D"), (0.5, "#06101F"), (1, "#040A14")])
    glow(img, 1250, 380, 520, "#16305A", 0.45)
    for i, (base, colour) in enumerate([(560, "#0A1A33"), (640, "#08152B"), (730, "#061124"),
                                         (830, "#050D1C"), (940, "#040914")]):
        x = np.arange(W, dtype=np.float32)
        line = base + 22 * np.sin(x * 0.0034 + i * 1.3) + 11 * np.sin(x * 0.0091 + i * 2.1)
        a = fill_below(img, line, colour, soft=6.0)
        # A thin light on each crest, brightest under the moon.
        crest = np.exp(-((ys - line[None, :]) / 2.2) ** 2) * np.exp(-((xs - 1250) / 520) ** 2)
        img += crest[..., None] * rgb("#5F86B8") * (0.30 / (1 + i))
    shade_for_text(img, top_left=0.4, bottom=0.35)
    finish(img, "haier-tide", 3)


if __name__ == "__main__":
    cosy_valley()
    hearth()
    tide()
