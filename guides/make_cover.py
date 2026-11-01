"""Make a branded cover for a guide page (1500x600, Notion cover size).

Usage:
  python3 guides/make_cover.py --title "I asked for one line" \
      --pill "commit message, one line" --out guides/assets/cover-line.jpg \
      [--art guides/assets/lina-laptop.jpg] [--dot red|lime]

Keep the title short (about 22 characters fits on one line). The art is
any image from guides/assets/ or the almuri-media posts; it is placed on
the right with soft edges. Notion crops covers to a band around the
middle, so all text sits between y=150 and y=450.
"""
import argparse
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BG = (21, 17, 42)
GLOW = (75, 60, 140)
LIME = (163, 224, 71)
RED = (240, 90, 70)
LAV = (190, 182, 230)
WHITE = (255, 255, 255)
INK = (17, 19, 32)
W, H = 1500, 600
HERE = os.path.dirname(os.path.abspath(__file__))


def font(bold, size):
    candidates = (
        ["/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf", "/usr/share/fonts/opentype/inter/Inter-Bold.otf"]
        if bold
        else ["/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"]
    ) + ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def feather(img, r):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rectangle((r, r, img.width - r, img.height - r), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(r / 2))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--title", required=True)
    p.add_argument("--pill", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--art", default=os.path.join(HERE, "assets", "lina-laptop.jpg"))
    p.add_argument("--dot", choices=["red", "lime"], default="red")
    p.add_argument("--byline", default="Lina's Guides  ·  @heyalmuri")
    a = p.parse_args()

    img = Image.new("RGB", (W, H), BG)
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((800, 60, 1450, 540), fill=90)
    img.paste(Image.new("RGB", (W, H), GLOW), (0, 0), glow.filter(ImageFilter.GaussianBlur(140)))

    art = Image.open(a.art).convert("RGB")
    scale = min(560 / art.width, 330 / art.height)
    art = art.resize((int(art.width * scale), int(art.height * scale)), Image.LANCZOS)
    img.paste(art, (W - art.width - 70, (H - art.height) // 2), feather(art, 30))

    d = ImageDraw.Draw(img)
    size = 84
    while size > 48 and d.textlength(a.title, font=font(True, size)) > 800:
        size -= 4
    f = font(True, size)
    d.text((90, 175), a.title, font=f, fill=WHITE)
    tw = d.textlength(a.title, font=f)
    r = max(8, size // 9)
    cy = 175 + int(size * 0.8)
    d.ellipse((90 + tw + 5, cy - r, 90 + tw + 5 + 2 * r, cy + r), fill=RED if a.dot == "red" else LIME)

    pf = font(False, 28)
    pw = d.textlength(a.pill, font=pf)
    d.rounded_rectangle((92, 300, 92 + pw + 34, 348), radius=12, fill=LIME)
    d.text((109, 308), a.pill, font=pf, fill=INK)
    d.text((92, 385), a.byline, font=font(False, 26), fill=LAV)

    img.save(a.out, quality=88, optimize=True)
    print(a.out)


if __name__ == "__main__":
    main()
