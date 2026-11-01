#!/usr/bin/env python3
"""Almuri comment kit: Lina-style reply images for Instagram comments.

Renders every reply three ways:
  png/<name>.png       1080x1080 still (last frame), night background
  gif/<name>.gif       540x540 looping animation
  stickers/<name>.png  transparent cut-out (only replies that stand on their own)
and a contact sheet, preview.png.

Run:  python3 make_kit.py            (all replies)
      python3 make_kit.py thank-you  (one or more by name)

Needs Pillow, numpy and ffmpeg. Fonts (Permanent Marker, Caveat: Apache/OFL)
are downloaded from github.com/google/fonts into .fonts/ on first run;
JetBrains Mono and Inter come from the system font folder.
"""
import math
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 20
GIF_SIZE = 540
PNG_SIZE = 1080

# ---------------------------------------------------------------- palette
NIGHT_TOP = (19, 23, 43)
NIGHT_BOT = (9, 11, 22)
GLOW = (44, 54, 102)
OFFWHITE = (243, 238, 227)
DIM = (128, 136, 168)
INK = (30, 29, 36)
RED_INK = (214, 48, 66)
MINT = (124, 255, 178)
AMBER = (255, 186, 82)
NEON_BLUE = (110, 200, 255)
NEON_PINK = (255, 105, 180)
YELLOW = (255, 216, 77)
PINK = (255, 150, 184)
GREEN = (146, 229, 164)
BLUE = (146, 204, 255)
ORANGE = (255, 178, 112)
LILAC = (198, 176, 255)

# ---------------------------------------------------------------- fonts
FONT_DIR = os.path.join(HERE, ".fonts")
REMOTE_FONTS = {
    "marker": ("PermanentMarker-Regular.ttf",
               "apache/permanentmarker/PermanentMarker-Regular.ttf"),
    "caveat": ("Caveat-wght.ttf", "ofl/caveat/Caveat%5Bwght%5D.ttf"),
}
SYSTEM_FONTS = {
    "mono": "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf",
    "mono-x": "/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf",
    "black": "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
}


def font_path(key):
    if key in SYSTEM_FONTS:
        return SYSTEM_FONTS[key]
    fname, remote = REMOTE_FONTS[key]
    path = os.path.join(FONT_DIR, fname)
    if not os.path.exists(path):
        os.makedirs(FONT_DIR, exist_ok=True)
        url = "https://raw.githubusercontent.com/google/fonts/main/" + remote
        print("downloading", url)
        urllib.request.urlretrieve(url, path)
    return path


_font_cache = {}


def font(key, size):
    size = max(1, int(round(size)))
    ck = (key, size)
    if ck not in _font_cache:
        base = key.split(":")[0]
        f = ImageFont.truetype(font_path(base), size)
        if key == "caveat:bold":
            f.set_variation_by_axes([700])
        _font_cache[ck] = f
    return _font_cache[ck]


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, t0, t1):
    """0..1 progress of t through the window [t0, t1]."""
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def ease_out_cubic(p):
    return 1 - (1 - p) ** 3


def ease_in_cubic(p):
    return p ** 3


def ease_out_back(p, s=1.8):
    p -= 1
    return p * p * ((s + 1) * p + s) + 1


def ease_in_out(p):
    return 0.5 - 0.5 * math.cos(math.pi * p)


# ---------------------------------------------------------------- canvas
class Canvas:
    """A square RGBA frame. All coordinates are on a 1080 grid and scaled."""

    def __init__(self, size, background=True):
        self.size = size
        self.k = size / 1080.0
        if background:
            self.img = night_background(size).copy()
        else:
            self.img = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    def u(self, v):
        return int(round(v * self.k))

    def paste(self, layer, cx, cy):
        """Alpha-composite `layer` centred on grid point (cx, cy)."""
        x = int(round(cx * self.k - layer.width / 2))
        y = int(round(cy * self.k - layer.height / 2))
        _composite(self.img, layer, x, y)

    def draw(self):
        return ImageDraw.Draw(self.img)


def _composite(base, layer, x, y):
    # alpha_composite needs the layer inside the canvas: crop what overflows.
    bx0, by0 = max(0, x), max(0, y)
    bx1 = min(base.width, x + layer.width)
    by1 = min(base.height, y + layer.height)
    if bx1 <= bx0 or by1 <= by0:
        return
    piece = layer.crop((bx0 - x, by0 - y, bx1 - x, by1 - y))
    base.alpha_composite(piece, dest=(bx0, by0))


_bg_cache = {}


def night_background(size):
    if size in _bg_cache:
        return _bg_cache[size]
    ys = np.linspace(0, 1, size)[:, None]
    xs = np.linspace(0, 1, size)[None, :]
    top, bot, glow = (np.array(c, dtype=np.float32) for c in (NIGHT_TOP, NIGHT_BOT, GLOW))
    base = top[None, None, :] * (1 - ys[..., None]) + bot[None, None, :] * ys[..., None]
    # soft monitor glow, a little above centre
    d = np.sqrt((xs - 0.5) ** 2 + ((ys - 0.40) * 1.15) ** 2)
    g = np.clip(1 - d / 0.62, 0, 1) ** 2 * 0.55
    rgb = base * (1 - g[..., None]) + glow[None, None, :] * g[..., None]
    # vignette
    v = np.clip(1 - (d - 0.45) * 0.55, 0.78, 1)
    rgb = rgb * v[..., None]
    arr = np.dstack([np.clip(rgb, 0, 255).astype(np.uint8),
                     np.full((size, size), 255, np.uint8)])
    img = Image.fromarray(arr, "RGBA")
    _bg_cache[size] = img
    return img


def watermark(cv):
    f = font("mono", 26 * cv.k)
    d = cv.draw()
    d.text((cv.size / 2, cv.u(1040)), "@heyalmuri", font=f, anchor="mm",
           fill=OFFWHITE + (90,))


# ---------------------------------------------------------------- text
def text_layer(text, fnt, fill, stroke=0, stroke_fill=None):
    """Tight RGBA image of `text` (ink bounding box plus a small pad)."""
    pad = max(4, int(fnt.size * 0.12)) + stroke
    x0, y0, x1, y1 = fnt.getbbox(text, stroke_width=stroke)
    img = Image.new("RGBA", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((pad - x0, pad - y0), text, font=fnt, fill=fill,
                             stroke_width=stroke, stroke_fill=stroke_fill)
    return img


def reveal(img, p):
    """Left-to-right 'being written' crop with a soft leading edge."""
    if p >= 1:
        return img
    if p <= 0:
        return None
    w = img.width
    edge = max(2, int(w * 0.06))
    cut = int((w + edge) * p)
    ramp = np.clip((cut - np.arange(w)) / edge, 0, 1).astype(np.float32)
    a = np.asarray(img.getchannel("A"), dtype=np.float32) * ramp[None, :]
    out = img.copy()
    out.putalpha(Image.fromarray(a.astype(np.uint8), "L"))
    return out


def paste_px(base, layer, cx, cy):
    """Composite `layer` centred on pixel (cx, cy) of `base`."""
    if layer is None:
        return
    _composite(base, layer, int(round(cx - layer.width / 2)), int(round(cy - layer.height / 2)))


def typed(text, p):
    n = int(round(len(text) * clamp(p)))
    return text[:n]


# ---------------------------------------------------------------- shapes
def heart(draw, cx, cy, s, fill):
    """Heart of width ~s centred on (cx, cy)."""
    r = s * 0.27
    draw.ellipse((cx - 2 * r + r * 0.12, cy - r * 1.55, cx + r * 0.12, cy + r * 0.45), fill=fill)
    draw.ellipse((cx - r * 0.12, cy - r * 1.55, cx + 2 * r - r * 0.12, cy + r * 0.45), fill=fill)
    draw.polygon([(cx - 1.93 * r, cy - r * 0.35), (cx + 1.93 * r, cy - r * 0.35),
                  (cx, cy + r * 1.95)], fill=fill)


def heart_layer(s, fill):
    big = int(s * 4)
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    heart(ImageDraw.Draw(img), big / 2, big / 2, big * 0.8, fill)
    return img.resize((int(s), int(s)), Image.LANCZOS)


def polyline_partial(draw, pts, p, fill, width):
    """Draw the first fraction p (by length) of a polyline, with round joints."""
    if p <= 0 or len(pts) < 2:
        return
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(segs)
    left = total * clamp(p)
    out = [pts[0]]
    for i, sl in enumerate(segs):
        if left >= sl:
            out.append(pts[i + 1])
            left -= sl
        else:
            f = left / sl if sl else 0
            a, b = pts[i], pts[i + 1]
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
            break
    draw.line(out, fill=fill, width=int(width), joint="curve")
    r = width / 2
    for q in (out[0], out[-1]):
        draw.ellipse((q[0] - r, q[1] - r, q[0] + r, q[1] + r), fill=fill)


def check_points(x, y, s):
    """Tick mark whose box starts at (x, y) and is s wide."""
    return [(x, y + s * 0.52), (x + s * 0.36, y + s * 0.86), (x + s, y + s * 0.12)]


def bezier(p0, p1, p2, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                    (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return pts


def glow(layer, k, radii=(22, 8), strength=(1.0, 0.9)):
    """Neon-style bloom around a layer's opaque pixels."""
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    for r, s in zip(radii, strength):
        b = layer.filter(ImageFilter.GaussianBlur(r * k))
        if s != 1.0:
            a = np.asarray(b.getchannel("A"), dtype=np.float32) * s
            b.putalpha(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "L"))
        out.alpha_composite(b)
    out.alpha_composite(layer)
    return out


def padded(layer, pad):
    out = Image.new("RGBA", (layer.width + 2 * pad, layer.height + 2 * pad), (0, 0, 0, 0))
    out.alpha_composite(layer, dest=(pad, pad))
    return out


def with_alpha(layer, a):
    if a >= 1:
        return layer
    out = layer.copy()
    arr = np.asarray(out.getchannel("A"), dtype=np.float32) * clamp(a)
    out.putalpha(Image.fromarray(arr.astype(np.uint8), "L"))
    return out


def shadow_of(layer, k, blur=16, alpha=0.55):
    """Soft drop shadow. Padded so the blur is not clipped; it keeps the same
    centre as `layer`, so paste it with paste_px at the layer's centre + offset."""
    pad = int(blur * k * 3) + 2
    a = padded(layer, pad).getchannel("A").filter(ImageFilter.GaussianBlur(blur * k))
    arr = np.asarray(a, dtype=np.float32) * alpha
    sh = Image.new("RGBA", a.size, (0, 0, 0, 0))
    sh.putalpha(Image.fromarray(arr.astype(np.uint8), "L"))
    return sh


# ---------------------------------------------------------------- props
def note_face(w, h, color):
    """A square sticky note: glue strip, soft gradient, lifted bottom edge."""
    ys = np.linspace(0, 1, h)[:, None]
    c = np.array(color, dtype=np.float32)
    shade = 1.04 - 0.10 * ys                      # lighter top, darker bottom
    shade = shade - 0.035 * (ys < 0.17)           # glue strip
    lift = np.clip((ys - 0.86) / 0.14, 0, 1) ** 2  # curl at the bottom edge
    shade = shade - 0.10 * lift
    rgb = np.clip(c[None, None, :] * shade[..., None], 0, 255)
    rgb = np.broadcast_to(rgb, (h, w, 3)).astype(np.uint8)
    arr = np.dstack([rgb, np.full((h, w), 255, np.uint8)])
    img = Image.fromarray(arr, "RGBA")
    # the curl makes the bottom corners slightly narrower
    mask = Image.new("L", (w, h), 0)
    curl = int(h * 0.018)
    ImageDraw.Draw(mask).polygon([(0, 0), (w, 0), (w, h - curl), (w - curl * 3, h),
                                  (curl * 3, h), (0, h - curl)], fill=255)
    img.putalpha(mask)
    return img


def place_note(cv, face, cx, cy, angle=0.0, scale=1.0, lift=0.0, alpha=1.0):
    """Rotate/scale a finished note (text already drawn) and drop it with a shadow.
    `lift` > 0 makes the shadow larger and further away (note in the air)."""
    k = cv.k
    layer = face
    if scale != 1.0:
        layer = layer.resize((max(1, int(face.width * scale)), max(1, int(face.height * scale))),
                             Image.LANCZOS)
    pad = int(60 * k)
    layer = padded(layer, pad).rotate(angle, resample=Image.BICUBIC, expand=True)
    sh = shadow_of(layer, k, blur=14 + 26 * lift, alpha=0.55 - 0.2 * lift)
    off = (10 + 40 * lift) * k, (18 + 60 * lift) * k
    sh = with_alpha(sh, alpha)
    paste_px(cv.img, sh, cx * k + off[0], cy * k + off[1])
    paste_px(cv.img, with_alpha(layer, alpha), cx * k, cy * k)


def slap_params(t, t0, dur=0.42):
    """Scale/lift/alpha for a note being slapped onto the wall."""
    p = prog(t, t0, t0 + dur)
    if p <= 0:
        return None
    scale = 1.32 - 0.32 * ease_out_back(p, 1.3)
    lift = clamp(1 - ease_out_cubic(p) * 1.15, 0, 1)
    return dict(scale=scale, lift=lift, alpha=clamp(p * 3))


def pushpin(cv, cx, cy, drop=0.0, color=(232, 64, 72)):
    """A round pushpin head at (cx, cy); drop 0..1 is how far it is from landing."""
    k = cv.k
    s = 46
    y = cy - 120 * drop
    sc = 1 + 0.5 * drop
    big = int(s * 4 * k * sc)
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = big * 0.36
    c = big / 2
    d.ellipse((c - r, c - r, c + r, c + r), fill=color + (255,))
    hr = r * 0.38
    d.ellipse((c - r * 0.45 - hr, c - r * 0.45 - hr, c - r * 0.45 + hr, c - r * 0.45 + hr),
              fill=(255, 255, 255, 150))
    img = img.resize((max(1, big // 2), max(1, big // 2)), Image.LANCZOS)
    sh = shadow_of(img, k, blur=6 + 14 * drop, alpha=0.6)
    paste_px(cv.img, sh, cx * k + (8 + 30 * drop) * k, y * k + (12 + 50 * drop) * k)
    paste_px(cv.img, img, cx * k, y * k)


def tape(w, h, k, color=(236, 224, 192), alpha=215, seed=3):
    """Masking tape strip with torn ends."""
    rng = np.random.default_rng(seed)
    W, H = int(w * k), int(h * k)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    teeth = 9
    left = [(rng.uniform(0, 0.035) * W, H * i / teeth) for i in range(teeth + 1)]
    right = [(W - rng.uniform(0, 0.035) * W, H * i / teeth) for i in range(teeth + 1)]
    d.polygon(left + right[::-1], fill=color + (alpha,))
    # faint paper fibres
    for _ in range(int(W / 14)):
        x = rng.uniform(0.04, 0.96) * W
        y = rng.uniform(0, 1) * H
        d.line((x, y, x + rng.uniform(-8, 8) * k, y + rng.uniform(4, 12) * k),
               fill=(255, 255, 255, 18), width=max(1, int(k)))
    return img


def terminal_window(cv, x0, y0, x1, y1, title):
    k = cv.k
    win = Image.new("RGBA", (int((x1 - x0) * k), int((y1 - y0) * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(win)
    r = 28 * k
    d.rounded_rectangle((0, 0, win.width - 1, win.height - 1), radius=r,
                        fill=(20, 24, 42, 250), outline=(70, 80, 120, 255), width=max(1, int(3 * k)))
    bar = 74 * k
    d.rounded_rectangle((0, 0, win.width - 1, bar), radius=r, fill=(32, 37, 62, 255))
    d.rectangle((0, bar - r, win.width - 1, bar), fill=(32, 37, 62, 255))
    d.line((0, bar, win.width, bar), fill=(70, 80, 120, 255), width=max(1, int(2 * k)))
    for i, c in enumerate([(240, 106, 106), (244, 191, 79), (110, 211, 129)]):
        cx, cy, rr = (44 + i * 40) * k, bar / 2, 12 * k
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=c + (255,))
    d.text((win.width / 2, bar / 2), title, font=font("mono", 28 * k), anchor="mm", fill=DIM)
    cx, cy = (x0 + x1) / 2 * k, (y0 + y1) / 2 * k
    paste_px(cv.img, shadow_of(win, k, blur=30, alpha=0.6), cx + 12 * k, cy + 26 * k)
    paste_px(cv.img, win, cx, cy)


def keycap(cv, cx, cy, w, h, label, pressed=0.0, label_size=84):
    """A chunky keyboard key; pressed 0..1 pushes it down."""
    k = cv.k
    depth = 26 * (1 - 0.8 * pressed)
    W, H = int(w * k), int((h + 30) * k)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = 30 * k
    top = (30 - depth) * k + 4 * k
    d.rounded_rectangle((0, 30 * k, W - 1, H - 1), radius=r, fill=(150, 144, 134, 255))
    d.rounded_rectangle((0, top, W - 1, top + h * k - 30 * k), radius=r, fill=(238, 233, 222, 255))
    d.rounded_rectangle((14 * k, top + 10 * k, W - 14 * k, top + h * k - 46 * k), radius=r * 0.7,
                        fill=(246, 242, 233, 255))
    d.text((W / 2, top + (h * k - 30 * k) / 2 - 4 * k), label, font=font("mono", label_size * k),
           anchor="mm", fill=INK)
    sh = shadow_of(img, k, blur=18, alpha=0.6)
    paste_px(cv.img, sh, cx * k + 8 * k, cy * k + 22 * k)
    paste_px(cv.img, img, cx * k, cy * k)


# ---------------------------------------------------------------- scenes
# Each scene: draw(cv, t) for t in seconds, plus duration and whether a
# transparent sticker makes sense.

def note_with_lines(cv, color, w, h, lines, t):
    """Build a note face and draw handwriting lines on it.
    lines: list of (text, font_key, size, fill, rel_y, t0, t1)."""
    k = cv.k
    face = note_face(int(w * k), int(h * k), color)
    for text, fk, size, fill, ry, t0, t1 in lines:
        layer = text_layer(text, font(fk, size * k), fill)
        paste_px(face, reveal(layer, prog(t, t0, t1)), face.width / 2, face.height * ry)
    return face


def scene_thank_you(cv, t):
    k = cv.k
    sp = slap_params(t, 0.05)
    if not sp:
        return
    face = note_with_lines(cv, YELLOW, 660, 660, [
        ("thank", "marker", 168, INK, 0.30, 0.50, 0.95),
        ("you!", "marker", 168, INK, 0.56, 0.95, 1.35),
        ("— lina, 2:47 am", "caveat:bold", 64, (92, 76, 30), 0.85, 1.75, 2.25),
    ], t)
    # underline swoosh under "you!"
    d = ImageDraw.Draw(face)
    W, H = face.size
    pts = bezier((W * 0.24, H * 0.705), (W * 0.52, H * 0.665), (W * 0.80, H * 0.69))
    polyline_partial(d, pts, ease_out_cubic(prog(t, 1.38, 1.65)), RED_INK + (255,), 11 * k)
    place_note(cv, face, 540, 520, angle=-4, **sp)


def scene_thank_you_human(cv, t):
    k = cv.k
    sp = slap_params(t, 0.05)
    if not sp:
        return
    face = note_with_lines(cv, PINK, 660, 660, [
        ("thank you,", "marker", 112, INK, 0.21, 0.50, 1.15),
        ("AI", "marker", 150, INK, 0.47, 1.20, 1.45),
        ("human.", "marker", 138, INK, 0.76, 2.35, 2.95),
    ], t)
    W, H = face.size
    d = ImageDraw.Draw(face)
    # scribble over "AI"
    zig = []
    n = 7
    for i in range(n + 1):
        x = W * (0.33 + 0.34 * i / n)
        y = H * (0.47 + (0.05 if i % 2 else -0.05))
        zig.append((x, y))
    polyline_partial(d, zig, prog(t, 1.85, 2.25), RED_INK + (255,), 14 * k)
    hp = prog(t, 3.0, 3.25)
    if hp > 0:
        hs = 70 * k * ease_out_back(hp)
        if hs > 2:
            hw = font("marker", 138 * k).getlength("human.")
            paste_px(face, heart_layer(hs, RED_INK + (255,)), W / 2 + hw / 2 + 42 * k, H * 0.70)
    place_note(cv, face, 540, 520, angle=3, **sp)


def scene_it_works(cv, t):
    k = cv.k
    a = prog(t, 0.0, 0.3)
    strip = tape(600, 128, k)
    label = text_layer("IT WORKS", font("marker", 86 * k), INK)
    paste_px(strip, label, strip.width / 2, strip.height / 2 + 2 * k)
    strip = padded(strip, int(20 * k)).rotate(-2, resample=Image.BICUBIC, expand=True)
    paste_px(cv.img, with_alpha(shadow_of(strip, k, blur=8, alpha=0.35), a), 546 * k, 216 * k)
    paste_px(cv.img, with_alpha(strip, a), 540 * k, 210 * k)

    p = prog(t, 0.35, 0.95)
    if p > 0:
        e = ease_out_back(p, 1.2)
        cy = 640 + (1 - e) * 560
        ang = 2.5 + (1 - e) * 14
        face = note_with_lines(cv, GREEN, 540, 540, [
            ("this", "marker", 130, INK, 0.38, 1.15, 1.45),
            ("comment.", "marker", 112, INK, 0.66, 1.45, 2.05),
        ], t)
        place_note(cv, face, 540, cy, angle=ang, lift=clamp(1 - p * 1.4) * 0.8)
    pp = prog(t, 0.95, 1.12)
    if pp > 0:
        pushpin(cv, 540, 410, drop=1 - ease_in_cubic(pp))


def scene_noted(cv, t):
    sp = slap_params(t, 0.05)
    if not sp:
        return
    face = note_with_lines(cv, BLUE, 640, 640, [
        ("noted.", "marker", 170, INK, 0.47, 0.75, 1.35),
        ("going on the wall", "caveat:bold", 66, (36, 58, 92), 0.80, 1.5, 2.1),
    ], t)
    place_note(cv, face, 540, 530, angle=-3, **sp)
    pp = prog(t, 0.48, 0.66)
    if pp > 0:
        pushpin(cv, 548, 236, drop=1 - ease_in_cubic(pp), color=(250, 196, 60))


def scene_same(cv, t):
    sp = slap_params(t, 0.05)
    if not sp:
        return
    face = note_with_lines(cv, LILAC, 640, 640, [
        ("same.", "marker", 190, INK, 0.45, 0.5, 1.05),
        ("(it's 3 am)", "caveat:bold", 72, (64, 50, 108), 0.79, 1.3, 1.8),
    ], t)
    place_note(cv, face, 540, 520, angle=4, **sp)


def scene_lol(cv, t):
    sp = slap_params(t, 0.05)
    if not sp:
        return
    face = note_with_lines(cv, ORANGE, 640, 640, [
        ("lol", "marker", 250, INK, 0.43, 0.5, 0.95),
        ("(actually out loud)", "caveat:bold", 66, (110, 58, 20), 0.80, 1.2, 1.85),
    ], t)
    # the note shakes a little, like it is laughing
    wob = 0.0
    if 2.0 <= t <= 2.8:
        wob = math.sin((t - 2.0) * 36) * 2.2 * (1 - prog(t, 2.0, 2.8))
    place_note(cv, face, 540, 520, angle=-3 + wob, **sp)


def scene_git_commit(cv, t):
    k = cv.k
    terminal_window(cv, 70, 255, 1010, 815, "lina@night: ~")
    d = cv.draw()
    f = font("mono", 60 * k)
    x = 130 * k
    ys = [400, 495, 610, 710]
    cw = f.getlength("M")

    def put(col, row, text, fill):
        d.text((x + col * cw, ys[row] * k), text, font=f, anchor="lm", fill=fill)

    l1 = typed("git commit -m", prog(t, 0.25, 0.95))
    put(0, 0, "$", MINT)
    put(2, 0, l1, OFFWHITE)
    l2 = typed('"thank you"', prog(t, 1.05, 1.6))
    put(2, 1, l2, AMBER)
    cursor_on = int(t * 2.5) % 2 == 0
    if t < 0.95:
        cur = (2 + len(l1), 0)
    elif t < 1.6:
        cur = (2 + len(l2), 1)
    if t >= 1.9:
        cx0 = x + 4 * k
        polyline_partial(d, check_points(cx0, (ys[2] - 20) * k, 40 * k), 1.0, MINT, 8 * k)
        put(2, 2, "1 heart inserted", MINT)
        hx = x + (2 + len("1 heart inserted") + 1.0) * cw
        paste_px(cv.img, heart_layer(52 * k, NEON_PINK + (255,)), hx, ys[2] * k + 2 * k)
    if t >= 2.15:
        put(0, 3, "$", MINT)
        cur = (2, 3)
    if t < 1.6 or t >= 2.15:
        if cursor_on or t < 1.6:
            cx, cy = x + cur[0] * cw, ys[cur[1]] * k
            d.rectangle((cx, cy - 34 * k, cx + cw * 0.9, cy + 34 * k), fill=OFFWHITE)


def scene_200_ok(cv, t):
    k = cv.k
    d = cv.draw()
    d.text((540 * k, 330 * k), "HTTP/1.1", font=font("mono", 50 * k), anchor="mm",
           fill=DIM + (int(255 * prog(t, 0.0, 0.3)),))
    big = typed("200 OK", prog(t, 0.3, 0.9))
    fb = font("mono-x", 230 * k)
    full_w = fb.getlength("200 OK")
    x0 = 540 * k - full_w / 2
    if big:
        layer = Image.new("RGBA", cv.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((x0, 500 * k), big, font=fb, anchor="lm", fill=MINT)
        cv.img.alpha_composite(glow(layer, k, radii=(30, 10), strength=(0.8, 0.6)))
    if t < 1.05:
        if int(t * 5) % 2 == 0 or t < 0.9:
            cx = x0 + fb.getlength(big) + 10 * k
            d.rectangle((cx, 420 * k, cx + 24 * k, 580 * k), fill=MINT)
    small = typed("thanks received", prog(t, 1.15, 2.0))
    fs = font("mono", 62 * k)
    sw = fs.getlength("thanks received")
    sx = 540 * k - sw / 2 - 30 * k
    d.text((sx, 720 * k), small, font=fs, anchor="lm", fill=OFFWHITE)
    hp = prog(t, 2.1, 2.35)
    if hp > 0:
        hs = 64 * k * ease_out_back(hp)
        if hs > 2:
            paste_px(cv.img, heart_layer(hs, NEON_PINK + (255,)), sx + sw + 55 * k, 720 * k)


def scene_check_dms(cv, t):
    k = cv.k
    d = cv.draw()
    if t < 1.35:
        # sending... progress bar
        p = ease_in_out(prog(t, 0.15, 1.15))
        fade = 1 - prog(t, 1.15, 1.35)
        a = int(255 * fade)
        d.text((540 * k, 440 * k), "sending" + "." * (1 + int(t * 4) % 3), font=font("mono", 56 * k),
               anchor="mm", fill=OFFWHITE + (a,))
        bx0, bx1, by = 220 * k, 860 * k, 540 * k
        d.rounded_rectangle((bx0, by - 28 * k, bx1, by + 28 * k), radius=28 * k,
                            outline=DIM + (a,), width=max(1, int(4 * k)))
        fill_w = (bx1 - bx0 - 20 * k) * p
        if fill_w > 30 * k:
            d.rounded_rectangle((bx0 + 10 * k, by - 18 * k, bx0 + 10 * k + fill_w, by + 18 * k),
                                radius=18 * k, fill=MINT + (a,))
        d.text((540 * k, 630 * k), f"{int(p * 100)}%", font=font("mono", 46 * k), anchor="mm",
               fill=DIM + (a,))
        return
    # envelope pops in
    ep = prog(t, 1.35, 1.75)
    s = ease_out_back(ep, 1.6)
    if s > 0.02:
        W, H = 300, 210
        big = 3
        env = Image.new("RGBA", (int((W + 40) * k * big), int((H + 40) * k * big)), (0, 0, 0, 0))
        e = ImageDraw.Draw(env)
        u = k * big
        ox, oy = 20 * u, 20 * u
        e.rounded_rectangle((ox, oy, ox + W * u, oy + H * u), radius=22 * u, fill=(28, 33, 58, 255),
                            outline=OFFWHITE + (255,), width=int(12 * u))
        e.line([(ox + 16 * u, oy + 20 * u), (ox + W * u / 2, oy + H * u * 0.56),
                (ox + W * u - 16 * u, oy + 20 * u)], fill=OFFWHITE, width=int(12 * u), joint="curve")
        env = env.resize((max(1, int(env.width / big * s)), max(1, int(env.height / big * s))),
                         Image.LANCZOS)
        paste_px(cv.img, env, 540 * k, 300 * k)
        bp = prog(t, 1.75, 1.95)
        if bp > 0:
            br = 34 * k * ease_out_back(bp, 2.2)
            bx, by = 540 * k + 150 * k, 300 * k - 104 * k
            dd = cv.draw()
            dd.ellipse((bx - br - 6 * k, by - br - 6 * k, bx + br + 6 * k, by + br + 6 * k), fill=NIGHT_TOP)
            dd.ellipse((bx - br, by - br, bx + br, by + br), fill=NEON_PINK)
            if bp >= 1:
                dd.text((bx, by + 1 * k), "1", font=font("mono", 40 * k), anchor="mm", fill=OFFWHITE)
    l1 = text_layer("check your", font("marker", 116 * k), OFFWHITE)
    l2 = text_layer("DMs", font("marker", 190 * k), YELLOW)
    paste_px(cv.img, reveal(l1, prog(t, 1.9, 2.45)), 540 * k, 560 * k)
    paste_px(cv.img, reveal(l2, prog(t, 2.45, 2.85)), 540 * k, 720 * k)
    a = int(255 * prog(t, 2.95, 3.25))
    if a:
        f = font("mono", 40 * k)
        txt = "sent · 1 message"
        tw = f.getlength(txt)
        tx = 540 * k - tw / 2 + 28 * k
        d = cv.draw()
        polyline_partial(d, check_points(tx - 64 * k, 862 * k, 40 * k), 1.0, MINT + (a,), 8 * k)
        d.text((tx, 882 * k), txt, font=f, anchor="lm", fill=MINT + (a,))


def scene_lgtm(cv, t):
    k = cv.k
    impact = 0.42
    p = prog(t, 0.12, impact)
    shake = (0, 0)
    if impact <= t < impact + 0.25:
        q = (t - impact) / 0.25
        amp = 14 * (1 - q)
        shake = (math.sin(q * 40) * amp, math.cos(q * 33) * amp * 0.6)
    if p > 0:
        st = stamp_layer(k)
        scale = 2.3 - 1.3 * ease_in_cubic(p)
        stl = st.resize((max(1, int(st.width * scale)), max(1, int(st.height * scale))), Image.LANCZOS)
        stl = stl.rotate(-8, resample=Image.BICUBIC, expand=True)
        stl = with_alpha(stl, clamp(p * 2.5))
        if t >= impact:
            splat(cv, 540 + shake[0], 450 + shake[1], k)
        paste_px(cv.img, stl, (540 + shake[0]) * k, (450 + shake[1]) * k)
    cap = typed("looks good to me.", prog(t, 0.95, 1.75))
    f = font("mono", 54 * k)
    tw = f.getlength("looks good to me.")
    tx = 540 * k - tw / 2 - 34 * k
    d = cv.draw()
    d.text((tx, 760 * k), cap, font=f, anchor="lm", fill=OFFWHITE)
    hp = prog(t, 1.85, 2.1)
    if hp > 0:
        hs = 58 * k * ease_out_back(hp)
        if hs > 2:
            paste_px(cv.img, heart_layer(hs, NEON_PINK + (255,)), tx + tw + 52 * k, 760 * k)


_stamp_cache = {}


def stamp_layer(k):
    key = round(k, 3)
    if key in _stamp_cache:
        return _stamp_cache[key]
    W, H = int(700 * k), int(330 * k)
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    ink = (98, 232, 152)
    d.rounded_rectangle((8 * k, 8 * k, W - 8 * k, H - 8 * k), radius=36 * k, outline=ink + (255,),
                        width=int(16 * k))
    d.rounded_rectangle((32 * k, 32 * k, W - 32 * k, H - 32 * k), radius=22 * k, outline=ink + (255,),
                        width=int(5 * k))
    d.text((W / 2, H / 2 + 4 * k), "LGTM", font=font("black", 210 * k), anchor="mm", fill=ink + (255,))
    # worn ink: speckle the alpha with deterministic noise
    rng = np.random.default_rng(11)
    small = rng.random((max(1, H // 6), max(1, W // 6))).astype(np.float32)
    noise = np.asarray(Image.fromarray((small * 255).astype(np.uint8), "L").resize((W, H), Image.BICUBIC),
                       dtype=np.float32) / 255
    fine = rng.random((H, W)).astype(np.float32)
    a = np.asarray(img.getchannel("A"), dtype=np.float32)
    keep = np.clip((noise - 0.18) * 2.2, 0.35, 1) * np.where(fine < 0.06, 0.25, 1.0)
    img.putalpha(Image.fromarray(np.clip(a * keep, 0, 255).astype(np.uint8), "L"))
    _stamp_cache[key] = img
    return img


def splat(cv, cx, cy, k):
    rng = np.random.default_rng(5)
    d = cv.draw()
    for _ in range(16):
        ang = rng.uniform(0, 2 * math.pi)
        dist = rng.uniform(380, 470)
        x = cx + math.cos(ang) * dist * 0.95
        y = cy + math.sin(ang) * dist * 0.48
        r = rng.uniform(4, 11)
        d.ellipse(((x - r) * k, (y - r) * k, (x + r) * k, (y + r) * k), fill=(98, 232, 152, 170))


def scene_saved(cv, t):
    k = cv.k
    press = 0.0
    if 0.55 <= t < 0.95:
        press = ease_out_cubic(prog(t, 0.55, 0.65)) * (1 - ease_in_out(prog(t, 0.8, 0.95)))
    a = prog(t, 0.0, 0.25)
    if a > 0:
        keycap(cv, 360, 400, 340, 230, "ctrl", pressed=press, label_size=76)
        cv.draw().text((598 * k, 400 * k), "+", font=font("mono", 90 * k), anchor="mm", fill=DIM)
        keycap(cv, 790, 400, 230, 230, "S", pressed=press, label_size=110)
    sv = text_layer("saved.", font("marker", 170 * k), OFFWHITE)
    paste_px(cv.img, reveal(sv, prog(t, 1.05, 1.6)), 500 * k, 730 * k)
    d = cv.draw()
    cx = 500 * k + sv.width / 2 + 10 * k
    polyline_partial(d, check_points(cx, 670 * k, 110 * k), ease_out_cubic(prog(t, 1.65, 1.95)),
                     MINT, 22 * k)


def scene_night_shift(cv, t):
    k = cv.k

    def tube(text, fk, size, color, cy, on):
        f = font(fk, size * k)
        core = text_layer(text, f, (255, 255, 255, 255), stroke=int(2 * k), stroke_fill=color)
        if on:
            col = Image.new("RGBA", core.size, color + (255,))
            col.putalpha(core.getchannel("A"))
            pad = int(70 * k)
            layer = padded(col, pad)
            bloom = glow(layer, k, radii=(34, 12), strength=(1.0, 0.9))
            bloom.alpha_composite(padded(core, pad))
            paste_px(cv.img, bloom, 540 * k, cy * k)
        else:
            dim = tuple(int(c * 0.22) for c in color)
            off = text_layer(text, f, dim + (255,))
            paste_px(cv.img, off, 540 * k, cy * k)

    def flick(t0, pattern):
        # pattern of (duration, on) steps starting at t0; on after the pattern
        if t < t0:
            return False
        acc = t0
        for dur, on in pattern:
            if t < acc + dur:
                return on
            acc += dur
        return True

    moon_on = flick(1.7, [(0.1, True), (0.1, False)])
    l1_on = flick(0.2, [(0.08, True), (0.12, False), (0.06, True), (0.2, False)])
    l2_on = flick(0.85, [(0.06, True), (0.1, False), (0.12, True), (0.06, False), (0.05, True), (0.15, False)])
    if 3.1 <= t < 3.2:
        l2_on = False
    # moon
    mlayer = Image.new("RGBA", (int(260 * k), int(260 * k)), (0, 0, 0, 0))
    md = ImageDraw.Draw(mlayer)
    c, r = 130 * k, 62 * k
    mc = AMBER if moon_on else tuple(int(x * 0.22) for x in AMBER)
    md.ellipse((c - r, c - r, c + r, c + r), fill=mc + (255,))
    md.ellipse((c - r + 30 * k, c - r - 16 * k, c + r + 30 * k, c + r - 16 * k), fill=(0, 0, 0, 0))
    if moon_on:
        mlayer = glow(mlayer, k, radii=(26, 8), strength=(0.9, 0.7))
    paste_px(cv.img, mlayer, 540 * k, 215 * k)
    tube("welcome to", "caveat:bold", 120, NEON_BLUE, 420, l1_on)
    tube("the night shift", "caveat:bold", 176, NEON_PINK, 610, l2_on)


def scene_3am(cv, t):
    k = cv.k
    # moon icon
    mlayer = Image.new("RGBA", (int(160 * k), int(160 * k)), (0, 0, 0, 0))
    md = ImageDraw.Draw(mlayer)
    c, r = 80 * k, 38 * k
    md.ellipse((c - r, c - r, c + r, c + r), fill=YELLOW + (255,))
    md.ellipse((c - r + 18 * k, c - r - 10 * k, c + r + 18 * k, c + r - 10 * k), fill=(0, 0, 0, 0))
    paste_px(cv.img, mlayer, 540 * k, 190 * k)
    # clock, colon blinks twice a second
    f = font("mono-x", 250 * k)
    fa = font("mono", 84 * k)
    colon = (int(t * 2) % 2) == 0
    layer = Image.new("RGBA", cv.img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    parts = ["3", ":" if colon else " ", "12"]
    total = f.getlength("3:12") + 24 * k + fa.getlength("AM")
    x = 540 * k - total / 2
    y = 420 * k
    for part in parts:
        ld.text((x, y), part, font=f, anchor="lm", fill=AMBER)
        x += f.getlength(part if part != " " else ":")
    ld.text((x + 24 * k, y + 52 * k), "AM", font=fa, anchor="lm", fill=AMBER)
    cv.img.alpha_composite(glow(layer, k, radii=(30, 10), strength=(0.75, 0.55)))
    l1 = text_layer("still up, reading comments.", font("caveat:bold", 74 * k), OFFWHITE)
    l2 = text_layer("thank you.", font("marker", 124 * k), YELLOW)
    paste_px(cv.img, reveal(l1, prog(t, 0.4, 1.4)), 540 * k, 650 * k)
    paste_px(cv.img, reveal(l2, prog(t, 1.6, 2.3)), 540 * k, 800 * k)


SCENES = {
    # name: (draw, seconds, sticker): sticker is False (none), True (plain
    # cut-out) or "diecut" (night-coloured outline so light text reads on any photo)
    "thank-you": (scene_thank_you, 3.6, True),
    "thank-you-human": (scene_thank_you_human, 4.6, True),
    "check-your-dms": (scene_check_dms, 4.4, False),
    "git-commit-thanks": (scene_git_commit, 4.0, True),
    "lgtm": (scene_lgtm, 3.4, "diecut"),
    "it-works": (scene_it_works, 3.6, True),
    "200-ok": (scene_200_ok, 3.6, False),
    "3am-thank-you": (scene_3am, 4.0, False),
    "ctrl-s-saved": (scene_saved, 3.4, "diecut"),
    "night-shift": (scene_night_shift, 4.0, False),
    "noted": (scene_noted, 3.4, True),
    "same": (scene_same, 3.0, True),
    "lol": (scene_lol, 3.6, True),
}


# ---------------------------------------------------------------- output
def render(name, t, size, background=True, mark=True):
    draw, _, _ = SCENES[name]
    cv = Canvas(size, background)
    draw(cv, t)
    if mark:
        watermark(cv)
    return cv.img


def make_still(name):
    _, dur, _ = SCENES[name]
    img = render(name, dur, PNG_SIZE * 2)
    img = img.resize((PNG_SIZE, PNG_SIZE), Image.LANCZOS).convert("RGB")
    out = os.path.join(HERE, "png", name + ".png")
    img.save(out, optimize=True)
    return out


def diecut(img, radius=30):
    """Put a rounded night-coloured backing under everything opaque in img."""
    k = img.width / 1080.0
    a = img.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    a = a.filter(ImageFilter.GaussianBlur(radius * k)).point(lambda v: 255 if v > 10 else 0)
    a = a.filter(ImageFilter.GaussianBlur(1.5 * k))
    back = Image.new("RGBA", img.size, NIGHT_TOP + (255,))
    back.putalpha(a)
    rim = Image.new("RGBA", img.size, (70, 80, 120, 255))
    rim.putalpha(a.filter(ImageFilter.MaxFilter(5)))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(rim)
    out.alpha_composite(back)
    out.alpha_composite(img)
    return out


def make_sticker(name):
    _, dur, kind = SCENES[name]
    img = render(name, dur, PNG_SIZE * 2, background=False, mark=False)
    if kind == "diecut":
        img = diecut(img)
    img = img.resize((PNG_SIZE, PNG_SIZE), Image.LANCZOS)
    bbox = img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    pad = 24
    img = img.crop((max(0, bbox[0] - pad), max(0, bbox[1] - pad),
                    min(PNG_SIZE, bbox[2] + pad), min(PNG_SIZE, bbox[3] + pad)))
    out = os.path.join(HERE, "stickers", name + ".png")
    img.save(out, optimize=True)
    return out


def make_gif(name):
    _, dur, _ = SCENES[name]
    n = int(round(dur * FPS))
    tmp = tempfile.mkdtemp(prefix="kit-")
    try:
        for i in range(n):
            t = i / FPS
            img = render(name, t, GIF_SIZE * 2)
            img = img.resize((GIF_SIZE, GIF_SIZE), Image.LANCZOS).convert("RGB")
            img.save(os.path.join(tmp, f"f{i:04d}.png"))
        out = os.path.join(HERE, "gif", name + ".gif")
        vf = ("split[a][b];[a]palettegen=max_colors=200:stats_mode=full[p];"
              "[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                        "-i", os.path.join(tmp, "f%04d.png"), "-vf", vf, "-loop", "0", out],
                       check=True)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def make_preview(names):
    cell, gap, label_h = 340, 24, 46
    cols = 4
    rows = math.ceil(len(names) / cols)
    W = cols * cell + (cols + 1) * gap
    H = rows * (cell + label_h) + (rows + 1) * gap + 90
    sheet = Image.new("RGB", (W, H), (12, 14, 26))
    d = ImageDraw.Draw(sheet)
    d.text((gap, 34), "almuri comment kit", font=font("marker", 46), fill=OFFWHITE, anchor="lm")
    d.text((W - gap, 34), "@heyalmuri", font=font("mono", 26), fill=DIM, anchor="rm")
    for i, name in enumerate(names):
        r, c = divmod(i, cols)
        x = gap + c * (cell + gap)
        y = 90 + gap + r * (cell + label_h + gap)
        im = Image.open(os.path.join(HERE, "png", name + ".png")).resize((cell, cell), Image.LANCZOS)
        sheet.paste(im, (x, y))
        d.text((x + cell / 2, y + cell + label_h / 2), name, font=font("mono", 22), fill=DIM, anchor="mm")
    out = os.path.join(HERE, "preview.png")
    sheet.save(out, optimize=True)
    return out


def main(argv):
    names = argv or list(SCENES)
    for bad in [n for n in names if n not in SCENES]:
        sys.exit(f"unknown reply '{bad}'. choose from: {', '.join(SCENES)}")
    for sub in ("png", "gif", "stickers"):
        os.makedirs(os.path.join(HERE, sub), exist_ok=True)
    for name in names:
        print("·", name)
        make_still(name)
        if SCENES[name][2]:
            make_sticker(name)
        make_gif(name)
    if not argv:
        make_preview(names)


if __name__ == "__main__":
    main(sys.argv[1:])
