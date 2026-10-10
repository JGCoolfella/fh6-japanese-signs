"""Rebrand the standalone konbini building bld_gbl_comm_03_a (the Fuji-view store type).

Textures handled (summer + winter, every quality):
  *_features_*_bclr   fascia band (rows 0-128 of 1024) -> brand design
  *_features_*_nrml   embossed 365 panel/lettering in the band -> flattened
  *_features_*_extra  365 lettering in the shininess map -> flattened
  *_plod_*_diff/emis  far-distance version: yellow band / red logo -> brand colours

Usage: python tools/brand_konbini_bld.py lawson
"""
import glob
import os
import re
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))
import brand
import install
import swatch

ROOT = brand.ROOT
BAND_H = 128          # fascia band height in the 1024 texture
LOGO = (418, 606)     # logo panel columns in the 1024 texture
PANEL_STRETCH = 1.75  # the building's mesh stretches the panel ~1.75x horizontally


def band_lawson(w=1024, h=BAND_H):
    """Fascia measured from the Fujikawaguchiko Lawson (assets/ref/lawson_fuji_*.jpg).
    Returns (RGB image, glow mask). The glow mask feeds the colour texture's alpha, which the
    game uses for the lit-sign glow: the whole lightbox glows, the letters glow less so the
    blue wordmark stays readable at night."""
    blue, pink, white = (0, 104, 183), (240, 160, 190), (250, 251, 252)
    a = np.zeros((h, w, 3), np.uint8)
    a[:] = white
    # kept within the top ~70%: the bottom rows of the fascia are hidden in game (the original 365
    # stripes all end at row 90 of 128), so the pink line sat out of view there
    for top, bottom, col in ((0.16, 0.58, blue), (0.63, 0.70, pink)):
        a[round(top * h): round(bottom * h)] = col
    x0, x1 = LOGO
    a[:, x0:x1] = (255, 255, 255)
    img = Image.fromarray(a)
    d = ImageDraw.Draw(img)
    d.line((x0, 0, x0, h), fill=(210, 212, 216), width=2)
    d.line((x1 - 1, 0, x1 - 1, h), fill=(210, 212, 216), width=2)
    # Wordmark drawn at on-screen proportions, then squashed to cancel the mesh stretch.
    logo = Image.open(os.path.join(brand.ASSETS, "lawson_logo.png")).convert("RGBA")
    la = np.asarray(logo).copy()
    la[..., :3] = blue  # same blue as the stripes
    logo = Image.fromarray(la)
    screen_w = int((x1 - x0) * PANEL_STRETCH)
    logo.thumbnail((int(screen_w * 0.92), int(h * 0.56)), Image.LANCZOS)
    logo = logo.resize((max(1, round(logo.width / PANEL_STRETCH)), logo.height), Image.LANCZOS)
    pos = (x0 + ((x1 - x0) - logo.width) // 2, max(0, round(0.37 * h - logo.height / 2)))   # centred on the blue band
    img.paste(logo, pos, logo)
    # Alpha layout copied from the original 365 sign: 1 on the stripes, 0 on the logo panel
    # background, 1 on the lettering (the original had its "365" letters at full alpha).
    # Inverting this washed the wordmark out in game.
    glow = np.ones((h, w), np.float32)
    glow[:, x0:x1] = 0.0
    letters = np.asarray(logo.split()[3], np.float32) / 255
    region = glow[pos[1]:pos[1] + logo.height, pos[0]:pos[0] + logo.width]
    glow[pos[1]:pos[1] + logo.height, pos[0]:pos[0] + logo.width] = np.maximum(region, letters)
    return img, glow


BRANDS = {"lawson": (band_lawson, (0, 104, 183), (240, 160, 190))}


def flatten_band(img, h_frac):
    """Replace the band rows with a plain patch of the same band (removes embossed lettering)."""
    a = np.asarray(img).copy()
    H, W = a.shape[:2]
    bh = int(round(H * h_frac))
    s = W / 1024
    plain = a[:bh, int(40 * s): int(380 * s)]
    reps = -(-W // plain.shape[1])
    a[:bh] = np.concatenate([plain, plain[:, ::-1]] * reps, axis=1)[:, :W]
    return Image.fromarray(a, img.mode)


def recolour_plod(img, stripe, accent):
    """Far LOD: yellow band pixels -> white with brand stripe; red logo pixels -> brand colour."""
    a = np.asarray(img.convert("RGBA")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    yellow = (r > 120) & (g > 100) & (b < 0.6 * g) & (r - b > 60)
    red = (r > 150) & (g < 90) & (b < 100)
    rows = np.where(yellow.any(axis=1))[0]
    out = a.copy()
    out[yellow] = (245, 246, 248, 255)
    if len(rows):
        mid = (rows.min() + rows.max()) // 2
        band_rows = yellow.copy()
        band_rows[:mid] = False
        band_rows[mid + 1:] = False
        out[band_rows] = (*stripe, 255)
    out[red] = (*stripe, 255)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "lawson"
    design, stripe, accent = BRANDS[name]
    band, glow = design()
    band.save(os.path.join(ROOT, "preview", f"konbini_{name}_band.png"))
    out_root = os.path.join(ROOT, "build", name)
    srcs = glob.glob(os.path.join(ROOT, "extract", "**", "bld_gbl_comm_03_a", "**", "*.pb"), recursive=True)
    with tempfile.TemporaryDirectory() as tmp:
        for src in sorted(srcs):
            base = os.path.basename(src)
            orig = open(src, "rb").read()
            if orig[:4] != b"burG":
                continue
            info = swatch.parse(orig)
            if info["format"] not in swatch.FORMATS:
                continue
            img, _ = swatch.to_image(orig)
            W, H = info["width"], info["height"]
            keep_alpha = True
            if re.search(r"_features_x(summer|winter)x_bclr", base):
                rgb = img.convert("RGB")
                bh = int(round(H * BAND_H / 1024))
                scaled = band.resize((W, bh), Image.LANCZOS)
                rgb.paste(brand.weathered(scaled, rgb.crop((0, 0, W, bh))) if W >= 256 else scaled, (0, 0))
                # Alpha = glow mask: rebuild it for the band from our design (the original
                # still had the 365 letters in it), keep the rest of the texture's alpha.
                alpha = np.asarray(img.split()[3]).copy()
                g = Image.fromarray((glow * 255).astype(np.uint8)).resize((W, bh), Image.LANCZOS)
                alpha[:bh] = np.asarray(g)
                new_img = Image.merge("RGBA", (*rgb.split(), Image.fromarray(alpha)))
                keep_alpha = False
            elif re.search(r"_features_x(summer|winter)x_(nrml|extra)", base):
                new_img = flatten_band(img, BAND_H / 1024)
                keep_alpha = False
            elif re.search(r"_plod_x(summer|winter)x_(diff|emis)", base):
                new_img = recolour_plod(img, stripe, accent)
                if "_emis" in base:  # glow: keep it dim, only where the original glowed
                    o = np.asarray(img.convert("RGB")).astype(float)
                    n = np.asarray(new_img.convert("RGB")).astype(float)
                    lum = o.max(axis=2, keepdims=True) / 255
                    new_img = Image.fromarray((n * lum).clip(0, 255).astype(np.uint8))
            else:
                continue
            new = brand.encode(new_img, orig, tmp, keep_alpha=keep_alpha)
            rel = os.path.relpath(src, os.path.join(ROOT, "extract"))
            dest = os.path.join(out_root, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(new)
            if W == 1024 and "summer" in base and "bclr" in base:
                swatch.to_image(new)[0].convert("RGB").save(os.path.join(ROOT, "preview", f"konbini_{name}_bclr.png"))
            print(f"built {base[:60]} {W}x{H}")


if __name__ == "__main__":
    main()
