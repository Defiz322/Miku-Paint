#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Draw a semi-realistic Hatsune Miku portrait as a MikuPaint project.

The generator writes two files next to this script:

  hatsune_miku.mipaint   the editable MikuPaint project (polygons, ovals, lines, text)
  hatsune_miku.png       an anti-aliased preview rendered from the exact same shapes

Run:
  python art/draw_miku.py
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 1600
SS = 2  # supersampling for the PNG preview
ROOT = Path(__file__).resolve().parent


# ---------------------------------------------------------------- colour utils


def rgb(color: str) -> tuple[int, int, int]:
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def hex_color(values) -> str:
    r, g, b = (max(0, min(255, round(v))) for v in values)
    return f"#{r:02x}{g:02x}{b:02x}"


def mix(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ca, cb = rgb(a), rgb(b)
    return hex_color(ca[i] + (cb[i] - ca[i]) * t for i in range(3))


def lighten(color: str, t: float) -> str:
    return mix(color, "#ffffff", t)


def darken(color: str, t: float) -> str:
    return mix(color, "#000000", t)


def smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# --------------------------------------------------------------- curve helpers


def catmull_rom(points, closed: bool = True, samples: int = 10):
    """Dense polyline through the control points (Catmull-Rom spline)."""
    pts = [(float(x), float(y)) for x, y in points]
    if closed:
        p = [pts[-1]] + pts + [pts[0], pts[1]]
        segments = len(pts)
    else:
        p = [pts[0]] + pts + [pts[-1]]
        segments = len(pts) - 1

    out = []
    for i in range(segments):
        p0, p1, p2, p3 = p[i], p[i + 1], p[i + 2], p[i + 3]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                       + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                       + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                       + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                       + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    if not closed:
        out.append(pts[-1])
    return out


def lerp_point(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def path_along(points, t: float):
    """Point at normalized distance t along a dense polyline."""
    if t <= 0:
        return points[0]
    if t >= 1:
        return points[-1]
    lengths = [math.dist(points[i], points[i + 1]) for i in range(len(points) - 1)]
    total = sum(lengths)
    target = total * t
    walked = 0.0
    for i, seg in enumerate(lengths):
        if walked + seg >= target:
            return lerp_point(points[i], points[i + 1], (target - walked) / max(seg, 1e-6))
        walked += seg
    return points[-1]


def offset_path(points, amount: float, side: float = 1.0):
    """Approximate polyline offset (positive = left normal)."""
    out = []
    n = len(points)
    for i, p in enumerate(points):
        a = points[max(0, i - 1)]
        b = points[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / length * side, dx / length * side
        out.append((p[0] + nx * amount, p[1] + ny * amount))
    return out


# ------------------------------------------------------------------- art class


class Art:
    def __init__(self):
        self.items: list[dict] = []
        self.image = Image.new("RGB", (W * SS, H * SS), "#071114")
        self.draw = ImageDraw.Draw(self.image)
        self.font_path = "C:/Windows/Fonts/arialbd.ttf"
        self._font_cache: dict[int, ImageFont.FreeTypeFont] = {}

    # -- primitives ---------------------------------------------------------

    def poly(self, points, fill: str, outline: str = "", width: float = 1.0):
        pts = [(round(x, 1), round(y, 1)) for x, y in points]
        if len(pts) < 3:
            return
        coords = [c for p in pts for c in p]
        self.items.append({
            "type": "polygon", "coords": coords, "fill": fill,
            "outline": outline, "width": str(float(width)),
        })
        self.draw.polygon([(x * SS, y * SS) for x, y in pts], fill=fill)
        if outline:
            self.draw.line([(x * SS, y * SS) for x, y in pts] + [(pts[0][0] * SS, pts[0][1] * SS)],
                           fill=outline, width=max(1, int(width * SS)), joint="curve")

    def ellipse(self, cx, cy, rx, ry, fill: str, outline: str = "", width: float = 1.0):
        x0, y0, x1, y1 = cx - rx, cy - ry, cx + rx, cy + ry
        self.items.append({
            "type": "oval", "coords": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
            "fill": fill, "outline": outline, "width": str(float(width)),
        })
        self.draw.ellipse([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=fill,
                          outline=outline or None, width=max(1, int(width * SS)))

    def line(self, points, fill: str, width: float = 3.0, cap: str = "round"):
        pts = [(round(x, 1), round(y, 1)) for x, y in points]
        if len(pts) < 2:
            return
        self.items.append({
            "type": "line", "coords": [c for p in pts for c in p],
            "fill": fill, "width": str(float(width)), "capstyle": cap, "joinstyle": "round",
        })
        scaled = [(x * SS, y * SS) for x, y in pts]
        self.draw.line(scaled, fill=fill, width=max(1, int(width * SS)), joint="curve")
        if cap == "round":
            r = width * SS / 2
            for x, y in (scaled[0], scaled[-1]):
                self.draw.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def text(self, x, y, text: str, fill: str, size: int = 30, anchor: str = "mm",
             bold: bool = False):
        self.items.append({
            "type": "text", "coords": [round(x, 1), round(y, 1)], "text": text,
            "fill": fill, "font": f"Arial {size} bold" if bold else f"Arial {size}",
        })
        font = ImageFont.truetype(self.font_path, size * SS)
        self.draw.text((x * SS, y * SS), text, fill=fill, font=font, anchor=anchor)

    # -- helpers ------------------------------------------------------------

    def soft_ellipse(self, cx, cy, rx, ry, base: str, color: str, strength: float = 1.0,
                     steps: int = 46, ease: bool = True):
        """Radial blend from `base` at the rim to `color` in the centre."""
        for i in range(steps):
            t = i / (steps - 1)
            f = smoothstep(t) if ease else t
            r = (1.0 - t)
            c = mix(base, color, strength * f)
            self.ellipse(cx, cy, rx * r, ry * r, c)

    def soft_poly(self, points, base: str, color: str, strength: float = 1.0,
                  steps: int = 36, centre=None):
        pts = [(float(x), float(y)) for x, y in points]
        if centre is None:
            centre = (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
        for i in range(steps):
            t = i / (steps - 1)
            c = mix(base, color, strength * smoothstep(t))
            s = 1.0 - t
            self.poly([(centre[0] + (x - centre[0]) * s,
                        centre[1] + (y - centre[1]) * s) for x, y in pts], c)

    def gradient_rect(self, x0, y0, x1, y1, top: str, bottom: str, bands: int = 320,
                      horizontal: bool = False):
        for i in range(bands):
            t = i / (bands - 1)
            c = mix(top, bottom, t)
            if horizontal:
                xa = x0 + (x1 - x0) * i / bands
                xb = x0 + (x1 - x0) * (i + 1) / bands + 0.5
                self.poly([(xa, y0), (xb, y0), (xb, y1), (xa, y1)], c)
            else:
                ya = y0 + (y1 - y0) * i / bands
                yb = y0 + (y1 - y0) * (i + 1) / bands + 0.5
                self.poly([(x0, ya), (x1, ya), (x1, yb), (x0, yb)], c)

    def glow(self, cx, cy, radius, base: str, color: str, strength=1.0, steps=80, squash=1.0):
        for i in range(steps):
            t = i / (steps - 1)
            r = radius * (1.0 - t)
            c = mix(base, color, strength * smoothstep(t))
            self.ellipse(cx, cy, r, r * squash, c)

    def save(self):
        data = {
            "version": "1.0",
            "app": "MikuPaint",
            "title": "Hatsune Miku - semi-realistic portrait",
            "canvas_width": W,
            "canvas_height": H,
            "items": self.items,
        }
        project = ROOT / "hatsune_miku.mipaint"
        project.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                           encoding="utf-8")
        preview = ROOT / "hatsune_miku.png"
        self.image.resize((W, H), Image.LANCZOS).save(preview)
        print(f"{project}  ({project.stat().st_size / 1024:.0f} KB, {len(self.items)} items)")
        print(f"{preview}")


# ---------------------------------------------------------------- the drawing


BG_TOP = "#061114"
BG_BOT = "#0b2729"
TEAL = "#39c5bb"
TEAL_LIGHT = "#8af0e2"
PINK = "#ff6b9d"

SKIN_BASE = "#efc7b3"
SKIN_LIGHT = "#ffe4d4"
SKIN_MID = "#f6d4c1"
SKIN_SHADOW = "#d29a84"
SKIN_DEEP = "#a96c5f"
SKIN_BLUSH = "#e69a90"

HAIR_DEEP = "#063a3d"
HAIR_DARK = "#0a5a5b"
HAIR_BASE = "#0f807c"
HAIR_MID = "#1aa79e"
HAIR_LIGHT = "#4fd6c9"
HAIR_HI = "#a5fff4"

OUT_DARK = "#11161c"
OUT_BASE = "#1e252e"
OUT_HI = "#39434f"

LIP = "#b9616b"
LIP_DARK = "#7c3d47"
LIP_LIGHT = "#d88a91"


def background(a: Art):
    a.gradient_rect(0, 0, W, H, BG_TOP, BG_BOT, bands=280)

    # Teal stage light behind the head.
    for i in range(70):
        t = i / 69
        r = 760 * (1 - t)
        c = mix(BG_TOP, "#155457", 0.55 * smoothstep(t))
        a.ellipse(600, 610, r, r * 0.92, c)

    # A soft violet counter-light from the lower right.
    for i in range(40):
        t = i / 39
        r = 620 * (1 - t)
        c = mix(BG_BOT, "#3a1e42", 0.25 * smoothstep(t))
        a.ellipse(1080, 1270, r, r, c)

    # Bokeh. Low-contrast concentric discs keep it subtle.
    bokeh = [
        (150, 250, 90, TEAL, 0.10), (280, 130, 45, TEAL, 0.12),
        (980, 220, 120, TEAL, 0.09), (1110, 380, 55, TEAL, 0.13),
        (120, 900, 70, PINK, 0.07), (1080, 780, 85, TEAL, 0.08),
        (210, 1420, 110, TEAL, 0.06), (1030, 1450, 130, PINK, 0.05),
        (70, 600, 40, TEAL, 0.12), (1140, 1050, 40, TEAL, 0.09),
    ]
    for x, y, r, col, strength in bokeh:
        a.glow(x, y, r, BG_BOT, col, strength=strength, steps=26, squash=1.0)
        a.ellipse(x, y, r * 0.92, r * 0.92, mix(BG_BOT, col, strength * 0.5))

    # A single soft diagonal light shaft, kept very low contrast.
    a.poly([(700, 0), (860, 0), (360, 1600), (200, 1600)],
           mix(BG_BOT, "#2f8f8b", 0.028))


def hair_back(a: Art):
    # Main mass of the two tails, painted as layered silhouettes.
    left = catmull_rom([
        (430, 400), (330, 350), (215, 410), (155, 545), (115, 720),
        (90, 930), (82, 1150), (105, 1370), (150, 1550), (195, 1600),
        (245, 1510), (270, 1320), (300, 1120), (322, 930), (340, 750),
        (360, 590), (392, 470),
    ], samples=8)
    right = [(W - x, y) for x, y in left]

    for shape in (left, right):
        a.poly(shape, HAIR_DEEP)

    # Tail volume: broad inner shapes in progressively lighter teal.
    left_layers = [
        ([(420, 430), (320, 400), (235, 480), (185, 640), (160, 845),
          (155, 1060), (175, 1265), (205, 1445), (225, 1535), (255, 1440),
          (270, 1250), (292, 1050), (310, 860), (330, 690), (365, 535)], HAIR_DARK),
        ([(405, 480), (330, 465), (265, 550), (225, 720), (210, 915),
          (215, 1110), (235, 1285), (255, 1420), (270, 1360), (280, 1190),
          (295, 1010), (315, 830), (335, 675), (370, 560)], HAIR_BASE),
        ([(388, 560), (340, 560), (300, 650), (278, 815), (272, 990),
          (283, 1160), (300, 1295), (310, 1250), (318, 1100), (330, 940),
          (345, 790), (365, 660)], HAIR_MID),
    ]
    for shape, color in left_layers:
        for poly, _ in ((shape, color),):
            a.poly(catmull_rom(poly, samples=6), color)
            a.poly(catmull_rom([(W - x, y) for x, y in poly], samples=6), color)

    # Deep folds between locks.
    fold_sets = [
        ([(355, 470), (300, 560), (265, 720), (250, 900), (255, 1080), (280, 1260)], HAIR_DEEP, 9),
        ([(245, 450), (200, 560), (170, 750), (155, 960), (160, 1170), (185, 1380)], HAIR_DEEP, 8),
        ([(430, 520), (390, 650), (370, 820), (360, 1000), (365, 1180), (385, 1340)], HAIR_DARK, 7),
    ]
    for pts, col, w in fold_sets:
        for side in (1, -1):
            line = catmull_rom([(x if side == 1 else W - x, y) for x, y in pts], closed=False, samples=10)
            a.line(line, col, w)

    # Huge glossy sweeps in the tails.
    for side in (1, -1):
        gloss = catmull_rom([(390, 560), (350, 700), (330, 870), (330, 1040),
                             (345, 1190), (365, 1300)], closed=False, samples=12)
        gloss = [(x if side == 1 else W - x, y) for x, y in gloss]
        a.line(gloss, mix(HAIR_MID, HAIR_LIGHT, 0.35), 16)
        a.line(offset_path(gloss, 7), mix(HAIR_MID, HAIR_LIGHT, 0.65), 5)
        a.line(offset_path(gloss, 18), HAIR_MID, 10)
        gloss2 = catmull_rom([(300, 600), (260, 760), (240, 950), (245, 1130), (265, 1290)],
                             closed=False, samples=12)
        gloss2 = [(x if side == 1 else W - x, y) for x, y in gloss2]
        a.line(gloss2, mix(HAIR_BASE, HAIR_LIGHT, 0.35), 11)
        a.line(offset_path(gloss2, -6), mix(HAIR_BASE, HAIR_LIGHT, 0.6), 4)

    # Fine strands, dense near the outer edge for a soft rim.
    rng = random.Random(39)
    for side in (1, -1):
        for i in range(34):
            x0 = 110 + rng.random() * 270
            y0 = 520 + rng.random() * 720
            bend = (rng.random() - 0.5) * 90
            pts = catmull_rom([
                (x0, y0), (x0 - 18 + bend, y0 + 170), (x0 - 30 + bend * 0.5, y0 + 360),
                (x0 - 20, y0 + 520), (x0 + 5, y0 + 640),
            ], closed=False, samples=8)
            col = rng.choice([HAIR_DEEP, HAIR_DARK, mix(HAIR_BASE, HAIR_LIGHT, 0.25)])
            a.line([(x if side == 1 else W - x, y) for x, y in pts], col, 2 + rng.random() * 4)

    # Rim light on the outside of both tails.
    for side in (1, -1):
        rim = catmull_rom([(157, 620), (115, 800), (95, 1000), (100, 1210), (130, 1430), (180, 1580)],
                          closed=False, samples=14)
        a.line([(x if side == 1 else W - x, y) for x, y in rim], mix(HAIR_LIGHT, "#d7fffb", 0.25), 5)


def body(a: Art):
    # Shoulders and upper arms.
    torso = catmull_rom([
        (600, 1060), (760, 1120), (930, 1200), (1040, 1290), (1100, 1420),
        (1140, 1600), (60, 1600), (100, 1420), (160, 1290), (270, 1200),
        (440, 1120),
    ], samples=10)
    a.poly(torso, SKIN_BASE)

    # Shoulder / chest modelling. Warm key light from upper left.
    a.soft_poly(torso, SKIN_BASE, SKIN_MID, 0.9, steps=26, centre=(520, 1350))
    a.soft_ellipse(420, 1350, 240, 180, SKIN_MID, SKIN_LIGHT, 0.75, steps=38)
    a.soft_ellipse(790, 1360, 260, 210, SKIN_MID, SKIN_SHADOW, 0.55, steps=38)
    a.soft_ellipse(1020, 1390, 160, 180, SKIN_BASE, SKIN_DEEP, 0.38, steps=30)
    a.soft_ellipse(600, 1510, 260, 160, SKIN_MID, SKIN_SHADOW, 0.22, steps=26)

    # Collarbones.
    left_bone = catmull_rom([(470, 1155), (520, 1180), (575, 1188), (600, 1184)],
                            closed=False, samples=8)
    right_bone = catmull_rom([(600, 1184), (650, 1180), (730, 1150)],
                             closed=False, samples=8)
    a.line(left_bone, mix(SKIN_SHADOW, SKIN_DEEP, 0.25), 4)
    a.line(right_bone, mix(SKIN_SHADOW, SKIN_DEEP, 0.3), 4)
    a.line(offset_path(left_bone, -5), SKIN_LIGHT, 5)
    a.line(offset_path(right_bone, 5), SKIN_LIGHT, 5)

    # Black sleeveless top.
    shirt = catmull_rom([
        (455, 1230), (500, 1215), (600, 1205), (700, 1215), (745, 1230),
        (790, 1280), (940, 1295), (1020, 1360), (1060, 1480), (1070, 1600),
        (130, 1600), (140, 1480), (180, 1360), (260, 1295), (410, 1280),
    ], samples=10)
    a.poly(shirt, OUT_DARK)

    # Shirt folds and sheen.
    a.soft_poly(shirt, OUT_DARK, OUT_BASE, 0.9, steps=30, centre=(560, 1420))
    a.soft_ellipse(470, 1390, 180, 140, OUT_BASE, mix(OUT_BASE, "#59677a", 0.5), 0.45, steps=30)
    a.soft_ellipse(760, 1430, 190, 150, OUT_BASE, "#070a0e", 0.7, steps=28)
    for pts, w in [
        ([(330, 1330), (355, 1420), (345, 1520)], 6),
        ([(430, 1305), (445, 1410), (430, 1540)], 5),
        ([(710, 1315), (690, 1420), (700, 1540)], 5),
        ([(900, 1350), (860, 1440), (845, 1560)], 6),
    ]:
        a.line(catmull_rom(pts, closed=False, samples=8), "#0a0e13", w)

    # Scoop collar with teal piping.
    collar = catmull_rom([
        (470, 1240), (505, 1260), (548, 1288), (600, 1298),
        (652, 1288), (695, 1260), (730, 1240),
    ], closed=False, samples=10)
    a.line(offset_path(collar, 10), OUT_HI, 10)
    a.line(collar, TEAL, 6)
    a.line(offset_path(collar, -7), mix(TEAL, "#ffffff", 0.25), 2)

    # The signature teal tie.
    knot = catmull_rom([(568, 1278), (600, 1266), (632, 1278), (620, 1310),
                        (580, 1310)], samples=8)
    a.poly(knot, TEAL)
    a.soft_poly(knot, TEAL, lighten(TEAL, 0.45), 0.9, steps=18, centre=(585, 1282))
    a.line([(580, 1308), (600, 1315), (620, 1308)], darken(TEAL, 0.3), 4)

    tie = catmull_rom([(578, 1310), (622, 1310), (660, 1470), (630, 1560),
                       (600, 1520), (570, 1560), (540, 1470)], samples=8)
    a.poly(tie, mix(TEAL, "#0d5b58", 0.25))
    a.poly(catmull_rom([(590, 1315), (614, 1315), (638, 1450), (620, 1520),
                        (600, 1495), (580, 1520), (562, 1450)], samples=8),
           TEAL)
    a.soft_poly(catmull_rom([(586, 1320), (600, 1320), (614, 1420), (600, 1470),
                             (586, 1420)], samples=8),
                TEAL, lighten(TEAL, 0.35), 0.8, steps=16, centre=(598, 1360))
    a.line([(600, 1320), (600, 1510)], darken(TEAL, 0.28), 4)
    a.line([(575, 1330), (548, 1460)], darken(TEAL, 0.35), 3)
    a.line([(626, 1330), (652, 1460)], darken(TEAL, 0.35), 3)
    a.line([(540, 1560), (570, 1520)], darken(TEAL, 0.2), 3)
    a.line([(660, 1560), (630, 1520)], darken(TEAL, 0.2), 3)

    # "01" tattoo on the left shoulder (viewer's left).
    a.text(300, 1395, "01", "#1b6d6b", size=44, bold=True)
    # Faint pink trim at the sleeves, just peeking into the crop.
    a.line([(85, 1540), (155, 1590)], PINK, 7)
    a.line([(1115, 1540), (1045, 1590)], PINK, 7)


def neck(a: Art):
    neck_poly = catmull_rom([
        (500, 920), (700, 920), (724, 1010), (738, 1100), (772, 1170),
        (700, 1230), (600, 1250), (500, 1230), (428, 1170), (462, 1100),
        (476, 1010),
    ], samples=9)
    a.poly(neck_poly, SKIN_BASE)
    a.soft_poly(neck_poly, SKIN_BASE, SKIN_MID, 0.9, steps=28, centre=(590, 1110))

    # Shadow cast by the jaw.
    a.soft_ellipse(600, 982, 190, 80, SKIN_MID, SKIN_SHADOW, 0.85, steps=34)
    a.soft_ellipse(610, 1000, 135, 50, SKIN_MID, SKIN_DEEP, 0.35, steps=26)
    a.soft_ellipse(710, 1080, 55, 125, SKIN_MID, SKIN_SHADOW, 0.55, steps=26)
    a.soft_ellipse(475, 1070, 45, 130, SKIN_MID, SKIN_LIGHT, 0.55, steps=26)

    # Sternocleidomastoid hints.
    a.line(catmull_rom([(520, 1000), (500, 1080), (480, 1180)], closed=False, samples=8),
           mix(SKIN_SHADOW, SKIN_DEEP, 0.3), 4)
    a.line(catmull_rom([(690, 1000), (714, 1090), (730, 1180)], closed=False, samples=8),
           mix(SKIN_SHADOW, SKIN_DEEP, 0.25), 4)


FACE = catmull_rom([
    (600, 372), (700, 395), (762, 475), (792, 590), (790, 700),
    (768, 805), (720, 895), (655, 958), (600, 982), (545, 958),
    (480, 895), (432, 805), (410, 700), (408, 590), (438, 475),
    (500, 395),
], samples=12)


def face(a: Art):
    a.poly(FACE, SKIN_BASE)

    # Broad modelling: light from the upper left, shadow to the right.
    a.soft_poly(FACE, SKIN_BASE, SKIN_MID, 0.85, steps=24, centre=(540, 690))
    a.soft_ellipse(500, 640, 190, 210, SKIN_MID, SKIN_LIGHT, 0.7, steps=38)
    a.soft_ellipse(745, 710, 110, 245, SKIN_BASE, SKIN_SHADOW, 0.8, steps=44)
    a.soft_ellipse(700, 895, 100, 100, SKIN_BASE, SKIN_SHADOW, 0.65, steps=30)
    a.soft_ellipse(465, 860, 75, 120, SKIN_BASE, SKIN_SHADOW, 0.4, steps=28)
    a.soft_ellipse(600, 935, 105, 55, SKIN_MID, SKIN_SHADOW, 0.5, steps=26)
    a.soft_ellipse(585, 540, 130, 80, SKIN_MID, SKIN_LIGHT, 0.65, steps=30)

    # Cheek blush.
    a.soft_ellipse(478, 805, 72, 48, SKIN_MID, SKIN_BLUSH, 0.35, steps=26)
    a.soft_ellipse(714, 810, 65, 42, SKIN_MID, SKIN_BLUSH, 0.28, steps=26)

    # Freckles and a beauty mark: tiny enough to read as skin texture.
    rng = random.Random(309)
    for _ in range(34):
        x = 535 + rng.random() * 130
        y = 775 + rng.random() * 47
        if ((x - 600) / 70) ** 2 + ((y - 800) / 30) ** 2 > 1.0:
            continue
        r = 0.8 + rng.random() * 1.4
        a.ellipse(x, y, r, r, mix(SKIN_SHADOW, SKIN_DEEP, 0.35 + rng.random() * 0.25))
    a.ellipse(468, 792, 2.6, 2.1, mix(SKIN_DEEP, "#5a2f2b", 0.45))
    a.ellipse(734, 780, 1.6, 1.3, mix(SKIN_SHADOW, SKIN_DEEP, 0.5))

    # Very soft brush texture, the kind of tiny strokes a painter would leave.
    def inside(pt, poly):
        x, y = pt
        hit = False
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                if x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                    hit = not hit
        return hit

    for i in range(150):
        x = 440 + rng.random() * 320
        y = 500 + rng.random() * 445
        if not inside((x, y), FACE):
            continue
        length = 4 + rng.random() * 9
        angle = rng.random() * math.pi
        dx, dy = math.cos(angle) * length, math.sin(angle) * length
        tone = mix(SKIN_BASE, SKIN_LIGHT if i % 2 else SKIN_SHADOW, 0.12)
        a.line([(x, y), (x + dx, y + dy)], tone, 0.9)

    # Eye sockets and upper-lid shadow.
    for cx in (508, 692):
        a.soft_ellipse(cx, 718, 78, 42, SKIN_MID, SKIN_SHADOW, 0.38, steps=22)
        a.soft_ellipse(cx, 690, 74, 28, SKIN_MID, SKIN_SHADOW, 0.2, steps=18)

    # Chin highlight.
    a.soft_ellipse(598, 933, 45, 28, SKIN_MID, SKIN_LIGHT, 0.6, steps=20)

    # Ears, mostly hidden by hair and the headset.
    for cx, flip in ((402, -1), (798, 1)):
        ear = catmull_rom([
            (cx, 690), (cx + 34 * flip, 690), (cx + 44 * flip, 730),
            (cx + 36 * flip, 790), (cx + 12 * flip, 818), (cx, 805),
        ], samples=8)
        a.poly(ear, SKIN_MID)
        a.soft_poly(ear, SKIN_MID, SKIN_SHADOW, 0.5, steps=18,
                    centre=(cx + 18 * flip, 755))
        a.line(catmull_rom([(cx + 8 * flip, 705), (cx + 20 * flip, 740),
                            (cx + 14 * flip, 785)], closed=False, samples=8),
               SKIN_DEEP, 3)


def eyes(a: Art):
    # Realistic almond eyes. Slight asymmetry keeps the face alive.
    for cx, cy, width, height, tilt in ((508, 728, 52, 24, -2), (692, 726, 50, 23, 2)):
        out = -1 if cx < 600 else 1  # outer corner points away from the nose
        outline = catmull_rom([
            (cx - width, cy + 4), (cx - width * 0.55, cy - height * 0.7),
            (cx, cy - height), (cx + width * 0.55, cy - height * 0.6),
            (cx + width, cy + 2), (cx + width * 0.5, cy + height * 0.65),
            (cx, cy + height * 0.8), (cx - width * 0.55, cy + height * 0.55),
        ], samples=10)
        # A whisper of rose and teal eyeshadow on the lid.
        a.soft_ellipse(cx + out * 4, cy - 21, 44, 12, SKIN_SHADOW,
                       mix(PINK, TEAL, 0.5), 0.11, steps=18)
        # Sclera with a warm shadow in the corners.
        a.poly(outline, "#f7f0e8")
        a.soft_poly(outline, "#f7f0e8", "#cdbbb6", 0.35, steps=18, centre=(cx, cy + 6))
        a.soft_ellipse(cx - width * 0.7, cy, 20, 16, "#f7f0e8", "#d9c4be", 0.3, steps=14)
        a.soft_ellipse(cx + width * 0.7, cy, 20, 16, "#f7f0e8", "#d9c4be", 0.3, steps=14)

        # Iris.
        iris_r = 22
        a.ellipse(cx, cy + 2, iris_r + 2.0, iris_r + 2.0, "#0a363a")
        for i in range(16):
            t = i / 15
            r = iris_r * (1 - t * 0.92)
            c = mix("#0a4d50", "#67e0d3", smoothstep(t))
            a.ellipse(cx, cy + 2, r, r, c)
        # Radial iris fibres.
        for k in range(22):
            ang = k / 22 * math.tau
            x2 = cx + math.cos(ang) * 17.7
            y2 = cy + 2 + math.sin(ang) * 17.7
            a.line([(cx, cy + 2), (x2, y2)], mix("#1b8d86", "#8df0e4", 0.25), 1.0)
        a.ellipse(cx, cy + 2, 9.4, 10.2, "#061d20")
        a.ellipse(cx - 1, cy, 6.6, 7.2, "#031113")
        # Catchlights.
        a.ellipse(cx - 7, cy - 6, 6.2, 7.8, "#ffffff")
        a.ellipse(cx + 7, cy + 8, 3.0, 2.7, mix("#ffffff", "#bffff8", 0.35))
        a.ellipse(cx - 6, cy + 9, 2.2, 1.9, "#e8fffc")

        # Upper lid / lashes.
        lid = catmull_rom([
            (cx - width * 1.03, cy + 8), (cx - width * 0.6, cy - height * 0.8),
            (cx, cy - height * 1.12), (cx + width * 0.6, cy - height * 0.72),
            (cx + width * 1.03, cy + 5),
        ], closed=False, samples=12)
        a.line(lid, "#2a1a1c", 9 if tilt > 0 else 8)
        a.line(offset_path(lid, -5, side=1), "#5a3a3a", 4)
        # Outer wing, mirrored per eye.
        wing = [(cx + out * width * 1.03, cy + 5), (cx + out * width * 1.28, cy - 4),
                (cx + out * width * 1.36, cy - 10)]
        a.line(wing, "#24181a", 5)
        # A few separate lash hairs at the outer corner.
        for k in range(4):
            a.line([(cx + out * (width * 1.02 + k * 2.2), cy + 2 - k * 1.5),
                    (cx + out * (width * 1.22 + k * 7), cy - 5 - k * 4.2)],
                   "#2a1a1c", 2.2 - k * 0.25)

        # Lower lash line and waterline.
        lower = catmull_rom([
            (cx - width * 0.95, cy + 9), (cx - width * 0.45, cy + height * 0.68),
            (cx, cy + height * 0.82), (cx + width * 0.5, cy + height * 0.62),
            (cx + width * 0.98, cy + 6),
        ], closed=False, samples=10)
        a.line(lower, mix(SKIN_SHADOW, "#6b4444", 0.5), 3)
        a.line(offset_path(lower, -2), "#f9e4d8", 2)
        # Tear duct at the inner corner.
        inner_x = cx - out * width * 0.92
        a.ellipse(inner_x, cy + 8, 5.0, 4.2, mix(SKIN_SHADOW, LIP, 0.3))
        a.ellipse(inner_x + out * 1.5, cy + 7, 2.2, 1.8, "#f9ded4")

        # Eyelid crease.
        crease = catmull_rom([
            (cx - width * 0.92, cy - 8), (cx - width * 0.5, cy - height * 1.35),
            (cx, cy - height * 1.55), (cx + width * 0.55, cy - height * 1.3),
            (cx + width * 0.98, cy - 6),
        ], closed=False, samples=10)
        a.line(crease, mix(SKIN_SHADOW, SKIN_DEEP, 0.45), 3)


def brows(a: Art):
    for cx, flip in ((507, -1), (693, 1)):
        pts = catmull_rom([
            (cx - 54 * flip, 658), (cx - 24 * flip, 646), (cx + 10 * flip, 643),
            (cx + 44 * flip, 650), (cx + 58 * flip, 660),
        ], closed=False, samples=10)
        a.line(pts, "#0a4b4d", 9)
        a.line(offset_path(pts, 2, side=1), "#1c7e7c", 4)
        # A few individual hairs.
        for k in range(7):
            base = path_along(pts, 0.12 + k * 0.12)
            a.line([(base[0], base[1]), (base[0] + 9 * flip, base[1] - 8)], "#0a4b4d", 2)


def nose(a: Art):
    # Bridge highlight, tip, wings and nostrils.
    a.soft_ellipse(607, 752, 18, 66, SKIN_MID, SKIN_LIGHT, 0.7, steps=22)
    a.soft_ellipse(620, 792, 22, 42, SKIN_MID, SKIN_SHADOW, 0.5, steps=22)
    a.soft_ellipse(600, 806, 30, 18, SKIN_MID, SKIN_LIGHT, 0.55, steps=18)
    a.soft_ellipse(600, 830, 42, 16, SKIN_MID, SKIN_SHADOW, 0.45, steps=18)

    # Nose wings.
    a.line(catmull_rom([(566, 806), (558, 820), (568, 833), (582, 833)],
                       closed=False, samples=8), mix(SKIN_SHADOW, SKIN_DEEP, 0.35), 3)
    a.line(catmull_rom([(634, 806), (642, 820), (632, 833), (618, 833)],
                       closed=False, samples=8), mix(SKIN_SHADOW, SKIN_DEEP, 0.35), 3)
    # Nostril shadows.
    a.ellipse(576, 826, 7, 3.4, mix(SKIN_DEEP, "#5d302d", 0.35))
    a.ellipse(624, 826, 7, 3.4, mix(SKIN_DEEP, "#5d302d", 0.35))
    # Septum shadow.
    a.line([(586, 834), (600, 838), (614, 834)], mix(SKIN_SHADOW, SKIN_DEEP, 0.4), 2)


def lips(a: Art):
    upper = catmull_rom([
        (548, 874), (568, 860), (586, 864), (600, 856), (614, 864),
        (632, 860), (652, 874), (600, 881),
    ], samples=9)
    lower = catmull_rom([
        (548, 874), (600, 881), (652, 874), (640, 893), (600, 902), (560, 893),
    ], samples=9)

    a.poly(upper, LIP)
    a.poly(lower, mix(LIP, LIP_LIGHT, 0.45))
    a.soft_poly(lower, mix(LIP, LIP_LIGHT, 0.45), LIP_LIGHT, 0.6, steps=20,
                centre=(600, 890))
    a.soft_poly(upper, LIP, darken(LIP, 0.25), 0.4, steps=16, centre=(600, 878))

    # Mouth line and corners.
    a.line(catmull_rom([(548, 874), (572, 878), (600, 880), (628, 878), (652, 874)],
                       closed=False, samples=10), LIP_DARK, 3)
    a.ellipse(548, 874, 4, 3, mix(LIP_DARK, SKIN_SHADOW, 0.4))
    a.ellipse(652, 874, 4, 3, mix(LIP_DARK, SKIN_SHADOW, 0.4))

    # Fine vertical lines give the lips their texture.
    for i in range(7):
        x = 562 + i * 12
        a.line([(x, 884), (x + (i - 3) * 0.4, 896 - abs(i - 3) * 1.4)],
               mix(LIP, LIP_DARK, 0.28), 1.1)

    # Gloss and lower-lip shadow.
    a.soft_ellipse(590, 889, 22, 7, mix(LIP, LIP_LIGHT, 0.45), "#ffe4e3", 0.55, steps=14)
    a.soft_ellipse(600, 908, 34, 8, SKIN_MID, SKIN_SHADOW, 0.45, steps=16)
    # Philtrum.
    a.soft_ellipse(600, 844, 14, 20, SKIN_MID, SKIN_SHADOW, 0.25, steps=14)

    # Faint nasolabial shadows keep the smile from floating on the face.
    for side in (1, -1):
        line = catmull_rom([(600 + 48 * side, 838), (600 + 57 * side, 854),
                            (600 + 54 * side, 869)], closed=False, samples=8)
        a.line(line, mix(SKIN_SHADOW, SKIN_DEEP, 0.18), 2)


def hair_front(a: Art):
    # Hair cap and bangs.
    cap = catmull_rom([
        (410, 470), (424, 372), (500, 310), (600, 292), (700, 310),
        (776, 372), (790, 470), (784, 520), (700, 505), (600, 498),
        (500, 505), (416, 520),
    ], samples=10)
    a.poly(cap, HAIR_DARK)
    a.soft_poly(cap, HAIR_DARK, HAIR_BASE, 0.8, steps=28, centre=(560, 450))
    a.soft_ellipse(520, 400, 150, 80, HAIR_BASE, mix(HAIR_MID, HAIR_LIGHT, 0.35), 0.75, steps=26)
    a.soft_ellipse(760, 560, 60, 170, HAIR_DARK, "#063033", 0.7, steps=24)

    # Bangs: seven pointed locks with different depths.
    bangs = [
        ([(430, 500), (400, 600), (420, 690), (458, 668), (470, 585), (500, 470)], 0.0),
        ([(475, 430), (455, 560), (470, 675), (512, 692), (522, 620), (540, 430)], 0.12),
        ([(540, 405), (525, 540), (548, 660), (582, 688), (596, 600), (606, 400)], 0.2),
        ([(606, 400), (612, 560), (628, 675), (658, 690), (670, 590), (675, 430)], 0.15),
        ([(675, 430), (688, 565), (700, 690), (735, 662), (742, 555), (745, 470)], 0.08),
        ([(745, 470), (756, 590), (764, 680), (792, 630), (790, 560), (780, 490)], 0.0),
    ]
    for points, hi in bangs:
        shape = catmull_rom(points, samples=8)
        base = mix(HAIR_BASE, HAIR_DARK, 0.35)
        a.poly(shape, base)
        a.soft_poly(shape, base, HAIR_MID, 0.55, steps=20,
                    centre=(sum(p[0] for p in points) / len(points), 520))
        a.line(shape, HAIR_DARK, 3)
        mid = catmull_rom([
            ((points[0][0] + points[1][0]) / 2 + 4, (points[0][1] + points[1][1]) / 2 + 12),
            ((points[1][0] + points[2][0]) / 2 + 2, (points[1][1] + points[2][1]) / 2 - 4),
            ((points[2][0] + points[3][0]) / 2 + 3, (points[2][1] + points[3][1]) / 2 - 26),
        ], closed=False, samples=8)
        a.line(mid, mix(HAIR_MID, HAIR_LIGHT, 0.22), 2.2)
        if hi:
            strand = catmull_rom([
                (points[0][0] + 10, points[0][1] + 20),
                (points[1][0] + 6, points[1][1] - 10),
                (points[2][0] + 8, points[2][1] - 26),
            ], closed=False, samples=8)
            a.line(strand, mix(HAIR_MID, HAIR_LIGHT, 0.45 + hi), 4)

    # The characteristic sharp side locks framing the face.
    for side in (1, -1):
        lock = catmull_rom([
            (430, 480), (400, 640), (416, 830), (440, 1010), (470, 1140),
            (490, 1060), (482, 910), (476, 750), (478, 590), (500, 490),
        ], samples=10)
        shape = [(x if side == 1 else W - x, y) for x, y in lock]
        a.poly(shape, HAIR_DARK)
        a.soft_poly(shape, HAIR_DARK, HAIR_BASE, 0.85, steps=24,
                    centre=(450 if side == 1 else W - 450, 800))
        edge = [(x if side == 1 else W - x, y) for x, y in
                catmull_rom([(438, 700), (452, 860), (470, 1040), (478, 1120)],
                            closed=False, samples=10)]
        a.line(edge, mix(HAIR_MID, HAIR_DARK, 0.4), 5)
        a.line(offset_path(edge, -8), mix(HAIR_MID, HAIR_LIGHT, 0.35), 2)

    # A few loose locks falling over the shoulders.
    for side in (1, -1):
        lock = catmull_rom([
            (455, 980), (430, 1120), (420, 1270), (440, 1400), (470, 1500),
            (500, 1410), (500, 1260), (500, 1100), (510, 1000),
        ], samples=9)
        shape = [(x if side == 1 else W - x, y) for x, y in lock]
        a.poly(shape, HAIR_DARK)
        a.soft_poly(shape, HAIR_DARK, HAIR_BASE, 0.7, steps=20,
                    centre=(460 if side == 1 else W - 460, 1250))
        a.line([(x if side == 1 else W - x, y) for x, y in
                catmull_rom([(455, 1020), (440, 1200), (450, 1380), (475, 1470)],
                            closed=False, samples=10)],
               mix(HAIR_MID, HAIR_LIGHT, 0.2), 3)


def headset(a: Art):
    # Headband, tucked under the bangs but visible at the temples.
    band = catmull_rom([
        (396, 646), (420, 520), (500, 430), (600, 405), (700, 430),
        (780, 520), (806, 646),
    ], closed=False, samples=12)
    a.line(catmull_rom([(392, 664), (410, 530), (492, 438), (600, 412),
                        (708, 438), (790, 530), (810, 664)], closed=False, samples=12),
           "#080d12", 30)
    a.line(catmull_rom([(392, 650), (410, 522), (492, 430), (600, 404),
                        (708, 430), (790, 522), (810, 650)], closed=False, samples=12),
           OUT_HI, 8)
    a.line(catmull_rom([(396, 638), (412, 512), (492, 422), (600, 398),
                        (708, 422), (790, 512), (806, 638)], closed=False, samples=12),
           "#0b1418", 4)

    # Ear cups.
    for cx, flip in ((392, -1), (808, 1)):
        a.ellipse(cx, 742, 44, 64, "#080d12")
        a.ellipse(cx, 742, 36, 55, "#202a33")
        a.ellipse(cx + 4 * flip, 742, 28, 46, "#0b1116")
        a.ellipse(cx + 4 * flip, 742, 22, 38, TEAL)
        a.ellipse(cx + 4 * flip, 742, 16, 30, "#0b5f60")
        a.ellipse(cx + 9 * flip, 730, 6, 16, mix(TEAL, "#ffffff", 0.45))
        a.ellipse(cx - 12 * flip, 760, 3.5, 10, "#062e30")

    # Mic boom on the viewer's left, ending in front of the cheek.
    boom = catmull_rom([(378, 782), (400, 820), (445, 852), (492, 868)],
                       closed=False, samples=12)
    a.line(boom, "#070b0f", 12)
    a.line(offset_path(boom, 2), "#36424e", 3)
    a.ellipse(500, 870, 17, 10, "#0a1014")
    a.ellipse(500, 870, 13, 7, "#35424d")
    a.ellipse(503, 868, 6, 4, TEAL_LIGHT)


def foreground(a: Art):
    # Two locks of the twin-tails fall in front of the shoulders, which gives
    # the bust a little depth instead of hiding all of the hair behind the body.
    for side in (1, -1):
        lock = catmull_rom([
            (250, 1060), (212, 1180), (188, 1330), (198, 1470),
            (228, 1560), (258, 1480), (254, 1340), (278, 1200), (300, 1080),
        ], samples=10)
        shape = [(x if side == 1 else W - x, y) for x, y in lock]
        a.poly(shape, HAIR_DARK)
        a.soft_poly(shape, HAIR_DARK, HAIR_BASE, 0.8, steps=22,
                    centre=(225 if side == 1 else W - 225, 1320))
        a.line([(x if side == 1 else W - x, y) for x, y in
                catmull_rom([(242, 1110), (210, 1260), (208, 1410), (230, 1520)],
                            closed=False, samples=10)],
               mix(HAIR_MID, HAIR_LIGHT, 0.25), 4)
        a.line([(x if side == 1 else W - x, y) for x, y in
                catmull_rom([(262, 1100), (246, 1240), (244, 1390), (256, 1500)],
                            closed=False, samples=10)],
               mix(HAIR_LIGHT, "#d9fffb", 0.25), 2)

    # Bright rim light along the right side of the face, hair and shoulder.
    rim = catmull_rom([
        (792, 600), (796, 710), (778, 815), (735, 900), (680, 955),
        (640, 978),
    ], closed=False, samples=10)
    a.line(rim, mix(TEAL_LIGHT, "#ffffff", 0.45), 5)
    a.line(offset_path(rim, -7), mix(TEAL_LIGHT, "#ffffff", 0.15), 2)

    # Soft teal bounce light on the jaw and neck.
    a.soft_ellipse(758, 858, 34, 70, SKIN_SHADOW, TEAL_LIGHT, 0.18, steps=20)
    a.soft_ellipse(700, 1030, 40, 80, SKIN_SHADOW, TEAL_LIGHT, 0.16, steps=18)

    # Loose flyaway hairs, painted last so they catch the light.
    rng = random.Random(3939)
    flyaways = [
        [(430, 500), (390, 470), (352, 452)],
        [(470, 460), (432, 420), (400, 386)],
        [(730, 448), (766, 404), (792, 360)],
        [(760, 500), (802, 470), (840, 452)],
        [(462, 660), (436, 610), (422, 560)],
        [(742, 620), (772, 570), (790, 520)],
        [(430, 1240), (398, 1300), (382, 1360)],
        [(450, 1460), (420, 1520), (408, 1570)],
    ]
    for pts in flyaways:
        a.line(catmull_rom(pts, closed=False, samples=8),
               mix(HAIR_LIGHT, "#d8fffb", rng.random() * 0.35), 1.8)

    # A tiny signature, keeping the portrait from feeling like stock art.
    a.text(1062, 1540, "39", "#2f8883", size=34, bold=True)
    a.text(1062, 1502, "MIKU", "#23625f", size=14, bold=True)


def draw_miku() -> Art:
    a = Art()
    background(a)
    hair_back(a)
    body(a)
    neck(a)
    face(a)
    eyes(a)
    brows(a)
    nose(a)
    lips(a)
    hair_front(a)
    headset(a)
    foreground(a)
    return a


if __name__ == "__main__":
    draw_miku().save()
