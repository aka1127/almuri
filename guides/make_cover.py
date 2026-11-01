"""Make a branded cover for a guide page (1500x600, Notion cover size).

Usage:
  python3 guides/make_cover.py --title "I asked for one line" \
      --pill "the 3 prompts" --out guides/assets/cover-line.jpg \
      [--art guides/assets/lina-laptop.jpg] [--dot red|lime] [--preview]

Notion crops covers differently on desktop, on phones and in link
previews (the Instagram DM shows the cover as the preview). Everything
important stays inside the safe zone x 280-1220, y 160-440, which
survives all three. --preview writes <out>-preview.jpg with the three
crops side by side: look at it before using the cover.

Keep the title short (about 20 characters) and the pill to a few words.
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BG = (21, 17, 42)
GLOW = (75, 60, 140)
LIME = (163, 224, 71)
RED = (240, 90, 70)
WHITE = (255, 255, 255)
INK = (17, 19, 32)
W, H = 1500, 600
SAFE = (280, 160, 1220, 440)
HERE = os.path.dirname(os.path.abspath(__file__))

# (name, box) for --preview: desktop band, phone crop, link preview 1.91:1
CROPS = [
    ("desktop", (0, 159, 1500, 440)),
    ("phone", (282, 0, 1218, 600)),
    ("link preview", (177, 0, 1323, 600)),
]


def font(bold, size):
    candidates = (
        ["/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", "/usr/share/fonts/opentype/inter/Inter-Bold.otf"]
        if bold
        else ["/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", "/usr/share/fonts/opentype/inter/Inter-Bold.otf"]
    ) + ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def oval_mask(size):
    w, h = size
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).ellipse((w * 0.06, h * 0.04, w * 0.94, h * 0.98), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(min(w, h) / 12))


def make(title, pill, art_path, dot):
    img = Image.new("RGB", (W, H), BG)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((820, 120, 1300, 500), fill=110)
    img.paste(Image.new("RGB", (W, H), GLOW), (0, 0), glow.filter(ImageFilter.GaussianBlur(110)))

    d = ImageDraw.Draw(img)
    left = SAFE[0] + 10
    size = 72
    while size > 52 and d.textlength(title, font=font(True, size)) > 560:
        size -= 2
    f = font(True, size)
    pf = font(False, 40)
    text_right = left + max(d.textlength(title, font=f) + 30, d.textlength(pill, font=pf) + 40)

    # Art fills the space right of the text, up to 280 px tall.
    art = Image.open(art_path).convert("RGB")
    max_w = max(330, SAFE[2] - 10 - int(text_right) - 40)
    scale = min(max_w / art.width, 280 / art.height)
    art = art.resize((int(art.width * scale), int(art.height * scale)), Image.LANCZOS)
    x = SAFE[2] - 10 - art.width
    y = 300 - art.height // 2
    img.paste(art, (x, y), oval_mask(art.size))
    d = ImageDraw.Draw(img)
    ty = 190
    d.text((left, ty), title, font=f, fill=WHITE)
    tw = d.textlength(title, font=f)
    r = max(7, size // 9)
    cy = ty + int(size * 0.8)
    d.ellipse((left + tw + 4, cy - r, left + tw + 4 + 2 * r, cy + r), fill=RED if dot == "red" else LIME)

    pw = d.textlength(pill, font=pf)
    py = ty + size + 30
    d.rounded_rectangle((left, py, left + pw + 40, py + 62), radius=14, fill=LIME)
    d.text((left + 20, py + 9), pill, font=pf, fill=INK)
    return img


def preview(img, out):
    tiles = []
    for name, box in CROPS:
        t = img.crop(box)
        t.thumbnail((700, 300))
        canvas = Image.new("RGB", (t.width, t.height + 30), "white")
        canvas.paste(t, (0, 30))
        ImageDraw.Draw(canvas).text((6, 6), name, fill="black", font=font(False, 18))
        tiles.append(canvas)
    sheet = Image.new("RGB", (sum(t.width for t in tiles) + 20 * len(tiles), max(t.height for t in tiles)), "white")
    x = 0
    for t in tiles:
        sheet.paste(t, (x, 0))
        x += t.width + 20
    path = os.path.splitext(out)[0] + "-preview.jpg"
    sheet.save(path, quality=85)
    return path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--title", required=True)
    p.add_argument("--pill", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--art", default=os.path.join(HERE, "assets", "lina-laptop.jpg"))
    p.add_argument("--dot", choices=["red", "lime"], default="red")
    p.add_argument("--preview", action="store_true")
    a = p.parse_args()

    img = make(a.title, a.pill, a.art, a.dot)
    img.save(a.out, quality=88, optimize=True)
    print(a.out)
    if a.preview:
        print(preview(img, a.out))


if __name__ == "__main__":
    main()
