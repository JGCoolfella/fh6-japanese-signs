"""Contact sheet: one tinted-sign mask rendered with every material variant's inks.

Usage: python tools/mask_matrix.py <model stem> <mask stem>  -> preview/matrix_<mask>.png
"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import install
import list_inks
import mask_preview
import swatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    model, mask_stem = sys.argv[1], sys.argv[2]
    lookup = install.chunk_lookup()
    c, i = lookup[next(n for n in lookup if n.startswith(model + "_cluster000"))]
    blocks = list_inks.blocks(install.original_entry(c, i))
    fs = glob.glob(os.path.join(ROOT, "extract", "**", f"{mask_stem}_pack_maskrgba_*.pb"), recursive=True)
    f = max(fs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
    mask = np.asarray(swatch.to_image(open(f, "rb").read())[0])
    thumbs = []
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 18)
    for b, (_, _, cols) in enumerate(blocks):
        inks = [cols.get(k) for k in list_inks.ORDER]
        im = mask_preview.composite(mask, inks)
        im.thumbnail((340, 340))
        canvas = Image.new("RGB", (im.width, im.height + 22), (30, 30, 30))
        canvas.paste(im, (0, 22))
        ImageDraw.Draw(canvas).text((4, 1), f"block {b}", fill=(255, 255, 0), font=font)
        thumbs.append(canvas)
    cols_n = 5
    w = max(t.width for t in thumbs) + 6
    h = max(t.height for t in thumbs) + 6
    rows = -(-len(thumbs) // cols_n)
    sheet = Image.new("RGB", (cols_n * w, rows * h), (60, 60, 60))
    for k, t in enumerate(thumbs):
        sheet.paste(t, ((k % cols_n) * w, (k // cols_n) * h))
    out = os.path.join(ROOT, "preview", f"matrix_{mask_stem}.png")
    sheet.save(out)
    print(out, len(thumbs), "blocks")


if __name__ == "__main__":
    main()
