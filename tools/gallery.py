"""Before/after overview of every change, as PNG sheets in _modwork/overview/.

Plain textures: original vs modded (largest version, alpha ignored).
Tinted signs: each rebranded variant rendered with its inks, original vs modded.
The konbini fascia is shown as the game composites it (alpha 0 = lit white panel).
"""
import glob
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import install
import jobs_masks
import mask_preview
import rebrand_masks as rm
import swatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "overview")
FONT = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 18)
SMALL = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
SKIP = re.compile(r"_nrml|_extra|_emis|plod", re.I)  # technical maps: not useful to look at


def largest(paths):
    return max(paths, key=lambda f: swatch.parse(open(f, "rb").read())["width"])


def shown(data, stem):
    img = swatch.to_image(data)[0]
    if "bld_gbl_comm_03_a_features" in stem:  # konbini fascia: emulate the lit panel
        a = np.asarray(img).astype(float)
        al = a[..., 3:4] / 255
        rgb = a[..., :3] * al + 255 * (1 - al)
        rgb[128:] = a[128:, :, :3]
        return Image.fromarray(rgb.clip(0, 255).astype(np.uint8))
    return img.convert("RGB")


def pairs_plain():
    stems = {}
    for f in glob.glob(os.path.join(ROOT, "build", "final", "**", "*.pb"), recursive=True):
        base = os.path.basename(f)
        if "maskrgba" in base or SKIP.search(base):
            continue
        stem = re.sub(r"_[0-9a-f]{8}-[0-9a-f-]{27}_quality\d+\.pb$", "", base)
        stems.setdefault(stem, []).append(f)
    out = []
    for stem, files in sorted(stems.items()):
        if "xwinterx" in stem:
            continue
        new = largest(files)
        old = os.path.join(ROOT, "extract", os.path.relpath(new, os.path.join(ROOT, "build", "final")))
        out.append((stem, shown(open(old, "rb").read(), stem), shown(open(new, "rb").read(), stem)))
    return out


def pairs_masks():
    out = []
    lookup = install.chunk_lookup()
    for model, mask, block, area, d in jobs_masks.JOBS:
        name = next(n for n in lookup if n.startswith(model + "_cluster000"))
        old_model = install.original_entry(*lookup[name])
        new_model = open(glob.glob(os.path.join(ROOT, "build", "final", "**", name), recursive=True)[0], "rb").read()
        imgs = []
        for data, base_dir in ((old_model, "extract"), (new_model, os.path.join("build", "final"))):
            slots = rm.layer_slots(data, block)
            inks = [rm.slot_rgb(data, slots[L]) if L in slots else None for L in rm.LAYERS]
            f = largest(glob.glob(os.path.join(ROOT, base_dir, "**", f"{mask}_pack_maskrgba_*.pb"), recursive=True))
            m = np.asarray(swatch.to_image(open(f, "rb").read())[0])
            x0, y0, x1, y1 = rm.resolve_area(area, m)
            imgs.append(mask_preview.composite(m[y0:y1, x0:x1], inks))
        out.append((f"{model} variant {block}", imgs[0], imgs[1]))
    return out


def sheet(pairs, title, path, per_page=12, cell=(420, 300)):
    cw, ch = cell
    pages = []
    for p in range(0, len(pairs), per_page):
        chunk = pairs[p:p + per_page]
        cols = 2
        rows = -(-len(chunk) // cols)
        W = cols * (2 * cw + 40)
        H = 50 + rows * (ch + 46)
        img = Image.new("RGB", (W, H), (28, 28, 30))
        d = ImageDraw.Draw(img)
        d.text((12, 12), f"{title}  (page {p // per_page + 1})   left = original, right = modded", fill=(255, 220, 80), font=FONT)
        for k, (label, a, b) in enumerate(chunk):
            x = (k % cols) * (2 * cw + 40) + 12
            y = 50 + (k // cols) * (ch + 46)
            d.text((x, y), label[:70], fill=(220, 220, 220), font=SMALL)
            for j, im in enumerate((a, b)):
                t = im.copy()
                t.thumbnail((cw - 8, ch - 8))
                img.paste(t, (x + j * cw + (cw - 8 - t.width) // 2, y + 22 + (ch - 8 - t.height) // 2))
            d.line((x + cw - 4, y + 22, x + cw - 4, y + ch + 14), fill=(255, 220, 80), width=2)
        out = f"{path}_{p // per_page + 1}.png"
        img.save(out)
        pages.append(out)
    return pages


def main():
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "*.png")):
        os.remove(f)
    pages = sheet(pairs_plain(), "Textures", os.path.join(OUT, "textures"))
    pages += sheet(pairs_masks(), "Tinted shop signs", os.path.join(OUT, "tinted_signs"), cell=(420, 180))
    for p in pages:
        print(p)


if __name__ == "__main__":
    main()
