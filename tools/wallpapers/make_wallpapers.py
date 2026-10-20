#!/usr/bin/env python3
"""Draws the Haier fork's wallpapers from code, so they are original and anyone can rebuild them.

    python3 -m venv /tmp/wp && /tmp/wp/bin/pip install numpy pillow
    /tmp/wp/bin/python tools/wallpapers/make_wallpapers.py            # writes themes/*/wallpaper.jpg

Every picture is 1920x1080, dark, and kept under 300 KB (themes/README.md). The top left, where the
clock sits, and the bottom third, where the dock band sits, stay the darkest parts of each picture.
haier-cosy-valley and haier-solar get sixteen time-of-day frames each (wallpaper-00.jpg to -15.jpg, see
DayPhase.java), plus wallpaper.jpg. The random seeds are fixed, so a rebuild gives the same pictures. Released under the repo's MIT licence.
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


def finish(img, name, seed, file="wallpaper.jpg"):
    """Dithers (the TV decodes to RGB 565, which bands smooth gradients), then saves under the limit."""
    rng = np.random.default_rng(seed)
    img = img + rng.uniform(-1.6, 1.6, img.shape).astype(np.float32)
    pic = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")
    path = ROOT / "themes" / name / file
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


# One row per time-of-day frame, in DayPhase order (launcher/.../DayPhase.java): 00 night, 01 to 07 from
# 90 minutes before sunrise to 90 minutes after, 08 day, 09 to 15 from 90 minutes before sunset to 90 after.
# sky top, sky middle, horizon, light (0 night .. 1 noon), sun x (None: below the horizon), sun height
# above the horizon in px, stars 0..1, moon 0..1, cottage windows 0..1.
SKY = [
    ("#03050E", "#090E2B", "#18255E", 0.00, None, 0, 1.0, 1.0, 1.0),   # 00 night
    ("#090D22", "#151C44", "#3D4A86", 0.05, None, 0, 0.7, 0.7, 1.0),   # 01 first light
    ("#12162E", "#232850", "#6A6788", 0.12, None, 0, 0.4, 0.3, 1.0),   # 02
    ("#1D1B33", "#363050", "#A27650", 0.22, None, 0, 0.15, 0.0, 0.9),  # 03 glow on the horizon
    ("#2E2236", "#553744", "#E2713A", 0.35, 330, -6, 0.0, 0.0, 0.6),   # 04 sunrise
    ("#30335A", "#504B7E", "#E69D4C", 0.50, 380, 70, 0.0, 0.0, 0.2),   # 05
    ("#303F88", "#4C5DB2", "#E6BC82", 0.68, 430, 150, 0.0, 0.0, 0.0),  # 06
    ("#3549AE", "#5269D8", "#E0CFB4", 0.85, 500, 230, 0.0, 0.0, 0.0),  # 07 morning
    ("#3B63DE", "#557CEB", "#A9B5DC", 1.00, 1520, 420, 0.0, 0.0, 0.0), # 08 day
    ("#3549AE", "#5269D8", "#E0CBAE", 0.85, 1420, 230, 0.0, 0.0, 0.0), # 09 afternoon
    ("#303D92", "#4C5BBA", "#E8B680", 0.68, 1490, 150, 0.0, 0.0, 0.0), # 10
    ("#323065", "#524989", "#EB984A", 0.50, 1540, 70, 0.0, 0.0, 0.2),  # 11 golden hour
    ("#362234", "#5E3546", "#E45C26", 0.35, 1590, -6, 0.0, 0.0, 0.7),  # 12 sunset
    ("#211D3A", "#383058", "#A86E50", 0.22, None, 0, 0.1, 0.0, 1.0),   # 13 afterglow
    ("#141833", "#262A55", "#76708E", 0.12, None, 0, 0.35, 0.3, 1.0),  # 14 dusk
    ("#0C1229", "#18204A", "#465492", 0.05, None, 0, 0.7, 0.7, 1.0),   # 15 blue hour
]
HORIZON_Y = 640


def mix(a, b, t):
    return rgb(a) * (1 - t) + rgb(b) * t


def sky(frame, horizon_y):
    """The sky for one frame: a three-stop gradient, a warm glow on the horizon under the sun, stars,
    the moon and the sun."""
    top, mid, hor, light, sun_x, sun_h, stars, moon, _ = SKY[frame]
    img = vertical([(0, top), (horizon_y / H * 0.55, mid), (horizon_y / H, hor), (1, hor)])
    gx = sun_x if sun_x is not None else (420 if frame <= 4 else 1500)
    warmth = max(0.0, 1 - abs(light - 0.35) / 0.3) if frame not in (0, 8) else 0.0
    glow(img, gx, horizon_y, 520, "#FF8A3A", 0.45 * warmth)
    if stars:
        rng = np.random.default_rng(7)
        for _ in range(420):
            x, y = rng.uniform(0, W), rng.uniform(0, horizon_y * 0.9) ** 1.0
            b = rng.uniform(40, 150) * (1 - y / horizon_y) * stars
            r = 1.1 if rng.random() < 0.9 else 1.9
            x0, x1, y0, y1 = int(x - 4), int(x + 5), int(y - 4), int(y + 5)
            if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
                continue
            d2 = (xs[y0:y1, x0:x1] - x) ** 2 + (ys[y0:y1, x0:x1] - y) ** 2
            img[y0:y1, x0:x1] += np.exp(-d2 / (r * r))[..., None] * np.array([0.9, 0.95, 1.0]) * b
    if moon:
        mx, my = 1480, 210
        glow(img, mx, my, 230, "#3A4060", 0.35 * moon)
        disc = np.clip(46 - np.sqrt((xs - mx) ** 2 + (ys - my) ** 2), 0, 1)
        bite = np.clip(44 - np.sqrt((xs - mx - 20) ** 2 + (ys - my + 10) ** 2), 0, 1)
        m = (disc * (1 - bite) * moon)[..., None]
        img[:] = img * (1 - m) + rgb("#E9E3C8") * m
    if sun_x is not None:
        sy = horizon_y - sun_h
        colour = mix("#FFC27A", "#FFF6E4", min(1.0, light))
        glow(img, sun_x, sy, 260, "#FFD6A0", 0.25)
        d = np.sqrt((xs - sun_x) ** 2 + (ys - sy) ** 2)
        s = np.clip(38 - d, 0, 1)[..., None]
        img[:] = img * (1 - s) + colour * s
    return img


def cosy_valley(frame):
    """A valley of hills with one cottage, under the frame's sky. The hills take the light of the hour;
    the cottage's windows light up from dusk to dawn."""
    _, _, hor, light, _, _, _, _, windows = SKY[frame]
    img = sky(frame, HORIZON_Y)
    # Far (hazier, bluer) to near (darkest); colours blend from night to day, warmed by the horizon.
    layers = [
        (11, 640, 46, 4, "#161B33", "#5A7090"),
        (12, 700, 52, 4, "#10142A", "#3F5E58"),
        (13, 770, 60, 3, "#0B0E1E", "#2E4A36"),
        (14, 860, 70, 3, "#06080F", "#1C2E20"),
    ]
    warm = max(0.0, 1 - abs(light - 0.35) / 0.3) if frame not in (0, 8) else 0.0
    colours = []
    for i, (*_, night, day) in enumerate(layers):
        c = mix(night, day, light ** 0.8) * (1 - 0.18 * warm * (1 - i / 4)) + rgb(hor) * 0.18 * warm * (1 - i / 4)
        colours.append("#%02X%02X%02X" % tuple(int(v) for v in np.clip(c, 0, 255)))
    lines = [ridge(seed, base, amp, waves) for seed, base, amp, waves, *_ in layers]
    for line, colour in zip(lines[:2], colours[:2]):
        fill_below(img, line, colour)
    for fx in (380, 455, 1040, 1720):
        fy = lines[1][fx] + 14
        glow(img, fx, fy, 3.2, "#FFB257", 0.9 * windows)
        glow(img, fx, fy, 16, "#FF9A3C", 0.10 * windows)
    cx = 1350
    gy = float(lines[1][cx - 60:cx + 60].max()) + 4
    wall = mix("#05060C", "#4A3A30", light)
    roof = mix("#05060C", "#5A2E26", light)
    house = (xs > cx - 58) & (xs < cx + 58) & (ys > gy - 62) & (ys < gy + 40)
    top = (ys > gy - 62 - 46 + np.abs(xs - cx) * 0.62) & (ys <= gy - 60) & (np.abs(xs - cx) < 76)
    chimney = (xs > cx + 22) & (xs < cx + 38) & (ys > gy - 112) & (ys < gy - 70)
    img[house | chimney] = wall
    img[top] = roof
    for wx in (cx - 30, cx + 30):
        win = (np.abs(xs - wx) < 11) & (ys > gy - 40) & (ys < gy - 18)
        img[win] = mix("#1C2230", "#FFC46E", windows)
        glow(img, wx, gy - 29, 42, "#FF9840", 0.22 * windows)
    door = (np.abs(xs - cx) < 9) & (ys > gy - 26) & (ys < gy + 40)
    img[door] = mix("#2A1708", "#3A2414", light)
    smoke = mix("#2A2E44", "#C8CCD8", light)
    for i in range(40):
        t = i / 40
        glow(img, cx + 30 + 40 * t + 10 * math.sin(t * 7), gy - 118 - 150 * t, 10 + 18 * t,
             "#%02X%02X%02X" % tuple(int(v) for v in smoke), 0.05 * (1 - t))
    for line, colour in zip(lines[2:], colours[2:]):
        fill_below(img, line, colour)
    # Bright frames get more shade, so the white clock and the dock keep their contrast in the day too.
    shade_for_text(img, top_left=0.35 + 0.25 * light, bottom=0.45 + 0.2 * light)
    return img


def solar(frame):
    """Only the sky: a plain gradient through the day, its horizon glow at the bottom edge."""
    top, mid, hor, light, *_ = SKY[frame]
    img = vertical([(0, top), (0.55, mid), (1, hor)])
    gx = 960
    warmth = max(0.0, 1 - abs(light - 0.35) / 0.3) if frame not in (0, 8) else 0.0
    glow(img, gx, H + 80, 700, "#FF8A3A", 0.5 * warmth)
    shade_for_text(img, top_left=0.35 + 0.3 * light, bottom=0.22)
    return img


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
    for n in range(len(SKY)):
        finish(cosy_valley(n), "haier-cosy-valley", 1, f"wallpaper-{n:02d}.jpg")
        finish(solar(n), "haier-solar", 4, f"wallpaper-{n:02d}.jpg")
    # wallpaper.jpg is the night frame: what an upstream launcher, which knows no frames, shows all day.
    finish(cosy_valley(0), "haier-cosy-valley", 1)
    finish(solar(0), "haier-solar", 4)
    hearth()
    tide()
