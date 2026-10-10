"""Rebrand the 365 variant of every shader-tinted ("pack_maskrgba") sign.

A tinted sign = mask texture (where each ink goes, channels R/G/B/A, layered over a base in
that order) + ink colours stored per variant in the sign model's material blocks:
  base d413b073   R 2ce6ce9c   G e81544ff   B 41157c29   A 26159464
For each target we set the 365 variant's inks to the brand's and redraw only the 365 area of
the mask. Models are rebuilt so they pack to exactly their original compressed length.

Usage: python tools/brand_masks.py lawson
"""
import glob
import itertools
import os
import re
import struct
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import brand
import fh6minizip
import install
import swatch

ROOT = brand.ROOT
KEY_RE = rb"environment_signage(?:_emissive)?\.materialbin"
INK = {"base": b"\xd4\x13\xb0\x73", "R": b"\x2c\xe6\xce\x9c", "G": b"\xe8\x15\x44\xff",
       "B": b"\x41\x15\x7c\x29", "A": b"\x26\x15\x94\x64"}

# 365 variants: model, mask texture, variant block, 365 area (x0, y0, x1, y1 in the largest
# mask; None = detect the top strip), layout.
TARGETS = [
    ("sgn_gbl_shop_hrzntl_6m_01_a", "sgn_gbl_shop_hrzntl_6m_01_a7", 14, None, "strip"),
    ("sgn_gbl_shop_vinyl_3m_01_a", "sgn_gbl_shop_vinyl_3m_01_a7", 14, None, "strip"),
    ("sgn_gbl_shops_vinyl_6m_01_a", "sgn_gbl_shops_vinyl_6m_01_a5", 2, None, "strip"),
    ("sgn_gbl_shop_square_01_a", "sgn_gbl_shop_square_01_a6", 16, (0, 0, 256, 256), "square"),
]

WHITE = (255, 255, 255)
BRANDS = {
    "lawson": {"blue": (0, 104, 183), "pink": (240, 160, 190), "logo": "lawson_logo.png"},
}


# ---------------------------------------------------------------- model inks

def _srgb(c):
    return int(round(255 * ((1.055 * max(c, 0) ** (1 / 2.4) - 0.055) if c > 0.0031308 else 12.92 * c)))


def _linear(rgb):
    out = []
    for c in rgb:
        c /= 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def block_bounds(data, index):
    starts = [m.start() for m in re.finditer(KEY_RE, data)]
    st = starts[index]
    en = starts[index + 1] if index + 1 < len(starts) else len(data)
    return st, en


def ink_slot(data, st, en, ink):
    m = next(re.finditer(rb"\x03\x04" + re.escape(INK[ink]) + rb"\x01.{20}.", data[st:en], re.S), None)
    return st + m.end() if m else None


def ink_colour(data, slot):
    return tuple(_srgb(x) for x in struct.unpack_from("<3f", data, slot))


def _float_options(data, v, tol=0.04):
    exact = struct.pack("<f", v)
    opts = [exact]
    for mask in (0xFFFF0000, 0xFFFFFF00, 0xFFF00000):
        bits = (struct.unpack("<I", exact)[0] + ((~mask & 0xFFFFFFFF) + 1) // 2) & mask
        opts.append(struct.pack("<I", bits))
    seen = set()
    for i in range(0, len(data) - 3, 4):
        f = struct.unpack_from("<f", data, i)[0]
        if abs(f - v) <= tol * max(v, 0.02) and data[i:i + 4] not in seen:
            seen.add(data[i:i + 4])
            opts.append(data[i:i + 4])
    uniq = []
    for o in opts:
        if o not in uniq:
            uniq.append(o)
    return sorted(uniq, key=lambda o: abs(struct.unpack("<f", o)[0] - v))[:3]


def _existing_records(data, rgb, max_dist=20):
    """Whole RGB float triples already in the file close to rgb (compress almost for free)."""
    out = []
    for m in re.finditer(rb"\x03\x04.{4}\x01.{20}.", data, re.S):
        v = data[m.end():m.end() + 16]
        if len(v) < 16:
            continue
        f = struct.unpack("<4f", v)
        if all(0 <= x <= 1.0001 for x in f) and abs(f[3] - 1) < 1e-4:
            if sum((_srgb(x) - t) ** 2 for x, t in zip(f[:3], rgb)) ** 0.5 <= max_dist and v[:12] not in out:
                out.append(v[:12])
    return out


def recolour(data, block, inks, target_len):
    """Set ink colours in one variant block so the model packs to exactly target_len."""
    st, en = block_bounds(data, block)
    slots = {k: ink_slot(data, st, en, k) for k in inks}
    missing = [k for k, s in slots.items() if s is None]
    if missing:
        raise ValueError(f"block {block} has no ink record for {missing}")
    order = list(inks)
    targets = {k: _linear(inks[k]) for k in order}
    options = {}
    for k in order:
        opts = _existing_records(data, inks[k])
        opts += [b"".join(c) for c in itertools.product(*[_float_options(data, v) for v in targets[k]])]
        options[k] = opts

    def err(blob, target):
        return sum(abs(struct.unpack_from("<f", blob, i * 4)[0] - t) for i, t in enumerate(target))

    one = struct.pack("<f", 1.0)
    combos = sorted(itertools.product(*[options[k] for k in order]),
                    key=lambda c: sum(err(v, targets[k]) for v, k in zip(c, order)))
    for combo in combos[:30000]:
        out = bytearray(data)
        for k, val in zip(order, combo):
            out[slots[k]:slots[k] + 16] = val + one
        out = bytes(out)
        try:
            install.lz4_exact(out, target_len, exact_only=True)
            return out
        except ValueError:
            continue
    raise ValueError("no colour encoding packs to the exact original length")


# ---------------------------------------------------------------- mask drawing

def detect_strip(mask):
    """Top strip holding the 365 design: from the first inked row down to a clear gap."""
    ink = (mask[..., 1:4] > 16).any(axis=2).any(axis=1)  # low threshold: include anti-aliased edges
    rows = np.where(ink)[0]
    y0 = max(0, int(rows[0]) - 1)
    y = y0
    gap = 0
    while y < mask.shape[0] and gap < 10:
        gap = 0 if ink[y] else gap + 1
        y += 1
    return y0, min(mask.shape[0], y - gap + 1)


def wordmark(brand_cfg, colour, box_w, box_h):
    logo = Image.open(os.path.join(brand.ASSETS, brand_cfg["logo"])).convert("RGBA")
    a = np.asarray(logo).copy()
    a[..., :3] = colour
    logo = Image.fromarray(a)
    logo.thumbnail((box_w, box_h), Image.LANCZOS)
    return logo


def design_strip(w, h, cfg, scale=4):
    W, H = w * scale, h * scale
    a = np.zeros((H, W, 3), np.uint8)
    a[:] = WHITE
    for top, bottom, col in ((0.23, 0.70, cfg["blue"]), (0.82, 0.89, cfg["pink"])):
        a[round(top * H): round(bottom * H)] = col
    half = int(W * 0.18)
    a[:, W // 2 - half: W // 2 + half] = WHITE
    img = Image.fromarray(a)
    logo = wordmark(cfg, cfg["blue"], int(2 * half * 0.9), int(H * 0.5))
    img.paste(logo, (W // 2 - logo.width // 2, (H - logo.height) // 2), logo)
    return img


def design_square(w, h, cfg, scale=4):
    W, H = w * scale, h * scale
    img = Image.new("RGB", (W, H), cfg["blue"])
    a = np.asarray(img).copy()
    a[int(H * 0.80): int(H * 0.86)] = cfg["pink"]
    img = Image.fromarray(a)
    logo = wordmark(cfg, WHITE, int(W * 0.84), int(H * 0.3))
    img.paste(logo, ((W - logo.width) // 2, int(H * 0.42) - logo.height // 2), logo)
    return img


def to_channels(design, cfg, scale=4):
    """White -> R only; blue -> G; pink -> B; A unused. Soft edges via supersampling."""
    a = np.asarray(design).astype(np.float32)
    inks = np.array([WHITE, cfg["blue"], cfg["pink"]], np.float32)
    idx = ((a[:, :, None, :] - inks[None, None]) ** 2).sum(-1).argmin(-1)
    h, w = idx.shape[0] // scale, idx.shape[1] // scale
    g = (idx == 1).astype(np.float32).reshape(h, scale, w, scale).mean(axis=(1, 3))
    b = (idx == 2).astype(np.float32).reshape(h, scale, w, scale).mean(axis=(1, 3))
    return g, b


# ---------------------------------------------------------------- main

def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "lawson"
    cfg = BRANDS[name]
    out_root = os.path.join(ROOT, "build", name)
    lookup = install.chunk_lookup()
    with tempfile.TemporaryDirectory() as tmp:
        for model, mask_name, block, area, layout in TARGETS:
            # 1) inks in every LOD/cluster file of the model
            inks = {"R": WHITE, "G": cfg["blue"], "B": cfg["pink"]}
            for fname, (c, i) in sorted(lookup.items()):
                if not (fname.startswith(model + "_cluster") and fname.endswith(".modelbin")):
                    continue
                orig = install.original_entry(c, i)
                mz = fh6minizip.MiniZip(os.path.join(install.TRACK, f"GeoChunk{c}.minizip"))
                off, size, flags, _, stored = mz.entries[i]
                if flags & 0xFF != 0x1F:
                    raise ValueError(f"{fname}: unexpected codec {flags:#x}")
                bk = os.path.join(install.BACKUP, f"GeoChunk{c}_{i}_{off:x}.bin")
                slot = open(bk, "rb").read() if os.path.exists(bk) else (mz.f.seek(off), mz.f.read(stored))[1]
                target = len(slot) - install.lz4_padding(slot, size)
                st, en = block_bounds(orig, block)
                before = {k: ink_colour(orig, ink_slot(orig, st, en, k)) for k in ("R", "G", "B")}
                new = recolour(orig, block, inks, target)
                rel = [n for n in fh6minizip.load_names(os.path.join(install.TRACK, f"ChunkContentsMiniZip{c}.txt")).values()
                       if n.endswith("/" + fname)][0]
                dest = os.path.join(out_root, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "wb").write(new)
                print(f"built {fname}  block {block} inks {before} -> lawson")
            # 2) mask: redraw the 365 area in every quality version
            srcs = [f for f in glob.glob(os.path.join(ROOT, "extract", "**", f"{mask_name}_pack_maskrgba_*.pb"), recursive=True)]
            big = max(srcs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
            full = np.asarray(swatch.to_image(open(big, "rb").read())[0]).copy()
            if area is None:
                y0, y1 = detect_strip(full)
                x0, x1 = 0, full.shape[1]
            else:
                x0, y0, x1, y1 = area
            w, h = x1 - x0, y1 - y0
            design = (design_strip if layout == "strip" else design_square)(w, h, cfg)
            g, b = to_channels(design, cfg)
            full[y0:y1, x0:x1, 0] = 255
            full[y0:y1, x0:x1, 1] = (g * 255).round()
            full[y0:y1, x0:x1, 2] = (b * 255).round()
            full[y0:y1, x0:x1, 3] = 0
            design.resize((w, h), Image.LANCZOS).save(os.path.join(ROOT, "preview", f"masks_{name}_{mask_name}.png"))
            new_full = Image.fromarray(full, "RGBA")
            for src in srcs:
                orig = open(src, "rb").read()
                inf = swatch.parse(orig)
                img = Image.merge("RGBA", [ch.resize((inf["width"], inf["height"]), Image.LANCZOS)
                                           for ch in new_full.split()])
                data = brand.encode(img, orig, tmp, keep_alpha=False)
                rel = os.path.relpath(src, os.path.join(ROOT, "extract"))
                dest = os.path.join(out_root, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "wb").write(data)
            print(f"built {mask_name} mask x{len(srcs)}  area {(x0, y0, x1, y1)}")


if __name__ == "__main__":
    main()
