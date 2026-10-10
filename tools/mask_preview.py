"""Render a tinted sign's mask with the inks of chosen material variant blocks.

Usage: python tools/mask_preview.py <model stem> <mask stem> <block> [block ...]
Writes preview/maskprev_<mask>_<block>.png (layering: base, then R, G, B, A).
"""
import glob
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import install
import list_inks
import swatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def composite(mask, inks):
    m = mask.astype(np.float32) / 255
    col = np.zeros(mask.shape[:2] + (3,), np.float32) + np.array(inks[0] or (0, 0, 0), np.float32)
    for k, ink in enumerate(inks[1:]):
        if ink is None:
            continue
        col = col * (1 - m[..., k:k + 1]) + np.array(ink, np.float32) * m[..., k:k + 1]
    return Image.fromarray(col.clip(0, 255).astype(np.uint8))


def main():
    model, mask_stem, blocks = sys.argv[1], sys.argv[2], [int(b) for b in sys.argv[3:]]
    lookup = install.chunk_lookup()
    c, i = lookup[next(n for n in lookup if n.startswith(model + "_cluster000"))]
    allb = list_inks.blocks(install.original_entry(c, i))
    fs = glob.glob(os.path.join(ROOT, "extract", "**", f"{mask_stem}_pack_maskrgba_*.pb"), recursive=True)
    f = max(fs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
    mask = np.asarray(swatch.to_image(open(f, "rb").read())[0])
    for b in blocks:
        cols = allb[b][2]
        inks = [cols.get(k) for k in list_inks.ORDER]
        composite(mask, inks).save(os.path.join(ROOT, "preview", f"maskprev_{mask_stem}_{b}.png"))
        print(b, inks)


if __name__ == "__main__":
    main()
