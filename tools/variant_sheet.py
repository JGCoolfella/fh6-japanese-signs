"""Render every variant of a tinted sign model as it appears in game: the variant's own
atlas cell, tinted with its own inks. One column per candidate mask sheet (when the model
uses several sheets, the right one is the one that looks like a sign).

Usage: python tools/variant_sheet.py <model stem> <mask stem> [<mask stem> ...]
"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import install
import mask_preview
import rebrand_masks as rm
import swatch
import variants

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    model, masks = sys.argv[1], sys.argv[2:]
    lookup = install.chunk_lookup()
    c, i = lookup[next(n for n in lookup if n.startswith(model + "_cluster000"))]
    data = install.original_entry(c, i)
    table = variants.variant_table(data)
    imgs = {}
    for m in masks:
        fs = glob.glob(os.path.join(ROOT, "extract", "**", f"{m}_pack_maskrgba_*.pb"), recursive=True)
        f = max(fs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
        imgs[m] = np.asarray(swatch.to_image(open(f, "rb").read())[0])
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 16)
    cw, ch = 300, 150
    sheet = Image.new("RGB", (60 + cw * len(masks), ch * len(table)), (35, 35, 35))
    d = ImageDraw.Draw(sheet)
    for r, (b, tex, grid, cell, cols) in enumerate(table):
        slots = rm.layer_slots(data, b)
        inks = [rm.slot_rgb(data, slots[L]) if L in slots else None for L in rm.LAYERS]
        d.text((4, r * ch + 4), f"b{b}\n{tex[:4]}\n{cell}", fill=(255, 255, 0), font=font)
        for k, m in enumerate(masks):
            mk = imgs[m]
            x0, y0, x1, y1 = rm.resolve_area(("cell", cell[0], cell[1], grid[0], grid[1]), mk)
            if x1 <= x0 or y1 <= y0:
                continue
            im = mask_preview.composite(mk[y0:y1, x0:x1], inks)
            im.thumbnail((cw - 6, ch - 6))
            sheet.paste(im, (60 + k * cw, r * ch + 3))
    out = os.path.join(ROOT, "preview", f"vs_{model}.png")
    sheet.save(out)
    print(out, len(table), "variants")


if __name__ == "__main__":
    main()
