"""Building directory boards (sgn_cty_billboard_sqre_x9_01_a): mask-only rebrand.

The mask is a 6x6 grid of 341px logo tiles shared by ~70 colourways. Each matched tile is
cleared (except its floor label corner) and the real logo is written into the board's ink
channels by colour: dark -> R, red -> G, blue -> B. No model changes needed.
"""
import glob
import os
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import brand
import install
import swatch

ROOT = brand.ROOT
FINAL = os.path.join(ROOT, "build", "final")
STEM = "sgn_cty_billboard_sqre_x9_01_a_pack_maskrgba"
T = 2048 / 6
INKS = {"R": (30, 30, 30), "G": (220, 40, 40), "B": (40, 80, 220)}
# (row, col) -> (logo file, fill, rotate)
TILES = {
    (1, 0): ("matsukiyo_logo_sq.png", 0.8, 0), (1, 3): ("seiyu_logo.png", 0.86, 0), (1, 4): ("seiyu_logo.png", 0.86, 0),
    (1, 5): ("taitostation_logo.png", 0.9, 0), (0, 4): ("docomo_logo.png", 0.86, 0), (4, 4): ("docomo_logo.png", 0.86, 0),
    (2, 0): ("japanpost_logo.png", 0.86, 0), (2, 4): ("starbucks_logo.png", 0.7, 0), (4, 0): ("starbucks_logo.png", 0.7, 0),
    (3, 1): ("nakau_logo.png", 0.8, 0), (5, 4): ("nakau_logo.png", 0.8, 0), (3, 4): ("ichiran_logo.png", 0.8, 0),
    (4, 1): ("welcia_logo.png", 0.86, 0), (4, 5): ("ohsho_logo.png", 0.86, 0), (5, 0): ("uniqlo_logo_en.png", 0.8, 0),
    (5, 1): ("seiyu_logo.png", 0.86, 0),
}


def tile_channels(logo_file, size, fill, rotate):
    S = size * 2
    logo = Image.open(os.path.join(brand.ASSETS, logo_file)).convert("RGBA")
    if rotate:
        logo = logo.rotate(rotate, expand=True)
    k = min(S * fill / logo.width, S * fill / logo.height)
    logo = logo.resize((max(1, round(logo.width * k)), max(1, round(logo.height * k))), Image.LANCZOS)
    canvas = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    canvas.paste(logo, ((S - logo.width) // 2, (S - logo.height) // 2 + S // 20), logo)
    a = np.asarray(canvas).astype(np.float32)
    alpha = a[..., 3] / 255
    rgb = a[..., :3]
    lum = rgb.mean(axis=2)
    inks = np.array(list(INKS.values()), np.float32)
    idx = ((rgb[:, :, None, :] - inks[None, None]) ** 2).sum(-1).argmin(-1)
    ink_mask = alpha * (lum < 225)  # white parts of logos stay background
    out = {}
    for k_, name in enumerate(INKS):
        ch = ink_mask * (idx == k_)
        out[name] = np.asarray(Image.fromarray((ch * 255).astype(np.uint8)).resize((size, size), Image.LANCZOS))
    return out


def main():
    srcs = glob.glob(os.path.join(ROOT, "extract", "**", f"{STEM}_*.pb"), recursive=True)
    big = max(srcs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
    cur_big = os.path.join(FINAL, os.path.relpath(big, os.path.join(ROOT, "extract")))
    full = np.asarray(swatch.to_image(open(cur_big if os.path.exists(cur_big) else big, "rb").read())[0]).copy()
    import jobs_user
    for (r, c), (logo, fill, rot) in TILES.items():
        if (r, c) in jobs_user.X9_KEEP:
            continue  # user chose keep original
        import brand_filter
        if not brand_filter.on(brand_filter.brand_of(logo)):
            continue  # brand switched off
        x0, y0, x1, y1 = round(c * T), round(r * T), round((c + 1) * T), round((r + 1) * T)
        size = min(x1 - x0, y1 - y0)
        keep = full[y0:y0 + 70, x0:x0 + 95].copy()  # floor label
        full[y0:y1, x0:x1, :] = 0
        chans = tile_channels(logo, size, fill, rot)
        for k_, name in enumerate(("R", "G", "B")):
            full[y0:y0 + size, x0:x0 + size, k_] = chans[name]
        full[y0:y0 + 70, x0:x0 + 95] = keep
    new_full = Image.fromarray(full, "RGBA")
    with tempfile.TemporaryDirectory() as tmp:
        for src in srcs:
            orig = open(src, "rb").read()
            inf = swatch.parse(orig)
            img = Image.merge("RGBA", [ch.resize((inf["width"], inf["height"]), Image.LANCZOS) for ch in new_full.split()])
            dest = os.path.join(FINAL, os.path.relpath(src, os.path.join(ROOT, "extract")))
            base = open(dest if os.path.exists(dest) else src, "rb").read()
            data = brand.encode(img, orig, tmp, keep_alpha=False, base_bytes=base)
            if not install.fits_slot(os.path.basename(src), data):
                print("   too big, skipped:", os.path.basename(src)[-30:])
                continue
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(data)
    print(f"built {STEM} x{len(srcs)}")


if __name__ == "__main__":
    main()
