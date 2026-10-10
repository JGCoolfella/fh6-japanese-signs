"""Rebrand the city POI decal atlases (city_poi_decals_atlas_a..j): 512px sheets of 64px
brand decals (many mirrored/rotated). Each tile is labelled with its fake brand (TILES);
the replacement is drawn upright and given the same orientation as the original tile,
found by matching the tile against that brand's upright exemplar under all 8 flips/rotations.

Stacks on build/final like the other job tools. Run after rebrand_plain.py.
"""
import glob
import os
import sys
import tempfile

import numpy as np
from PIL import Image, ImageOps

sys.path.insert(0, os.path.dirname(__file__))
import brand
import install
import swatch

ROOT = brand.ROOT
FINAL = os.path.join(ROOT, "build", "final")
ASSETS = brand.ASSETS
CELL = 64

W = (246, 246, 246)
# fake brand -> (background, logo file, logo fill, rotate for upright design)
DESIGN = {
    "prav": (W, "beams_logo.png", 0.86, 0),
    "fizi": (W, "mitsuya_logo.png", 0.9, 0),
    "tomi": (W, "tomica_logo.png", 0.88, 0),
    "moriya_v": (W, "seiyu_logo.png", 0.9, -90),
    "moriya_w": (W, "seiyu_logo.png", 0.86, 0),
    "on_ad": (W, "docomo_logo.png", 0.86, 0),
    "on_logo": (W, "docomo_logo.png", 0.86, 0),
    "flowzoil": ((230, 20, 30), "motul_logo.png", 0.9, 0),
    "swizzer": ((255, 222, 0), "cclemon_logo.png", 0.86, 0),
    "sybil": (W, "softbank_logo.png", 0.9, 0),
    "brass": (W, "kirin_logo.png", 0.86, 0),
    "owners": ((250, 215, 0), "yellowhat_logo.png", 0.9, 0),
    "midori": ((0, 88, 58), "smbc_logo_w.png", 0.88, 0),
    "midori_v": ((0, 88, 58), "smbc_logo_w.png", 0.9, -90),
    "medi": (W, "welcia_logo.png", 0.86, 0),
    "vaneso": (W, "boss_logo.png", 0.86, 0),
    "kakimoto": ((29, 57, 196), "matsukiyo_logo_sq.png", 0.86, 0),
    "kakimoto_g": ((29, 57, 196), "matsukiyo_logo_sq.png", 0.86, 0),
    "gacha": (W, "tokyofm_logo.png", 0.9, 0),
    "365_v": ((0, 104, 183), "lawson_logo.png", 0.9, -90),
}
EXEMPLAR = {"prav": "a00", "fizi": "a02", "tomi": "a03", "moriya_v": "a04", "moriya_w": "b02", "on_ad": "a06",
            "on_logo": "a23", "flowzoil": "a11", "swizzer": "b15", "sybil": "b16", "brass": "c22", "owners": "b03",
            "midori": "b21", "midori_v": "b04", "medi": "b05", "vaneso": "b06", "kakimoto": "c02",
            "kakimoto_g": "d05", "gacha": "c11", "365_v": "d20"}
TILES = {
    "a00": "prav", "a02": "fizi", "a03": "tomi", "a04": "moriya_v", "a05": "moriya_v", "a06": "on_ad", "a10": "tomi",
    "a11": "flowzoil", "a12": "tomi", "a13": "tomi", "a14": "tomi", "a15": "prav", "a16": "tomi", "a17": "on_ad",
    "a20": "moriya_v", "a21": "on_ad", "a22": "on_ad", "a23": "on_logo", "a24": "fizi", "a25": "on_logo", "a26": "fizi",
    "a27": "prav", "a30": "swizzer", "a31": "sybil", "a32": "brass", "b00": "fizi", "b01": "prav", "b02": "moriya_w",
    "b03": "owners", "b04": "midori_v", "b05": "medi", "b06": "vaneso", "b10": "owners", "b11": "vaneso",
    "b12": "owners", "b13": "owners", "b14": "owners", "b15": "swizzer", "b16": "sybil", "b20": "medi",
    "b21": "midori", "b22": "midori", "b23": "swizzer", "b25": "fizi", "c00": "on_logo", "c01": "swizzer",
    "c02": "kakimoto", "c03": "fizi", "c04": "medi", "c05": "midori_v", "c06": "sybil", "c10": "sybil",
    "c11": "gacha", "c12": "swizzer", "c13": "sybil", "c14": "fizi", "c15": "on_logo", "c16": "owners",
    "c20": "midori_v", "c21": "vaneso", "c22": "brass", "c23": "prav", "c25": "prav", "d00": "swizzer",
    "d01": "sybil", "d02": "sybil", "d03": "sybil", "d05": "kakimoto_g", "d06": "brass", "d10": "fizi",
    "d11": "on_ad", "d12": "prav", "d13": "gacha", "d14": "on_ad", "d15": "kakimoto", "d16": "fizi",
    "d20": "365_v", "d21": "sybil", "d22": "gacha", "d23": "fizi", "d25": "midori", "e00": "sybil",
    "e02": "swizzer", "e03": "prav", "e06": "gacha", "e10": "prav", "e11": "brass", "e12": "sybil",
    "e13": "flowzoil", "e14": "vaneso", "e15": "moriya_w", "e16": "swizzer", "e20": "on_logo", "e21": "gacha",
    "e22": "sybil", "e23": "midori", "e25": "moriya_w", "f02": "midori", "f03": "swizzer", "f06": "midori",
    "f10": "swizzer", "f11": "midori_v", "f12": "on_ad", "f13": "on_ad", "f15": "sybil", "f16": "vaneso",
    "f20": "kakimoto_g", "f21": "brass", "f22": "vaneso", "f23": "medi", "g12": "flowzoil", "g16": "on_ad",
    "g21": "on_logo", "g23": "sybil", "h16": "flowzoil", "h21": "prav", "h23": "moriya_w", "i16": "gacha",
}
TRANSFORMS = [
    lambda im: im, lambda im: im.transpose(Image.ROTATE_90), lambda im: im.transpose(Image.ROTATE_180),
    lambda im: im.transpose(Image.ROTATE_270), lambda im: ImageOps.mirror(im), lambda im: ImageOps.flip(im),
    lambda im: ImageOps.mirror(im.transpose(Image.ROTATE_90)), lambda im: ImageOps.flip(im.transpose(Image.ROTATE_90)),
]


def atlas_path(letter, base=None):
    fs = glob.glob(os.path.join(ROOT, "extract", "**", f"city_poi_decals_atlas_{letter}_diff_*.pb"), recursive=True)
    return fs


def tile_of(images, key):
    L, r, k = key[0], int(key[1]), int(key[2])
    return images[L].crop((k * CELL, r * CELL, (k + 1) * CELL, (r + 1) * CELL))


def feat(im):
    return np.asarray(im.convert("L").resize((16, 16), Image.BILINEAR), np.float32)


def design(kind):
    bg, logo_file, fill, rot = DESIGN[kind]
    S = CELL * 4
    img = Image.new("RGB", (S, S), bg)
    logo = Image.open(os.path.join(ASSETS, logo_file)).convert("RGBA")
    if rot:
        logo = logo.rotate(rot, expand=True)
    k = min(S * fill / logo.width, S * fill / logo.height)
    logo = logo.resize((max(1, round(logo.width * k)), max(1, round(logo.height * k))), Image.LANCZOS)
    img.paste(logo, ((S - logo.width) // 2, (S - logo.height) // 2), logo)
    return img.resize((CELL, CELL), Image.LANCZOS)


def custom_tile(file, bg, fill):
    """User artwork for one cell, upright. bg None = the artwork is the whole sticker."""
    S = CELL * 4
    art = Image.open(os.path.join(ASSETS, file)).convert("RGBA")
    if bg is None:
        return art.convert("RGB").resize((CELL, CELL), Image.LANCZOS)
    img = Image.new("RGBA", (S, S), tuple(bg) + (255,))
    k = min(S * fill / art.width, S * fill / art.height)
    art = art.resize((max(1, round(art.width * k)), max(1, round(art.height * k))), Image.LANCZOS)
    img.alpha_composite(art, ((S - art.width) // 2, (S - art.height) // 2))
    return img.convert("RGB").resize((CELL, CELL), Image.LANCZOS)


def main():
    import jobs_user
    images = {}
    srcs = {}
    for L in "abcdefghij":
        fs = atlas_path(L)
        big = max(fs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
        srcs[L] = fs
        images[L] = swatch.to_image(open(big, "rb").read())[0].convert("RGB")
    ex = {kind: feat(tile_of(images, key)) for kind, key in EXEMPLAR.items()}
    designs = {kind: design(kind) for kind in DESIGN}
    new = {L: images[L].copy() for L in images}
    import brand_filter
    for key, (file, bg, fill) in jobs_user.POI.items():
        if not brand_filter.on(brand_filter.brand_of(file)):
            continue
        L, r, k = key[0], int(key[1]), int(key[2])
        new[L].paste(custom_tile(file, bg, fill), (k * CELL, r * CELL))
    for key, kind in TILES.items():
        if key in jobs_user.POI or key in jobs_user.POI_KEEP:
            continue  # user's own artwork / user chose to keep the original
        if not brand_filter.on(brand_filter.brand_of(DESIGN[kind][1])):
            continue  # brand switched off
        t = feat(tile_of(images, key))
        # orientation: which transform of the upright exemplar best matches this tile
        best = min(range(8), key=lambda i: float(((feat(TRANSFORMS[i](Image.fromarray(ex[kind].astype(np.uint8)))) - t) ** 2).mean()))
        tile = TRANSFORMS[best](designs[kind])
        L, r, k = key[0], int(key[1]), int(key[2])
        new[L].paste(tile, (k * CELL, r * CELL))
    with tempfile.TemporaryDirectory() as tmp:
        for L in images:
            new[L].save(os.path.join(ROOT, "preview", f"final_poi_{L}.png"))
            full = new[L].convert("RGBA")
            for src in srcs[L]:
                orig = open(src, "rb").read()
                inf = swatch.parse(orig)
                img = full.resize((inf["width"], inf["height"]), Image.LANCZOS)
                data = brand.encode(img, orig, tmp, keep_alpha=True)
                if not install.fits_slot(os.path.basename(src), data):
                    print("   too big, keeping original:", os.path.basename(src))
                    continue
                dest = os.path.join(FINAL, os.path.relpath(src, os.path.join(ROOT, "extract")))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "wb").write(data)
            print(f"built city_poi_decals_atlas_{L} x{len(srcs[L])}")


if __name__ == "__main__":
    main()
