"""Rebrand the city shopfront fascia atlas (sgn_gbl_shop_station_atlas_01_a_bclr).

The right half of the 1024x512 atlas is the '365 Konbini' fascia:
  y   0-111  stripe strip A (vertical mirror of strip B)
  y 112-295  logo panel (shown squashed ~1.9x horizontally in game)
  y 296-407  stripe strip B (upright)
  y 408-511  ATM / P / 24h plates on yellow
The left half (Kadomart) is left untouched.

Usage: python tools/brand_station.py 7eleven
"""
import glob
import os
import shutil
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import brand
import swatch

ROOT = brand.ROOT
X0 = 512                      # right half
STRIP_H = 112
PANEL = (112, 296)
PANEL_X = (527, 893)          # visible panel width in the atlas
SQUASH = 1.9                  # in-game horizontal compression of the panel
WHITE = (252, 252, 250)


def strip_7eleven(width):
    orange, green, red = (245, 130, 31), (0, 128, 97), (237, 27, 45)
    a = np.zeros((STRIP_H, width, 3), np.uint8)
    a[:] = WHITE
    for top, bottom, col in ((0.03, 0.23, orange), (0.315, 0.62, green), (0.72, 0.95, red)):
        a[round(top * STRIP_H): round(bottom * STRIP_H)] = col
    return a


def clean_logo(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.int16)
    sat = a.max(axis=2) - a.min(axis=2)
    ys, xs = np.where(sat > 90)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
    s = a.max(axis=2) - a.min(axis=2)
    a[s < 25] = 255
    return Image.fromarray(a.astype(np.uint8))


def build_7eleven(img):
    a = np.asarray(img.convert("RGB")).copy()
    w = a.shape[1] - X0
    strip = strip_7eleven(w)
    a[296:296 + STRIP_H, X0:] = strip            # upright strip
    a[0:STRIP_H, X0:] = strip[::-1]              # mirrored strip
    # Logo panel: white, logo drawn in "screen space" then stretched by SQUASH.
    a[PANEL[0]:PANEL[1], X0:] = WHITE
    ph = PANEL[1] - PANEL[0]
    pw = PANEL_X[1] - PANEL_X[0]
    canvas = Image.new("RGB", (round(pw / SQUASH), ph), (255, 255, 255))
    logo = clean_logo(os.path.join(brand.ASSETS, "7eleven_panel_logo.png"))
    logo.thumbnail((canvas.width - 8, ph - 14), Image.LANCZOS)
    canvas.paste(logo, ((canvas.width - logo.width) // 2, (ph - logo.height) // 2))
    canvas = canvas.resize((pw, ph), Image.LANCZOS)
    a[PANEL[0]:PANEL[1], PANEL_X[0]:PANEL_X[1]] = np.asarray(canvas)
    # Panel is pure white; snap near-white resampling residue so no box/outline shows.
    panel = a[PANEL[0]:PANEL[1], X0:].astype(int)
    panel[(panel.min(axis=2) > 200) & (panel.max(axis=2) - panel.min(axis=2) < 40)] = 255
    a[PANEL[0]:PANEL[1], X0:] = panel
    # Plates area: yellow background -> white, plates themselves kept.
    plates = a[408:, X0:].astype(int)
    yellow = (plates[..., 0] > 200) & (plates[..., 1] > 180) & (plates[..., 2] < 120)
    plates[yellow] = WHITE
    a[408:, X0:] = plates
    return Image.fromarray(a)


LAWSON_BLUE, LAWSON_PINK = (0, 104, 183), (240, 160, 190)


def strip_lawson(width):
    a = np.zeros((STRIP_H, width, 3), np.uint8)
    a[:] = WHITE
    for top, bottom, col in ((0.23, 0.70, LAWSON_BLUE), (0.82, 0.89, LAWSON_PINK)):
        a[round(top * STRIP_H): round(bottom * STRIP_H)] = col
    return a


def build_lawson(img):
    a = np.asarray(img.convert("RGB")).copy()
    w = a.shape[1] - X0
    strip = strip_lawson(w)
    a[296:296 + STRIP_H, X0:] = strip            # upright strip
    a[0:STRIP_H, X0:] = strip[::-1]              # mirrored strip
    a[PANEL[0]:PANEL[1], X0:] = WHITE
    ph = PANEL[1] - PANEL[0]
    pw = PANEL_X[1] - PANEL_X[0]
    canvas = Image.new("RGB", (round(pw / SQUASH), ph), (255, 255, 255))
    logo = Image.open(os.path.join(brand.ASSETS, "lawson_logo.png")).convert("RGBA")
    la = np.asarray(logo).copy()
    la[..., :3] = LAWSON_BLUE
    logo = Image.fromarray(la)
    logo.thumbnail((canvas.width - 8, int(ph * 0.5)), Image.LANCZOS)
    canvas.paste(logo, ((canvas.width - logo.width) // 2, (ph - logo.height) // 2), logo)
    canvas = canvas.resize((pw, ph), Image.LANCZOS)
    a[PANEL[0]:PANEL[1], PANEL_X[0]:PANEL_X[1]] = np.asarray(canvas)
    plates = a[408:, X0:].astype(int)
    yellow = (plates[..., 0] > 200) & (plates[..., 1] > 180) & (plates[..., 2] < 120)
    plates[yellow] = WHITE
    a[408:, X0:] = plates
    return Image.fromarray(a)


BUILDERS = {"7eleven": build_7eleven, "lawson": build_lawson}


def main():
    brand_name = sys.argv[1] if len(sys.argv) > 1 else "7eleven"
    build_fn = BUILDERS[brand_name]
    sources = [f for f in glob.glob(os.path.join(ROOT, "extract", "**", "sgn_gbl_shop_station_atlas_01_a_bclr_*.pb"),
                                    recursive=True) if open(f, "rb").read(4) == b"burG"]
    if not sources:
        sys.exit("Extract first: python tools/fh6minizip.py ../media/Tracks/Brio '*sgn_gbl_shop_station*' -o extract")
    src_big = max(sources, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
    full, info = swatch.to_image(open(src_big, "rb").read())
    if (info["width"], info["height"]) != (1024, 512):
        sys.exit(f"unexpected atlas size {info['width']}x{info['height']}")
    new_full = build_fn(full)
    new_full.save(os.path.join(ROOT, "preview", f"station_{brand_name}_design.png"))
    out_root = os.path.join(ROOT, "build", brand_name)
    with tempfile.TemporaryDirectory() as tmp:
        for src in sources:
            orig = open(src, "rb").read()
            i = swatch.parse(orig)
            img = new_full.resize((i["width"], i["height"]), Image.LANCZOS)
            new = brand.encode(img, orig, tmp)
            rel = os.path.relpath(src, os.path.join(ROOT, "extract"))
            dest = os.path.join(out_root, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(new)
            if i["width"] == 1024:
                swatch.to_image(new)[0].convert("RGB").save(
                    os.path.join(ROOT, "preview", f"station_{brand_name}_encoded.png"))
            print(f"built {os.path.basename(dest)} {i['width']}x{i['height']}")


if __name__ == "__main__":
    main()
