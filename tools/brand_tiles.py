"""Replace single-brand tiles inside shared sign atlases (A-boards, banners, boards).

Each entry: texture name, tile box (x0, y0, x1, y1) in the largest version,
and an optional plain area of the original tile to borrow grime from.
Usage: python tools/brand_tiles.py 7eleven
"""
import glob
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
import brand
import brand_station
import swatch

ROOT = brand.ROOT

# 365 Konbini tiles -> 7-Eleven
TILES_365 = [
    ("sgn_gbl_shop_aboard_01_a6_bclr", (0, 0, 342, 256), None),
    ("sgn_gbl_shop_aboard_01_a8_bclr", (682, 0, 1024, 512), None),
    ("sgn_gbl_board_grassroute_01_abcd_bclr", (0, 768, 512, 1024), (90, 776, 430, 800)),
    ("sgn_gbl_shops_vinyl_poster_01_a6_bclr", (0, 0, 256, 512), None),
    ("tex_cty_decal_akih_billbrd_atlas_01_vertical_b_bclr", (0, 0, 683, 2048), None),
]

ORANGE, GREEN, RED = (245, 130, 31), (0, 128, 97), (237, 27, 45)


def tile_7eleven(w, h):
    img = Image.new("RGB", (w, h), (250, 250, 248))
    a = np.asarray(img).copy()
    horizontal = w >= h
    # Signature stripes across the bottom: orange, green, red with white gaps.
    unit = h * (0.06 if horizontal else 0.035)
    y = h - unit * 1.2
    for col in (RED, GREEN, ORANGE):
        a[int(y - unit): int(y)] = col
        y -= unit * 1.45
    stripes_top = int(y)
    img = Image.fromarray(a)
    logo = brand_station.clean_logo(os.path.join(brand.ASSETS, "7eleven_panel_logo.png"))
    box_w = int(w * (0.62 if horizontal else 0.8))
    box_h = int(stripes_top * 0.86)
    logo.thumbnail((box_w, box_h), Image.LANCZOS)
    img.paste(logo, ((w - logo.width) // 2, (stripes_top - logo.height) // 2))
    p = np.asarray(img).astype(int)
    p[(p.min(axis=2) > 200) & (p.max(axis=2) - p.min(axis=2) < 40)] = (250, 250, 248)
    return Image.fromarray(p.astype(np.uint8))


LAWSON_BLUE, LAWSON_PINK = (0, 104, 183), (240, 160, 190)


def tile_lawson(w, h):
    """Lawson pylon / A-board style: Lawson-blue panel, white wordmark, pink pinstripe.
    Tall tiles get the wordmark running down the panel like real vertical Lawson signs."""
    img = Image.new("RGB", (w, h), LAWSON_BLUE)
    a = np.asarray(img).copy()
    vertical = h > w * 1.6
    if vertical:
        a[:, int(w * 0.80): int(w * 0.86)] = LAWSON_PINK
    else:
        a[int(h * 0.80): int(h * 0.86)] = LAWSON_PINK
    img = Image.fromarray(a)
    logo = Image.open(os.path.join(brand.ASSETS, "lawson_logo.png")).convert("RGBA")
    la = np.asarray(logo).copy()
    la[..., :3] = 255
    logo = Image.fromarray(la)
    if vertical:
        logo = logo.rotate(-90, expand=True)
        logo.thumbnail((int(w * 0.5), int(h * 0.86)), Image.LANCZOS)
        img.paste(logo, (int(w * 0.42) - logo.width // 2, (h - logo.height) // 2), logo)
    else:
        logo.thumbnail((int(w * 0.84), int(h * 0.34)), Image.LANCZOS)
        img.paste(logo, ((w - logo.width) // 2, int(h * 0.42) - logo.height // 2), logo)
    return img


TILE_DESIGNS = {"7eleven": None, "lawson": tile_lawson}


def grime(tile, original, sample):
    """Multiply by high-pass detail tiled from a plain patch of the original."""
    g = original.convert("L")
    o = np.asarray(g, np.float32) + 1
    blur = np.asarray(g.filter(ImageFilter.GaussianBlur(8)), np.float32) + 1
    x0, y0, x1, y1 = sample
    patch = (o / blur)[y0:y1, x0:x1]
    reps_y = -(-tile.height // patch.shape[0])
    reps_x = -(-tile.width // patch.shape[1])
    rows = np.concatenate([patch, patch[::-1]] * reps_y, axis=0)[: tile.height]
    full = np.concatenate([rows, rows[:, ::-1]] * reps_x, axis=1)[:, : tile.width]
    # Also keep the overall paper tint/darkening of the original tile area.
    out = np.asarray(tile, np.float32) * np.clip(full, 0.9, 1.06)[..., None]
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def main():
    brand_name = sys.argv[1] if len(sys.argv) > 1 else "7eleven"
    make_tile = TILE_DESIGNS[brand_name] or tile_7eleven
    out_root = os.path.join(ROOT, "build", brand_name)
    with tempfile.TemporaryDirectory() as tmp:
        for name, box, sample in TILES_365:
            sources = glob.glob(os.path.join(ROOT, "extract", "**", f"{name}_*.pb"), recursive=True)
            if not sources:
                print(f"skip {name}: not extracted")
                continue
            big = max(sources, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
            full, info = swatch.to_image(open(big, "rb").read())
            full = full.convert("RGB")
            x0, y0, x1, y1 = box
            tile = make_tile(x1 - x0, y1 - y0)
            if sample:
                tile = grime(tile, full, sample)
            full.paste(tile, (x0, y0))
            full.save(os.path.join(ROOT, "preview", f"tile_{brand_name}_{name}.png"))
            for src in sources:
                orig = open(src, "rb").read()
                i = swatch.parse(orig)
                img = full.resize((i["width"], i["height"]), Image.LANCZOS)
                new = brand.encode(img, orig, tmp)
                rel = os.path.relpath(src, os.path.join(ROOT, "extract"))
                dest = os.path.join(out_root, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "wb").write(new)
                print(f"built {os.path.basename(dest)} {i['width']}x{i['height']}")


if __name__ == "__main__":
    main()
