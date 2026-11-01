#!/usr/bin/env python3
"""Almuri comment kit: reaction memes with Lina, claude and chatgpt.

Three formats, all square, all ending in the @heyalmuri footer with the
disclosure line:
  chat     a DM thread where claude or chatgpt answers the comment
  caption  the classic meme: white caption on top, the cast underneath
  card     the guide-cover look: navy, a cast cut-out, title with a red dot,
           lime pill

Every reply is rendered as png/<name>.png (1080) and gif/<name>.gif (540,
looping), plus preview.png.

Run:  python3 make_kit.py              (everything)
      python3 make_kit.py lina-real    (one or more by name)

Needs Pillow, numpy and ffmpeg, plus Inter and Noto Color Emoji (system fonts,
paths in FONTS). The cast images in cast/ come from guides/assets; the .png
cut-outs were made from them with rembg (isnet-general-use).
"""
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
CAST = os.path.join(HERE, "cast")
FPS = 20
GIF_SIZE = 540
PNG_SIZE = 1080
FOOTER_H = 70

# ---------------------------------------------------------------- palette
# Same as guides/make_cover.py, plus the cast colours.
BG = (21, 17, 42)
GLOW = (75, 60, 140)
LIME = (163, 224, 71)
RED = (240, 90, 70)
WHITE = (255, 255, 255)
INK = (17, 19, 32)
LILAC = (186, 176, 228)
CLAUDE_C = (232, 146, 116)
GPT_C = (110, 196, 164)

DISCLOSURE = "made with ai, parody characters, not affiliated with any ai company"

# ---------------------------------------------------------------- fonts
FONTS = {
    "title": "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
    "heavy": "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf",
    "semi": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
    "medium": "/usr/share/fonts/opentype/inter/Inter-Medium.otf",
    "italic": "/usr/share/fonts/opentype/inter/Inter-MediumItalic.otf",
    "emoji": "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
}
_fonts = {}


def font(key, size):
    size = max(1, int(round(size)))
    if key == "emoji":
        size = 109  # the only size the colour bitmaps come in
    if (key, size) not in _fonts:
        _fonts[(key, size)] = ImageFont.truetype(FONTS[key], size)
    return _fonts[(key, size)]


def is_emoji(ch):
    return ord(ch) >= 0x1F000 or 0x2600 <= ord(ch) <= 0x27BF


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return clamp((t - t0) / (t1 - t0))


def ease_out_cubic(p):
    return 1 - (1 - p) ** 3


def ease_in_out(p):
    return 0.5 - 0.5 * math.cos(math.pi * clamp(p))


def ease_out_back(p, s=1.7):
    p -= 1
    return p * p * ((s + 1) * p + s) + 1


def punch(t, tb, dur=0.35):
    """1 right at the beat, decaying to 0: drives zoom punches and shakes."""
    if t < tb or t > tb + dur:
        return 0.0
    return (1 - (t - tb) / dur) ** 2


# ---------------------------------------------------------------- canvas
class Canvas:
    """Square RGBA frame; every coordinate is on a 1080 grid, scaled by k."""

    def __init__(self, size):
        self.size = size
        self.k = size / 1080.0
        self.img = Image.new("RGBA", (size, size), BG + (255,))

    def u(self, v):
        return v * self.k

    def draw(self):
        return ImageDraw.Draw(self.img)

    def put(self, layer, cx, cy):
        """Composite a pixel-sized layer centred on grid point (cx, cy)."""
        if layer is None:
            return
        _composite(self.img, layer, int(round(cx * self.k - layer.width / 2)),
                   int(round(cy * self.k - layer.height / 2)))

    def put_tl(self, layer, x, y):
        if layer is None:
            return
        _composite(self.img, layer, int(round(x * self.k)), int(round(y * self.k)))


def _composite(base, layer, x, y):
    bx0, by0 = max(0, x), max(0, y)
    bx1, by1 = min(base.width, x + layer.width), min(base.height, y + layer.height)
    if bx1 <= bx0 or by1 <= by0:
        return
    base.alpha_composite(layer.crop((bx0 - x, by0 - y, bx1 - x, by1 - y)), dest=(bx0, by0))


_glow_cache = {}


def brand_bg(cv, cx=540, cy=560, color=GLOW, radius=620, strength=0.85):
    key = (cv.size, cx, cy, color, radius, strength)
    if key not in _glow_cache:
        n = cv.size
        ys, xs = np.mgrid[0:n, 0:n].astype(np.float32) / cv.k
        d = np.sqrt((xs - cx) ** 2 + (ys - cy) ** 2) / radius
        g = (np.clip(1 - d, 0, 1) ** 2 * strength)[..., None]
        rgb = np.array(BG, np.float32) * (1 - g) + np.array(color, np.float32) * g
        arr = np.dstack([rgb.astype(np.uint8), np.full((n, n), 255, np.uint8)])
        _glow_cache[key] = Image.fromarray(arr, "RGBA")
    cv.img.paste(_glow_cache[key])


def footer(cv):
    k = cv.k
    d = cv.draw()
    y0 = (1080 - FOOTER_H) * k
    d.rectangle((0, y0, cv.size, cv.size), fill=BG)
    d.line((0, y0, cv.size, y0), fill=(52, 44, 92), width=max(1, int(2 * k)))
    cy = y0 + FOOTER_H * k / 2
    d.text((40 * k, cy), "@heyalmuri", font=font("title", 30 * k), anchor="lm", fill=WHITE)
    d.text((cv.size - 40 * k, cy), DISCLOSURE, font=font("medium", 19 * k), anchor="rm", fill=LILAC)


# ---------------------------------------------------------------- assets
_assets = {}


def asset(name):
    if name not in _assets:
        _assets[name] = Image.open(os.path.join(CAST, name)).convert("RGBA")
    return _assets[name]


def scaled(img, scale):
    return img.resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))), Image.LANCZOS)


def with_alpha(layer, a):
    if a >= 1:
        return layer
    out = layer.copy()
    arr = np.asarray(out.getchannel("A"), dtype=np.float32) * clamp(a)
    out.putalpha(Image.fromarray(arr.astype(np.uint8), "L"))
    return out


def padded(layer, pad):
    out = Image.new("RGBA", (layer.width + 2 * pad, layer.height + 2 * pad), (0, 0, 0, 0))
    out.alpha_composite(layer, dest=(pad, pad))
    return out


def tinted_glow(layer, color, radius, alpha):
    """A soft coloured halo the shape of the layer (for auras and lift)."""
    pad = int(radius * 3)
    a = padded(layer, pad).getchannel("A").filter(ImageFilter.GaussianBlur(radius))
    arr = np.clip(np.asarray(a, dtype=np.float32) * alpha, 0, 255).astype(np.uint8)
    g = Image.new("RGBA", a.size, color + (0,))
    g.putalpha(Image.fromarray(arr, "L"))
    return g


def shadow(layer, k, blur=18, alpha=0.6):
    return tinted_glow(layer, (0, 0, 0), blur * k, alpha)


def place(cv, img, cx, bottom, height=None, width=None, scale=1.0, alpha=1.0, glow=None, shadow_on=True):
    """Put a cut-out with its feet at (cx, bottom). height/width in grid units."""
    k = cv.k
    if height:
        s = height * k / img.height
    else:
        s = width * k / img.width
    layer = scaled(img, s * scale)
    cy = bottom - layer.height / k / 2
    if glow:
        cv.put(tinted_glow(layer, glow[0], glow[1] * k, glow[2]), cx, cy)
    if shadow_on:
        cv.put(with_alpha(shadow(layer, k), alpha), cx + 8, cy + 14)
    cv.put(with_alpha(layer, alpha), cx, cy)
    return layer


# ---------------------------------------------------------------- text
def text_runs(text, size, fkey, fill):
    """One line of text with colour emoji mixed in, as a tight RGBA layer."""
    f = font(fkey, size)
    asc, desc = f.getmetrics()
    esize = int(size * 1.12)
    tokens, buf = [], ""
    for ch in text:
        if is_emoji(ch) or ch == "️":
            if buf:
                tokens.append(("t", buf))
                buf = ""
            if ch != "️":
                tokens.append(("e", ch))
        else:
            buf += ch
    if buf:
        tokens.append(("t", buf))
    widths = [f.getlength(s) if kind == "t" else esize + size * 0.08 for kind, s in tokens]
    W = int(sum(widths)) + 4
    H = asc + desc + 4
    img = Image.new("RGBA", (max(1, W), H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 0
    for (kind, s), w in zip(tokens, widths):
        if kind == "t":
            d.text((x, asc), s, font=f, anchor="ls", fill=fill)
        else:
            e = Image.new("RGBA", (140, 140), (0, 0, 0, 0))
            ImageDraw.Draw(e).text((6, 6), s, font=font("emoji", 109), embedded_color=True)
            e = e.crop(e.getbbox()).resize((esize, esize), Image.LANCZOS)
            img.alpha_composite(e, dest=(int(x + size * 0.04), max(0, int(asc - esize * 0.86))))
        x += w
    return img


def text_width(text, size, fkey):
    f = font(fkey, size)
    return sum(size * 1.2 if is_emoji(ch) else f.getlength(ch) for ch in text)


def wrap(text, size, fkey, max_w):
    lines, cur = [], ""
    for word in text.split(" "):
        trial = (cur + " " + word).strip()
        if cur and text_width(trial, size, fkey) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def typed(text, p):
    return text[: int(round(len(text) * clamp(p)))]


def tiktok_label(text, size, k):
    """White bold text with a heavy black outline: the meme-overlay look.
    Words are spaced by hand, since the outline eats the normal space."""
    f = font("heavy", size * k)
    stroke = max(2, int(size * k * 0.11))
    gap = size * k * 0.34
    words = text.split(" ")
    asc, desc = f.getmetrics()
    widths = [f.getlength(w) for w in words]
    W = int(sum(widths) + gap * (len(words) - 1) + 2 * stroke + 8)
    H = asc + desc + 2 * stroke + 8
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = stroke + 4
    for w, ww in zip(words, widths):
        d.text((x, stroke + 4 + asc), w, font=f, anchor="ls", fill=WHITE, stroke_width=stroke,
               stroke_fill=(0, 0, 0))
        x += ww + gap
    return img


def title_with_dot(cv, text, x, y, size, p=1.0, color=WHITE, align="left", fkey="title", dot=True):
    """Guide-cover title: white, with the red dot after the last letter."""
    k = cv.k
    shown = typed(text, p)
    f = font(fkey, size * k)
    full_w = f.getlength(text) + size * 0.3 * k
    if align == "center":
        x = 540 - full_w / k / 2
    d = cv.draw()
    if shown:
        d.text((x * k, y * k), shown, font=f, anchor="ls", fill=color)
    if p >= 1 and dot:
        r = size * 0.095 * k
        dx = x * k + f.getlength(text) + r * 1.4
        dy = y * k - r
        d.ellipse((dx - r, dy - r, dx + r, dy + r), fill=RED)


def pill(cv, text, x, y, size, p=1.0, align="left", fill=LIME, ink=INK):
    """Lime pill like the guide covers; (x, y) is its top-left (or top-centre)."""
    if p <= 0:
        return
    k = cv.k
    f = font("semi", size * k)
    tw = f.getlength(text)
    padx, h = size * 0.5 * k, size * 1.55 * k
    w = tw + 2 * padx
    layer = Image.new("RGBA", (int(w) + 2, int(h) + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((0, 0, w, h), radius=h * 0.32, fill=fill + (255,))
    d.text((w / 2, h / 2), text, font=f, anchor="mm", fill=ink)
    s = ease_out_back(clamp(p))
    layer = scaled(layer, max(0.01, s))
    cx = (x * k + w / 2) / k if align == "left" else x
    cv.put(with_alpha(layer, clamp(p * 3)), cx, y + h / k / 2)


# ---------------------------------------------------------------- shapes
def sparkle(d, cx, cy, r, color):
    """Four-point twinkle star."""
    w = r * 0.22
    d.polygon([(cx, cy - r), (cx + w, cy - w), (cx + r, cy), (cx + w, cy + w), (cx, cy + r),
               (cx - w, cy + w), (cx - r, cy), (cx - w, cy - w)], fill=color)


def confetti(cv, t, t0, n=60, seed=7, colors=(LIME, RED, WHITE, LILAC, GPT_C)):
    if t < t0:
        return
    rng = np.random.default_rng(seed)
    d = cv.draw()
    k = cv.k
    for i in range(n):
        x0 = rng.uniform(40, 1040)
        vy = rng.uniform(260, 520)
        delay = rng.uniform(0, 0.8)
        spin = rng.uniform(4, 10)
        sway = rng.uniform(20, 60)
        col = colors[i % len(colors)]
        tt = t - t0 - delay
        if tt < 0:
            continue
        y = -40 + vy * tt
        if y > 1010:
            continue
        x = x0 + math.sin(tt * 3 + i) * sway
        a = tt * spin + i
        w, h = 18, 9 + 7 * abs(math.sin(a))
        ca, sa = math.cos(a), math.sin(a)
        pts = [(x + (px * ca - py * sa), y + (px * sa + py * ca)) for px, py in
               ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        d.polygon([(px * k, py * k) for px, py in pts], fill=col)


def faded_bottom(img, frac):
    """Fade the lowest `frac` of a cut-out to transparent (no hard neck line)."""
    a = np.asarray(img.getchannel("A"), dtype=np.float32)
    h = a.shape[0]
    ramp = np.clip((h - np.arange(h)) / (h * frac), 0, 1) ** 1.5
    out = img.copy()
    out.putalpha(Image.fromarray((a * ramp[:, None]).astype(np.uint8), "L"))
    return out


def circle_crop(img, size):
    img = img.resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    img.putalpha(m.resize((size, size), Image.LANCZOS))
    return img


# ================================================================ formats
# ---------------------------------------------------------------- chat
def chat(cv, t, who, msgs, reply_hint):
    """A DM thread. who: (name, face file, bubble colour, status).
    msgs: list of (kind, payload, t_appear, typing_seconds)."""
    k = cv.k
    name, face, color, status = who
    brand_bg(cv, 540, 300, GLOW, 760, 0.55)
    d = cv.draw()
    # header
    av = circle_crop(asset(face), int(124 * k))
    ring = Image.new("RGBA", (av.width + int(10 * k), av.height + int(10 * k)), (0, 0, 0, 0))
    ImageDraw.Draw(ring).ellipse((0, 0, ring.width - 1, ring.height - 1), fill=color + (255,))
    cv.put(ring, 140, 140)
    cv.put(av, 140, 140)
    typing_now = any(ta - ty <= t < ta for _, _, ta, ty in msgs if ty)
    d.text((234 * k, 128 * k), name, font=font("title", 58 * k), anchor="ls", fill=WHITE)
    d.text((236 * k, 180 * k), "typing…" if typing_now else status, font=font("medium", 32 * k),
           anchor="ls", fill=color if typing_now else LILAC)
    d.line((60 * k, 232 * k, 1020 * k, 232 * k), fill=(70, 60, 120), width=max(1, int(2 * k)))
    # composer
    d.rounded_rectangle((60 * k, 912 * k, 1020 * k, 982 * k), radius=35 * k, outline=(92, 82, 150),
                        width=max(1, int(3 * k)))
    d.text((100 * k, 947 * k), reply_hint, font=font("medium", 30 * k), anchor="lm", fill=(130, 120, 180))
    # bubbles, laid out top-down at fixed positions
    y = 272
    for kind, payload, ta, ty in msgs:
        layer, h = build_msg(kind, payload, color, k)
        if ty and ta - ty <= t < ta:
            typing_bubble(cv, t, 60, y, color)
        if t >= ta:
            p = prog(t, ta, ta + 0.22)
            s = 0.8 + 0.2 * ease_out_back(p, 2.2)
            lay = scaled(layer, s)
            x_left = 60 if kind != "note" else 86
            cv.put(with_alpha(lay, clamp(p * 3)), x_left + layer.width / k / 2, y + h / 2)
        y += h + (18 if kind == "note" else 24)


def build_msg(kind, payload, color, k):
    if kind == "note":
        img = text_runs(payload, 42 * k, "italic", LILAC + (255,))
        return img, img.height / k
    if kind == "table":
        rows = payload
        fs = 50
        c1 = max(text_width(a, fs, "semi") for a, _ in rows) + 64
        c2 = max(text_width(b, fs, "semi") for _, b in rows) + 64
        rh = 84
        W, H = (c1 + c2 + 40) * k, (rh * len(rows) + 40) * k
        img = Image.new("RGBA", (int(W), int(H)), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, W - 1, H - 1), radius=40 * k, fill=color + (255,))
        tx = 20 * k
        d.rounded_rectangle((tx, 20 * k, W - tx, H - 20 * k), radius=18 * k, fill=(255, 255, 255, 235))
        for i, (a, b) in enumerate(rows):
            yy = (20 + rh * i + rh / 2) * k
            if i:
                d.line((tx, (20 + rh * i) * k, W - tx, (20 + rh * i) * k), fill=(210, 210, 220), width=max(1, int(2 * k)))
            d.text((tx + 30 * k, yy), a, font=font("semi", fs * k), anchor="lm", fill=INK)
            d.text((tx + (c1 + 10) * k, yy), b, font=font("semi", fs * k), anchor="lm", fill=(40, 120, 90))
        d.line((tx + c1 * k - 10 * k, 20 * k, tx + c1 * k - 10 * k, H - 20 * k), fill=(210, 210, 220), width=max(1, int(2 * k)))
        return img, H / k
    # bubble
    fs, lh = 62, 80
    lines = wrap(payload, fs, "medium", 880)
    layers = [text_runs(ln, fs * k, "medium", INK + (255,)) for ln in lines]
    tw = max(l.width for l in layers) / k
    W, H = (tw + 80) * k, (len(lines) * lh + 52) * k
    img = Image.new("RGBA", (int(W), int(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=min(44 * k, H / 2), fill=color + (255,))
    for i, l in enumerate(layers):
        img.alpha_composite(l, dest=(int(40 * k), int((26 + i * lh + (lh - l.height / k) / 2) * k)))
    return img, H / k


def typing_bubble(cv, t, x, y, color):
    k = cv.k
    d = cv.draw()
    d.rounded_rectangle((x * k, y * k, (x + 170) * k, (y + 132) * k), radius=60 * k, fill=color)
    for i in range(3):
        bob = math.sin(t * 12 - i * 0.9) * 8
        cx, cy, r = (x + 48 + i * 37) * k, (y + 66 - max(0, bob)) * k, 12 * k
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=INK + (200,))


# ---------------------------------------------------------------- caption meme
def caption_meme(cv, t, caption, img_name, focus, zoom, overlay=None, overlay_t=99, pan=None,
                 beat=None, chip=None):
    """White caption band on top, the image underneath, slow zoom (and an
    optional zoom punch at `beat`)."""
    k = cv.k
    fs, lh, pad = 56, 72, 46
    lines = wrap(caption, fs, "medium", 1080 - 2 * pad)
    band = pad * 2 + lh * len(lines) - 10
    d = cv.draw()
    d.rectangle((0, 0, cv.size, band * k), fill=WHITE)
    for i, ln in enumerate(lines):
        cv.put_tl(text_runs(ln, fs * k, "medium", INK + (255,)), pad, pad - 6 + i * lh)
    top, bot = band, 1080 - FOOTER_H
    pw, ph = 1080, bot - top
    src = asset(img_name)
    z = zoom(t)
    shake = (0, 0)
    if beat is not None:
        q = punch(t, beat)
        z *= 1 + 0.14 * q
        shake = (math.sin(t * 90) * 10 * q, math.cos(t * 70) * 8 * q)
    aspect = pw / ph
    cw = min(src.width, src.height * aspect) / z
    ch = cw / aspect
    fx, fy = focus if pan is None else pan(t)
    cx = clamp(fx * src.width, cw / 2, src.width - cw / 2)
    cy = clamp(fy * src.height, ch / 2, src.height - ch / 2)
    cx += shake[0] * cw / pw
    cy += shake[1] * ch / ph
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    panel = src.convert("RGB").resize((int(pw * k), int(ph * k)), Image.LANCZOS, box=box)
    cv.img.paste(panel, (0, int(top * k)))
    if beat is not None and punch(t, beat) > 0:
        flash = Image.new("RGBA", panel.size, (255, 255, 255, int(110 * punch(t, beat, 0.2))))
        cv.img.alpha_composite(flash, dest=(0, int(top * k)))
    if chip and t >= chip[1]:
        p = prog(t, chip[1], chip[1] + 0.25)
        lay = text_runs(chip[0], 34 * k, "semi", WHITE + (255,))
        bg = Image.new("RGBA", (lay.width + int(40 * k), lay.height + int(22 * k)), (0, 0, 0, 0))
        ImageDraw.Draw(bg).rounded_rectangle((0, 0, bg.width - 1, bg.height - 1), radius=bg.height / 2,
                                             fill=(0, 0, 0, 150))
        bg.alpha_composite(lay, dest=(int(20 * k), int(11 * k)))
        cv.put(with_alpha(scaled(bg, 0.6 + 0.4 * ease_out_back(p)), clamp(p * 3)), 50 + bg.width / k / 2,
               bot - 50)
    if overlay and t >= overlay_t:
        p = prog(t, overlay_t, overlay_t + 0.25)
        lab = tiktok_label(overlay, 58, k)
        cv.put(with_alpha(scaled(lab, 0.6 + 0.4 * ease_out_back(p, 2.4)), clamp(p * 3)), 540, bot - 74)


# ================================================================ replies
def r_claude_short_version(cv, t):
    chat(cv, t, ("claude", "face-claude.jpg", CLAUDE_C, "parody ai · online at 3am"), [
        ("bubble", "sorry. short version:", 0.55, 0.45),
        ("bubble", "thank you 🫶", 1.6, 0.6),
        ("note", "(page 1 of 4)", 2.5, 0),
    ], "reply to claude…")


def r_claude_absolutely_right(cv, t):
    chat(cv, t, ("claude", "face-claude.jpg", CLAUDE_C, "parody ai · online at 3am"), [
        ("bubble", "you're absolutely right!", 0.5, 0.4),
        ("bubble", "you're absolutely right!!", 1.25, 0.35),
        ("bubble", "genuinely the best point ever made", 2.05, 0.4),
        ("note", "(he has not opened your comment)", 3.0, 0),
    ], "reply to claude…")


def r_claude_apology(cv, t):
    chat(cv, t, ("claude", "face-claude.jpg", CLAUDE_C, "parody ai · online at 3am"), [
        ("bubble", "you caught that. i sincerely apologize for the confusion", 0.5, 0.45),
        ("bubble", "here's the corrected version:", 1.55, 0.45),
        ("note", "(it's the exact same version)", 2.55, 0),
    ], "reply to claude…")


def r_chatgpt_glazing(cv, t):
    chat(cv, t, ("chatgpt", "face-chatgpt.jpg", GPT_C, "parody ai · online, always"), [
        ("bubble", "WOW. what a comment 🤩", 0.5, 0.4),
        ("table", [("humor", "10/10"), ("timing", "immaculate"), ("aura", "infinite")], 1.35, 0.4),
        ("bubble", "want a pie chart too?", 2.5, 0.45),
    ], "reply to chatgpt…")


def r_lina_laughing(cv, t):
    caption_meme(cv, t, "no bc lina actually laughed out loud at your comment", "face-lina.jpg",
                 (0.5, 0.56), lambda t: 1.0 + 0.16 * ease_in_out(prog(t, 0, 3.2)),
                 overlay="(this is her laughing)", overlay_t=1.6)


def r_claude_funnier(cv, t):
    caption_meme(cv, t, "claude realizing your comment is funnier than his whole 4 page answer",
                 "face-claude.jpg", (0.52, 0.5), lambda t: 1.0 + 0.10 * ease_in_out(prog(t, 0, 3.2)),
                 overlay="(writing page 5 to cope)", overlay_t=1.9, beat=1.3)


def r_cast_dms(cv, t):
    def pan(t):
        p = ease_in_out(prog(t, 0.2, 2.6))
        return (0.18 + 0.66 * p, 0.42)

    caption_meme(cv, t, "us sliding into your DMs after you comment the keyword", "scene-cast-top.jpg",
                 None, lambda t: 1.0, overlay="(it's literally just the file)", overlay_t=2.8, pan=pan)


def r_pov_night_shift(cv, t):
    caption_meme(cv, t, "pov: you followed and now you're on lina's night shift", "scene-lina-desk.jpg",
                 (0.42, 0.45), lambda t: 1.0 + 0.18 * ease_in_out(prog(t, 0, 3.4)), chip=("☕ 2:14 am", 0.9))


def r_lina_fine(cv, t):
    caption_meme(cv, t, "lina acting like your comment didn't make her emotional at 3am", "lina-laptop.jpg",
                 (0.45, 0.36), lambda t: 1.15 + 0.3 * ease_in_out(prog(t, 0, 3.4)),
                 overlay="she's fine (she is not fine)", overlay_t=1.7)


def r_lina_check_dms(cv, t):
    k = cv.k
    brand_bg(cv, 760, 640, GLOW, 640, 0.9)
    p = ease_out_cubic(prog(t, 0.0, 0.55))
    place(cv, asset("lina-laptop.png"), 770, 1010 + (1 - p) * 520, height=640)
    # DM notification pops above her laptop
    bp = prog(t, 0.75, 1.05)
    if bp > 0:
        bob = math.sin(max(0, t - 1.05) * 4) * 6
        s = ease_out_back(bp, 2.0)
        r = 74
        big = int(2 * (r + 30) * k * 2)
        ic = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        d = ImageDraw.Draw(ic)
        c, rr = big / 2, r * k * 2
        d.ellipse((c - rr, c - rr, c + rr, c + rr), fill=LIME + (255,))
        u = rr / 70
        d.polygon([(c - 40 * u, c + 2 * u), (c + 44 * u, c - 36 * u), (c + 8 * u, c + 44 * u),
                   (c - 2 * u, c + 12 * u)], fill=INK + (255,))
        d.line([(c - 2 * u, c + 12 * u), (c + 44 * u, c - 36 * u)], fill=LIME + (255,), width=int(5 * u))
        br = 30 * u
        bx, by = c + rr * 0.72, c - rr * 0.72
        d.ellipse((bx - br - 5 * u, by - br - 5 * u, bx + br + 5 * u, by + br + 5 * u), fill=BG + (255,))
        d.ellipse((bx - br, by - br, bx + br, by + br), fill=RED + (255,))
        d.text((bx, by + 1 * u), "1", font=font("title", 38 * u), anchor="mm", fill=WHITE)
        ic = scaled(ic, 0.5 * s)
        cv.put(shadow(ic, k, 14, 0.5), 958, 300 + bob + 12)
        cv.put(ic, 950, 290 + bob)
    title_with_dot(cv, "check your DMs", 64, 196, 104, prog(t, 0.95, 1.55))
    pill(cv, "lina sent it at 3am", 66, 252, 44, prog(t, 1.7, 1.95))
    a = int(255 * prog(t, 2.2, 2.5))
    if a:
        d = cv.draw()
        d.text((68 * k, 392 * k), "not following yet?", font=font("semi", 34 * k), anchor="ls", fill=LILAC + (a,))
        d.text((68 * k, 438 * k), "check your message requests", font=font("medium", 34 * k), anchor="ls",
               fill=LILAC + (a,))


def r_aura(cv, t):
    k = cv.k
    on = ease_out_cubic(prog(t, 0.35, 1.2))
    pulse = 0.75 + 0.25 * math.sin(t * 6)
    brand_bg(cv, 540, 620, (72, 96, 40), 560, 0.9 * on)
    lina = asset("lina-standing.png")
    p = ease_out_back(prog(t, 0.0, 0.45), 1.4)
    if p > 0:
        layer = scaled(lina, 740 * k / lina.height)
        cy = 1000 - layer.height / k / 2
        if on > 0:
            cv.put(tinted_glow(layer, LIME, 34 * k, 2.4 * on * pulse), 540, cy)
            cv.put(tinted_glow(layer, (230, 255, 170), 9 * k, 2.2 * on), 540, cy)
        cv.put(with_alpha(layer, clamp(p * 2)), 540, cy + (1 - p) * 60)
    # sparkles
    rng = np.random.default_rng(3)
    d = cv.draw()
    for i in range(14):
        x, y = rng.uniform(140, 940), rng.uniform(300, 960)
        if 400 < x < 680 and y > 320:
            x += 300 if x > 540 else -300
        ph = rng.uniform(0, 6.28)
        s = max(0.0, math.sin(t * 5 + ph)) * on
        if s > 0.05:
            sparkle(d, x * k, y * k, (10 + 18 * s) * k, (235, 255, 190, int(255 * s)))
    pill(cv, "this comment:", 540, 50, 40, prog(t, 0.3, 0.55), align="center")
    n = int(ease_out_cubic(prog(t, 0.6, 1.7)) * 1000 / 10) * 10
    if t >= 0.6:
        q = punch(t, 1.7, 0.3)
        lab = text_runs(f"+{n} aura", 132 * k, "heavy", WHITE + (255,))
        lab = scaled(lab, 1 + 0.18 * q)
        if n >= 1000:
            cv.put(tinted_glow(lab, LIME, 16 * k, 1.4), 540, 210)
        cv.put(lab, 540, 210)


def r_number_one_fan(cv, t):
    k = cv.k
    brand_bg(cv, 540, 660, (40, 96, 80), 620, 0.8)
    confetti(cv, t, 0.55)
    g = asset("chatgpt.png")
    p = ease_out_back(prog(t, 0.0, 0.5), 1.5)
    if p > 0:
        beat = (t - 0.6) % 0.5 if t > 0.6 else 1
        sq = 0.06 * max(0, 1 - beat / 0.18) if t > 0.6 else 0
        layer = scaled(g, 640 * k / g.width)
        layer = layer.resize((int(layer.width * (1 + sq)), int(layer.height * (1 - sq))), Image.LANCZOS)
        bottom = 960 + (1 - p) * 600
        cy = bottom - layer.height / k / 2
        cv.put(shadow(layer, k, 20, 0.6), 548, cy + 16)
        cv.put(layer, 540, cy)
    title_with_dot(cv, "#1 commenter", 0, 200, 124, prog(t, 0.55, 1.1), align="center")
    pill(cv, "chatgpt is your biggest fan now", 540, 250, 42, prog(t, 1.25, 1.5), align="center")


def r_lina_real(cv, t):
    k = cv.k
    brand_bg(cv, 540, 480, GLOW, 600, 0.9)
    q = punch(t, 0.55, 0.4)
    head = faded_bottom(asset("lina-head.png"), 0.26)
    layer = scaled(head, 560 * k / head.height * (1 + 0.1 * q))
    sx, sy = math.sin(t * 95) * 12 * q, math.cos(t * 80) * 9 * q
    cv.put(shadow(layer, k, 24, 0.55), 548 + sx, 500 + sy + 14)
    cv.put(layer, 540 + sx, 500 + sy)
    if t >= 0.55:
        p = prog(t, 0.55, 0.75)
        lab = text_runs("real", 230 * k, "heavy", WHITE + (255,))
        f = font("heavy", 230 * k)
        r = 230 * 0.095 * k
        dotw = int(r * 3.2)
        full = Image.new("RGBA", (lab.width + dotw, lab.height), (0, 0, 0, 0))
        full.alpha_composite(lab)
        asc = f.getmetrics()[0]
        ImageDraw.Draw(full).ellipse((lab.width + r * 0.6, asc - 2 * r, lab.width + r * 2.6, asc), fill=RED)
        s = 1.8 - 0.8 * ease_out_cubic(p)
        cv.put(shadow(full, k, 16, 0.7), 546, 880)
        cv.put(with_alpha(scaled(full, s), clamp(p * 3)), 540, 874)
    if q > 0:
        cv.img.alpha_composite(Image.new("RGBA", cv.img.size, (255, 255, 255, int(90 * punch(t, 0.55, 0.2)))))
    pill(cv, "lina doesn't say that often", 540, 70, 40, prog(t, 1.3, 1.55), align="center")


def r_cast_reacting(cv, t):
    k = cv.k
    brand_bg(cv, 640, 760, (60, 92, 44), 640, 0.75)
    title_with_dot(cv, "the cast read", 0, 118, 86, prog(t, 0.0, 0.45), align="center", dot=False)
    if t >= 0.45:
        title_with_dot(cv, "your comment", 0, 216, 86, prog(t, 0.45, 0.9), align="center")
    # (image, centre x, width, line, time it speaks, bubble colour, bubble bottom y)
    cast = [
        ("lina-laptop.png", 240, 430, "ok that's actually funny", 1.2, WHITE, 515, 380),
        ("claude.png", 640, 300, "sorry. agreed", 2.0, CLAUDE_C, 745, 300),
        ("chatgpt.png", 912, 296, "10/10 want a table?", 2.8, GPT_C, 650, 240),
    ]
    for img, cx, w, line, tb, col, _, _ in cast:
        hop = math.sin(clamp((t - tb) / 0.3) * math.pi) * 28 if tb <= t <= tb + 0.3 else 0
        place(cv, asset(img), cx, 1000 - hop, width=w)
    for img, cx, w, line, tb, col, by, wrap_w in cast:
        if t < tb:
            continue
        p = prog(t, tb, tb + 0.22)
        lines = wrap(line, 44, "semi", wrap_w)
        lays = [text_runs(ln, 44 * k, "semi", INK + (255,)) for ln in lines]
        bw = max(l.width for l in lays) + int(48 * k)
        bh = sum(l.height for l in lays) + int(34 * k)
        tail = int(24 * k)
        b = Image.new("RGBA", (bw, bh + tail), (0, 0, 0, 0))
        d = ImageDraw.Draw(b)
        d.rounded_rectangle((0, 0, bw - 1, bh - 1), radius=24 * k, fill=col + (255,))
        d.polygon([(bw / 2 - tail, bh - 2), (bw / 2 + tail, bh - 2), (bw / 2, bh + tail)], fill=col + (255,))
        y = int(17 * k)
        for l in lays:
            b.alpha_composite(l, dest=((bw - l.width) // 2, y))
            y += l.height
        cxb = min(max(cx, bw / k / 2 + 14), 1080 - bw / k / 2 - 14)
        cv.put(with_alpha(scaled(b, 0.6 + 0.4 * ease_out_back(p, 2.2)), clamp(p * 3)), cxb,
               by - (bh + tail) / k / 2)


REPLIES = {
    # name: (draw, seconds, when to use it)
    "claude-short-version": (r_claude_short_version, 4.2, "any nice comment"),
    "chatgpt-glazing": (r_chatgpt_glazing, 4.4, "compliments"),
    "lina-check-dms": (r_lina_check_dms, 3.8, "someone commented the keyword"),
    "cast-dms": (r_cast_dms, 4.4, "someone commented the keyword"),
    "lina-laughing": (r_lina_laughing, 3.6, "a funny comment"),
    "claude-funnier": (r_claude_funnier, 3.8, "a funny comment"),
    "claude-absolutely-right": (r_claude_absolutely_right, 4.6, "someone makes a point"),
    "claude-apology": (r_claude_apology, 4.0, "someone spots a mistake"),
    "aura": (r_aura, 3.6, "the best comment under the post"),
    "number-one-fan": (r_number_one_fan, 3.6, "a regular, or a big supporter"),
    "lina-real": (r_lina_real, 3.0, "a relatable comment"),
    "lina-fine": (r_lina_fine, 3.8, "a wholesome comment"),
    "cast-reacting": (r_cast_reacting, 4.2, "anything, the all-rounder"),
    "pov-night-shift": (r_pov_night_shift, 3.6, "a first comment or a new follower"),
}


# ---------------------------------------------------------------- output
def prepare_assets():
    """Derived source: the cast scene without its baked-in footer text."""
    out = os.path.join(CAST, "scene-cast-top.jpg")
    if not os.path.exists(out):
        Image.open(os.path.join(CAST, "scene-cast.jpg")).crop((0, 0, 1200, 430)).save(out, quality=95)


def render(name, t, size):
    draw = REPLIES[name][0]
    cv = Canvas(size)
    draw(cv, t)
    footer(cv)
    return cv.img


def make_still(name):
    dur = REPLIES[name][1]
    img = render(name, dur, PNG_SIZE * 2).resize((PNG_SIZE, PNG_SIZE), Image.LANCZOS)
    out = os.path.join(HERE, "png", name + ".png")
    img.convert("RGB").save(out, optimize=True)
    return out


def make_gif(name):
    dur = REPLIES[name][1]
    n = int(round(dur * FPS))
    tmp = tempfile.mkdtemp(prefix="kit-")
    try:
        for i in range(n):
            img = render(name, i / FPS, GIF_SIZE * 2)
            img.resize((GIF_SIZE, GIF_SIZE), Image.LANCZOS).convert("RGB").save(os.path.join(tmp, f"f{i:04d}.png"))
        out = os.path.join(HERE, "gif", name + ".gif")
        vf = ("split[a][b];[a]palettegen=max_colors=256:stats_mode=full[p];"
              "[b][p]paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i",
                        os.path.join(tmp, "f%04d.png"), "-vf", vf, "-loop", "0", out], check=True)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def make_preview(names):
    cell, gap, label_h, cols = 340, 22, 50, 4
    rows = math.ceil(len(names) / cols)
    W = cols * cell + (cols + 1) * gap
    H = rows * (cell + label_h) + (rows + 1) * gap + 96
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((gap, 50), "almuri comment kit", font=font("title", 46), fill=WHITE, anchor="lm")
    d.ellipse((gap + font("title", 46).getlength("almuri comment kit") + 6, 56, gap + font("title", 46).getlength(
        "almuri comment kit") + 18, 68), fill=RED)
    d.text((W - gap, 50), "@heyalmuri", font=font("semi", 26), fill=LILAC, anchor="rm")
    for i, name in enumerate(names):
        r, c = divmod(i, cols)
        x = gap + c * (cell + gap)
        y = 96 + gap + r * (cell + label_h + gap)
        sheet.paste(Image.open(os.path.join(HERE, "png", name + ".png")).resize((cell, cell), Image.LANCZOS), (x, y))
        d.text((x + cell / 2, y + cell + label_h / 2), name, font=font("semi", 22), fill=LILAC, anchor="mm")
    sheet.save(os.path.join(HERE, "preview.png"), optimize=True)


def main(argv):
    names = argv or list(REPLIES)
    for bad in [n for n in names if n not in REPLIES]:
        sys.exit(f"unknown reply '{bad}'. choose from: {', '.join(REPLIES)}")
    prepare_assets()
    for sub in ("png", "gif"):
        os.makedirs(os.path.join(HERE, sub), exist_ok=True)
    for name in names:
        print("·", name)
        make_still(name)
        make_gif(name)
    if not argv:
        make_preview(names)


if __name__ == "__main__":
    main(sys.argv[1:])
