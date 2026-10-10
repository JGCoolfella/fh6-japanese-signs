"""Rebrand the '365 Konbini' fascia (bld_gbl_comm_03_a_features *_bclr) as a real store.

Usage:  python tools/brand.py <brand> [--logo path/to/logo.png]
Brands: 7eleven, lawson, familymart
Writes rebuilt .pb textures to build/<brand>/... and a preview PNG.
"""
import argparse
import glob
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import swatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEXCONV = os.path.join(HERE, "texconv.exe")
FONTS = "C:/Windows/Fonts/"

# Layout of the fascia band in the 1024x1024 texture (scaled for smaller qualities).
BAND = (0, 0, 1024, 128)
LOGO = (418, 0, 606, 128)


def font(name, size):
    return ImageFont.truetype(FONTS + name, size)


def centered(draw, box, text, fnt, fill):
    l, t, r, b = draw.textbbox((0, 0), text, font=fnt)
    x = box[0] + (box[2] - box[0] - (r - l)) / 2 - l
    y = box[1] + (box[3] - box[1] - (b - t)) / 2 - t
    draw.text((x, y), text, font=fnt, fill=fill)


def fit_logo(path, box, bg):
    """Paste a user supplied logo into the logo box, keeping aspect ratio."""
    w, h = box[2] - box[0], box[3] - box[1]
    tile = Image.new("RGB", (w, h), bg)
    logo = Image.open(path).convert("RGBA")
    logo.thumbnail((int(w * 0.9), int(h * 0.9)), Image.LANCZOS)
    tile.paste(logo, ((w - logo.width) // 2, (h - logo.height) // 2), logo)
    return tile


ASSETS = os.path.join(ROOT, "assets")


def band_7eleven(logo_path=None):
    """Japanese 7-Eleven fascia, measured from a storefront photo (assets/ref)."""
    W, H = BAND[2], BAND[3]
    orange, green, red = (245, 130, 31), (0, 128, 97), (237, 27, 45)  # official logo colours
    img = Image.new("RGB", (W, H), (252, 252, 250))
    d = ImageDraw.Draw(img)
    # Stripe bands as fractions of the fascia height: orange, gap, green (widest), gap, red.
    for top, bottom, col in ((0.03, 0.23, orange), (0.315, 0.62, green), (0.72, 0.95, red)):
        d.rectangle((0, round(top * H), W, round(bottom * H) - 1), fill=col)
    # Logo panel: plain white with the logo, stripes stop at its edges.
    lx0, ly0, lx1, ly1 = LOGO
    d.rectangle(LOGO, fill=(255, 255, 255))
    d.line((lx0, 0, lx0, H), fill=(205, 205, 205), width=2)
    d.line((lx1 - 1, 0, lx1 - 1, H), fill=(205, 205, 205), width=2)
    logo = Image.open(logo_path or os.path.join(ASSETS, "7eleven_panel_logo.png")).convert("RGB")
    a = np.asarray(logo).astype(np.int16)
    sat = a.max(axis=2) - a.min(axis=2)
    ys, xs = np.where(sat > 90)  # the 7 and the lettering only
    keep = np.zeros(sat.shape, bool)
    keep[ys.min():ys.max() + 1, xs.min():xs.max() + 1] = True
    # Inside the artwork keep anti-aliased edges; outside it, everything becomes white
    # (removes the faint outline left from the original background).
    a[~keep] = 255
    a[keep & (sat < 25)] = 255
    logo = Image.fromarray(a.astype(np.uint8))
    logo = logo.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    logo.thumbnail((lx1 - lx0 - 24, ly1 - ly0 - 10), Image.LANCZOS)
    img.paste(logo, (lx0 + (lx1 - lx0 - logo.width) // 2, ly0 + (ly1 - ly0 - logo.height) // 2))
    # Snap near-white resampling residue in the panel to pure white.
    p = np.asarray(img).astype(np.int16)
    panel = p[:, lx0 + 2: lx1 - 2]
    panel[(panel.min(axis=2) > 200) & (panel.max(axis=2) - panel.min(axis=2) < 40)] = 255
    return Image.fromarray(p.astype(np.uint8))


def band_lawson(logo_path=None):
    W, H = BAND[2], BAND[3]
    blue = (0, 104, 183)
    img = Image.new("RGB", (W, H), blue)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 112, W, 117), fill=(255, 255, 255))
    if logo_path:
        img.paste(fit_logo(logo_path, LOGO, blue), (LOGO[0], LOGO[1]))
        return img
    # Wide wordmark across the centre of the band, milk can icon to its left.
    centered(d, (300, 10, 724, 108), "LAWSON", font("arialbd.ttf", 74), (255, 255, 255))
    d.rounded_rectangle((250, 30, 290, 92), radius=8, outline=(255, 255, 255), width=5)
    d.rectangle((258, 22, 282, 32), fill=(255, 255, 255))
    return img


def band_familymart(logo_path=None):
    W, H = BAND[2], BAND[3]
    img = Image.new("RGB", (W, H), (250, 250, 247))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 22), fill=(0, 155, 72))
    d.rectangle((0, 106, W, 128), fill=(0, 104, 183))
    if logo_path:
        img.paste(fit_logo(logo_path, LOGO, (250, 250, 247)), (LOGO[0], LOGO[1]))
        return img
    f = font("arialbd.ttf", 56)
    d.text((330, 32), "Family", font=f, fill=(0, 104, 183))
    fw = d.textlength("Family", font=f)
    d.text((330 + fw, 32), "Mart", font=f, fill=(0, 155, 72))
    return img


BRANDS = {"7eleven": band_7eleven, "lawson": band_lawson, "familymart": band_familymart}


def weathered(band, original):
    """Multiply the new band by the original's fine detail (grime, scratches).

    Detail is sampled only from the plain strip left of the logo box and tiled across,
    so none of the old lettering or box edges carry over.
    """
    g = original.convert("L")
    o = np.asarray(g, np.float32) + 1
    blur = np.asarray(g.filter(ImageFilter.GaussianBlur(10)), np.float32) + 1
    s = original.width / 1024
    # Plain area: left of the logo box and above the original's thin stripes (y < 64).
    plain = (o / blur)[: int(64 * s), : int((LOGO[0] - 16) * s)]
    reps = -(-original.width // plain.shape[1])
    rows = np.concatenate([plain, plain[:, ::-1]] * reps, axis=1)[:, : original.width]
    vreps = -(-original.height // rows.shape[0])
    tiled = np.concatenate([rows, rows[::-1]] * vreps, axis=0)[: original.height]
    detail = np.clip(tiled, 0.93, 1.04)
    detail[:, int(LOGO[0] * s): int(LOGO[2] * s)] = 1.0  # keep the logo crisp
    detail = detail[..., None]
    out = np.asarray(band, np.float32) * detail
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def encode(img, orig_bytes, workdir, keep_alpha=True, base_bytes=None):
    """Encode img to the original's BC format and mip count, keeping its header.

    keep_alpha: reuse the original texture's alpha channel (it often carries cut-outs or
    material masks rather than transparency). Pass False when img's alpha is intentional."""
    info = swatch.parse(orig_bytes)
    if keep_alpha:
        orig_alpha = swatch.to_image(orig_bytes)[0].split()[3]
        img = Image.merge("RGBA", (*img.convert("RGB").split(), orig_alpha.resize(img.size)))
    name, block, _ = swatch.FORMATS[info["format"]]
    png = os.path.join(workdir, "in.png")
    img.save(png)
    subprocess.run([TEXCONV, "-nologo", "-y", "-f", f"{name}_UNORM", "-m", str(info["mips"]),
                    "-o", workdir, png], check=True, stdout=subprocess.DEVNULL)
    dds = open(os.path.join(workdir, "in.dds"), "rb").read()
    hdr = 148 if dds[84:88] == b"DX10" else 128
    pixels = dds[hdr:]
    expected = len(orig_bytes) - info["header_size"]
    if len(pixels) != expected:
        raise RuntimeError(f"pixel size {len(pixels)} != original {expected}")
    pixels = splice_unchanged(base_bytes or orig_bytes, pixels, info, img)
    return orig_bytes[:info["header_size"]] + pixels


def splice_unchanged(base_bytes, new_pixels, info, src_img, tol=2):
    """Keep the base texture's compressed 4x4 blocks wherever the picture did not change.

    Re-encoding untouched areas gives slightly different (and less compressible) blocks and
    archive slots are fixed-size, so those blocks are copied byte-for-byte from base_bytes
    (the original, or the current modded version). Mip 0 is compared against the source
    picture; smaller mips are compared decoded-vs-decoded with a little tolerance."""
    _, block, decode = swatch.FORMATS[info["format"]]
    base_pixels = base_bytes[info["header_size"]:]
    out = bytearray(new_pixels)
    w, h = info["width"], info["height"]
    src = np.asarray(src_img.convert("RGBA")).astype(np.int16)
    pos = 0
    for level in range(max(1, info["mips"])):
        bw, bh = max(1, (w + 3) // 4), max(1, (h + 3) // 4)
        size = bw * bh * block
        if pos + size > len(out) or pos + size > len(base_pixels):
            break
        dw, dh = bw * 4, bh * 4
        o = np.frombuffer(decode(base_pixels[pos:pos + size], dw, dh), np.uint8).reshape(dh, dw, 4)[..., [2, 1, 0, 3]].astype(np.int16)
        if level == 0 and src.shape[:2] == (h, w):
            n = np.zeros_like(o)
            n[:h, :w] = src
            n[h:, :] = o[h:, :]
            n[:, w:] = o[:, w:]
            t = tol
        else:
            n = np.frombuffer(decode(bytes(new_pixels[pos:pos + size]), dw, dh), np.uint8).reshape(dh, dw, 4)[..., [2, 1, 0, 3]].astype(np.int16)
            t = tol + 6
        if swatch.FORMATS[info["format"]][0] in ("BC1",):
            o[..., 3] = n[..., 3]  # BC1 alpha is not meaningful here
        diff = np.abs(o - n).reshape(bh, 4, bw, 4, 4).max(axis=(1, 3, 4))
        for by, bx in np.argwhere(diff <= t):
            k = pos + (by * bw + bx) * block
            out[k:k + block] = base_pixels[k:k + block]
        pos += size
        w, h = max(1, w // 2), max(1, h // 2)
    return bytes(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("brand", choices=BRANDS)
    ap.add_argument("--logo", help="optional logo PNG to place in the centre box")
    args = ap.parse_args()

    band = BRANDS[args.brand](args.logo)
    sources = sorted(glob.glob(os.path.join(ROOT, "extract", "**", "bld_gbl_comm_03_a_features_x*_bclr_*.pb"),
                           recursive=True))
    if not sources:
        sys.exit("Extract the textures first: python tools/fh6minizip.py ../media/Tracks/Brio '*bld_gbl_comm_03_a*' -o extract")
    out_root = os.path.join(ROOT, "build", args.brand)
    shutil.rmtree(out_root, ignore_errors=True)
    with tempfile.TemporaryDirectory() as tmp:
        for src in sources:
            orig = open(src, "rb").read()
            img, info = swatch.to_image(orig)
            img = img.convert("RGB")
            s = info["width"] / 1024
            box = tuple(int(v * s) for v in BAND)
            scaled = band.resize((box[2] - box[0], box[3] - box[1]), Image.LANCZOS)
            img.paste(weathered(scaled, img.crop(box)), box[:2])
            new = encode(img, orig, tmp)
            rel = os.path.relpath(src, os.path.join(ROOT, "extract"))
            dest = os.path.join(out_root, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(new)
            check, _ = swatch.to_image(new)
            if info["width"] == 1024:
                tag = "winter" if "xwinterx" in src else "summer"
                check.convert("RGB").save(os.path.join(ROOT, "preview", f"{args.brand}_{tag}.png"))
            print(f"built {os.path.basename(dest)} {info['width']}x{info['height']}")


if __name__ == "__main__":
    main()
