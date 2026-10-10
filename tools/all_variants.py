"""Render EVERY material variant of every tinted sign model, using the exact mask texture
each variant references (texture id = SourceHash in AssetManifest.xml).

Writes preview/allvar_N.png sheets and preview/allvar_index.tsv:
  label  model  block  mask_stem  cell  grid
Usage: python tools/all_variants.py
"""
import glob
import os
import re
import struct
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
FINAL_MODE = "--final" in sys.argv
MANIFEST = os.path.join(install.TRACK, "AssetManifest.xml")


def hash_table():
    x = open(MANIFEST, encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r'Source="([^"]+?)\.swatch" SourceHash="(\d+)"', x):
        name = m.group(1).split("\\")[-1]
        stem = re.sub(r"_[0-9a-f]{8}-[0-9a-f-]{27}$", "", name)
        out[int(m.group(2))] = stem
    return out


def models():
    lookup = install.chunk_lookup()
    found = set()
    for n in lookup:
        m = re.match(r"(sgn_(?:cty|gbl|rur)_[a-z0-9_]+?)_cluster000\.i\.modelbin$", n)
        if m:
            found.add(m.group(1))
    return lookup, sorted(found)


def mask_image(stem, cache):
    if stem not in cache:
        fs = [f for f in glob.glob(os.path.join(ROOT, "extract", "**", f"{stem}_*.pb"), recursive=True)
              if open(f, "rb").read(4) == b"burG"]
        if not fs:
            cache[stem] = None
        else:
            f = max(fs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
            if FINAL_MODE:
                alt = os.path.join(ROOT, "build", "final", os.path.relpath(f, os.path.join(ROOT, "extract")))
                f = alt if os.path.exists(alt) else f
            try:
                cache[stem] = np.asarray(swatch.to_image(open(f, "rb").read())[0])
            except Exception:
                cache[stem] = None
    return cache[stem]


def main():
    hashes = hash_table()
    lookup, mods = models()
    cache = {}
    rows = []
    for model in mods:
        data = install.original_entry(*lookup[model + "_cluster000.i.modelbin"])
        if FINAL_MODE:
            alt = glob.glob(os.path.join(ROOT, "build", "final", "**", model + "_cluster000.i.modelbin"), recursive=True)
            if alt:
                data = open(alt[0], "rb").read()
        if not re.search(rb"environment_signage", data):
            continue
        for b, tex, grid, cell, cols in variants.variant_table(data):
            if not tex:
                continue
            h = struct.unpack(">I", bytes.fromhex(tex))[0]
            stem = hashes.get(h) or hashes.get(struct.unpack("<I", bytes.fromhex(tex))[0])
            if not stem:
                continue
            m = mask_image(stem, cache)
            if m is None:
                rows.append((model, b, stem, cell, grid, None))
                continue
            slots = rm.layer_slots(data, b)
            inks = [rm.slot_rgb(data, slots[L]) if L in slots else None for L in rm.LAYERS]
            x0, y0, x1, y1 = rm.resolve_area(("cell", cell[0], cell[1], grid[0], grid[1]), m)
            if x1 - x0 < 2 or y1 - y0 < 2:
                continue
            rows.append((model, b, stem, cell, grid, mask_preview.composite(m[y0:y1, x0:x1], inks)))
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 13)
    per, cols_n, tw, th = 48, 8, 240, 150
    index = []
    for p in range(0, len(rows), per):
        chunk = rows[p:p + per]
        sheet = Image.new("RGB", (cols_n * tw, -(-len(chunk) // cols_n) * (th + 30)), (30, 30, 30))
        d = ImageDraw.Draw(sheet)
        for k, (model, b, stem, cell, grid, im) in enumerate(chunk):
            n = p + k
            x, y = (k % cols_n) * tw, (k // cols_n) * (th + 30)
            if im is not None and im.width > 1 and im.height > 1:
                t = im.copy()
                t.thumbnail((tw - 6, th - 6))
                sheet.paste(t, (x + 3, y + 3))
            else:
                d.text((x + 6, y + 40), "mask not extracted", fill=(255, 80, 80), font=font)
            short = model.replace("sgn_", "").replace("_01_a", "")
            d.text((x + 3, y + th), f"#{n} {short} b{b}", fill=(255, 230, 90), font=font)
            d.text((x + 3, y + th + 14), stem.replace(model, "")[:30], fill=(170, 170, 170), font=font)
            index.append(f"#{n}\t{model}\t{b}\t{stem}\t{cell}\t{grid}")
        sheet.save(os.path.join(ROOT, "preview", f"{'finalvar' if FINAL_MODE else 'allvar'}_{p // per + 1}.png"))
    open(os.path.join(ROOT, "preview", "allvar_index.tsv"), "w").write("\n".join(index))
    print(len(rows), "variants,", -(-len(rows) // per), "sheets")


if __name__ == "__main__":
    main()
