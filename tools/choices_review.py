"""Review sheet for the user's choices: original | your image | result now (after build + catalogue refresh).
Writes catalogue/choices/review_N.png
"""
import csv
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = os.path.join(ROOT, "catalogue")
CH = os.path.join(CAT, "choices")


def main():
    rows = list(csv.DictReader(open(os.path.join(CH, "choices.csv"), encoding="utf-8-sig")))
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 15)
    small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
    T, per, cols = 200, 16, 2
    for p in range(0, len(rows), per):
        chunk = rows[p:p + per]
        sheet = Image.new("RGB", (cols * (3 * T + 40), -(-len(chunk) // cols) * (T + 46)), (36, 36, 38))
        d = ImageDraw.Draw(sheet)
        for k, r in enumerate(chunk):
            x, y = (k % cols) * (3 * T + 40) + 10, (k // cols) * (T + 46) + 6
            i = r["id"]
            imgs = [os.path.join(CAT, "img", f"{i}.webp"),
                    os.path.join(CH, f"{i}_custom.png") if r["custom_image"] else None,
                    os.path.join(CAT, "img", f"{i}_now.webp")]
            for j, f in enumerate(imgs):
                if f and os.path.exists(f):
                    im = Image.open(f).convert("RGBA")
                    bg = Image.new("RGBA", im.size, (90, 90, 90, 255))
                    bg.alpha_composite(im)
                    im = bg.convert("RGB")
                    im.thumbnail((T - 8, T - 8))
                    sheet.paste(im, (x + j * T + (T - 8 - im.width) // 2, y + 20 + (T - 8 - im.height) // 2))
                elif j == 2:
                    d.text((x + j * T + 10, y + 90), "original (unchanged)", fill=(180, 180, 180), font=small)
            d.text((x, y), f"{i}  {r['original_sign'][:28]}  ->  {r['your_choice']}", fill=(255, 220, 80), font=font)
            d.text((x, y + T + 14), "original            your image            result", fill=(150, 150, 150), font=small)
        sheet.save(os.path.join(CH, f"review_{p // per + 1}.png"))
    print("done")


if __name__ == "__main__":
    main()
