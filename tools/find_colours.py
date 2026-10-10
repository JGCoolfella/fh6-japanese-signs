"""Find textures by colour signature (e.g. the green/yellow/red 'Kakimoto' poster).

Usage: python tools/find_colours.py
Scans sgn_/prp_/bld_/tex_/int_/dec* colour textures (one mid-size version each) and lists
textures containing enough of each signature colour. Thumbnails -> preview/fc_*.png
"""
import os
import re
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import fh6minizip
import install
import swatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = re.compile(r"^(sgn|sng|prp|bld|tex|int|dec|amb|inf|gcr|city|commercial|highrise)", re.I)
COLOUR = re.compile(r"bclr|diff|basecol", re.I)


def signature(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    green = (r < 90) & (g > 105) & (g < 175) & (b > 50) & (b < 120)
    yellow = (r > 215) & (g > 185) & (b < 90)
    red = (r > 190) & (g < 70) & (b < 70)
    return green.mean(), yellow.mean(), red.mean()


def main():
    hits = []
    for c in range(4):
        names = fh6minizip.load_names(os.path.join(install.TRACK, f"ChunkContentsMiniZip{c}.txt"))
        mz = fh6minizip.MiniZip(os.path.join(install.TRACK, f"GeoChunk{c}.minizip"))
        groups = {}
        for i, n in names.items():
            base = os.path.basename(n)
            if not base.endswith(".pb") or not KEEP.match(base) or not COLOUR.search(base):
                continue
            stem = re.sub(r"_quality\d+\.pb$", "", base)
            groups.setdefault(stem, []).append(i)
        for stem, idxs in groups.items():
            idxs.sort(key=lambda i: mz.entries[i][1])
            pick = next((i for i in idxs if mz.entries[i][1] > 60000), idxs[-1])
            try:
                img = swatch.to_image(mz.read(pick))[0].convert("RGB")
            except Exception:
                continue
            g, y, r = signature(np.asarray(img))
            if g > 0.02 and y > 0.005 and r > 0.002:
                hits.append((stem, g, y, r))
                img.thumbnail((256, 256))
                img.save(os.path.join(ROOT, "preview", f"fc_{len(hits):02d}.png"))
                print(f"HIT {len(hits):02d} {stem[:70]}  green {g:.3f} yellow {y:.3f} red {r:.3f}", flush=True)
    print(len(hits), "hits")


if __name__ == "__main__":
    main()
