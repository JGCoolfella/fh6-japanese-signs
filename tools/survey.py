"""Contact sheets of every extracted colour texture that has NOT been modded yet.

Usage: python tools/survey.py [name regex]   -> preview/survey_N.png + preview/survey_index.txt
"""
import glob
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import swatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = re.compile(r"_nrml|_extra|_emis|_mask|_mod_|lmap|lmbake|plod|_vc_|_ao|rough|winter|xwinterx|swatchtint", re.I)


def main():
    rx = re.compile(sys.argv[1], re.I) if len(sys.argv) > 1 else None
    done = {re.sub(r"_quality\d+\.pb$", "", os.path.basename(f))
            for f in glob.glob(os.path.join(ROOT, "build", "final", "**", "*.pb"), recursive=True)}
    best = {}
    for f in glob.glob(os.path.join(ROOT, "extract", "**", "*.pb"), recursive=True):
        base = os.path.basename(f)
        if SKIP.search(base) or not re.search(r"bclr|diff|maskrgba", base, re.I):
            continue
        if rx and not rx.search(base):
            continue
        stem = re.sub(r"_quality\d+\.pb$", "", base)
        if stem in done:
            continue
        try:
            w = swatch.parse(open(f, "rb").read())["width"]
        except Exception:
            continue
        if stem not in best or w > best[stem][0]:
            best[stem] = (w, f)
    items = sorted(best.items())
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 13)
    per, cols, tw, th = 30, 6, 330, 330
    index = []
    for p in range(0, len(items), per):
        chunk = items[p:p + per]
        sheet = Image.new("RGB", (cols * tw, -(-len(chunk) // cols) * (th + 20)), (35, 35, 35))
        d = ImageDraw.Draw(sheet)
        for k, (stem, (w, f)) in enumerate(chunk):
            try:
                img = swatch.to_image(open(f, "rb").read())[0].convert("RGB")
            except Exception:
                continue
            img.thumbnail((tw - 6, th - 6))
            x, y = (k % cols) * tw, (k // cols) * (th + 20)
            sheet.paste(img, (x + 3, y + 3))
            n = p + k
            label = re.sub(r"_[0-9a-f]{8}-[0-9a-f-]{27}", "", stem)
            d.text((x + 3, y + th), f"#{n} {label[:42]}", fill=(255, 230, 90), font=font)
            index.append(f"#{n}\t{label}\t{w}")
        sheet.save(os.path.join(ROOT, "preview", f"survey_{p // per + 1}.png"))
    open(os.path.join(ROOT, "preview", "survey_index.txt"), "w").write("\n".join(index))
    print(len(items), "unmodded textures,", -(-len(items) // per), "sheets")


if __name__ == "__main__":
    main()
