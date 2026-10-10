"""Rebrand shader-tinted ("pack_maskrgba") shop signs.

These signs are drawn from a mask texture whose channels say where each of four inks
go, and the ink colours live in the sign model's material variant block:
  R -> param 2ce6ce9c (base, white)   G -> e81544ff   B -> 41157c29   A -> 26159464
For the 365 variant of sgn_gbl_shop_hrzntl_6m_01_a (yellow/red/blue) we recolour the inks
to 7-Eleven orange/red/green and redraw the 365 strip of mask a7.

Usage: python tools/brand_mask.py 7eleven
"""
import glob
import os
import re
import struct
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import brand
import brand_station
import fh6minizip
import install
import swatch

ROOT = brand.ROOT
TRACK = os.path.join(os.path.dirname(ROOT), "media", "Tracks", "Brio")

INK_G, INK_B, INK_A = b"\xe8\x15\x44\xff", b"\x41\x15\x7c\x29", b"\x26\x15\x94\x64"
YELLOW_365 = struct.pack("<4f", 0.8631572127342224, 0.6795424818992615, 0.021219011396169662, 1.0)

ORANGE, RED, GREEN, WHITE = (245, 130, 31), (237, 27, 45), (0, 128, 97), (255, 255, 255)


def linear(rgb):
    """Linear float4 colour, rounded so each float's low 16 bits are zero. The change is
    invisible but compresses better, which matters because the model must fit its slot."""
    out = []
    for c in rgb:
        c /= 255
        v = c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        bits = (struct.unpack("<I", struct.pack("<f", v))[0] + 0x8000) & 0xFFFF0000
        out.append(struct.unpack("<f", struct.pack("<I", bits))[0])
    return struct.pack("<4f", *out, 1.0)


def _srgb(c):
    return int(round(255 * ((1.055 * c ** (1 / 2.4) - 0.055) if c > 0.0031308 else 12.92 * c)))


def existing_colour(data, rgb, max_dist=20):
    """A float4 colour already present in this model close to rgb, or None.
    Reusing exact bytes costs almost nothing after compression, which keeps the
    model inside its fixed-size slot."""
    best, best_d = None, None
    for m in re.finditer(rb"\x03\x04.{4}\x01.{20}.", data, re.S):
        v = data[m.end():m.end() + 16]
        if len(v) < 16:
            continue
        f = struct.unpack("<4f", v)
        if not (all(0 <= x <= 1.0001 for x in f) and abs(f[3] - 1) < 1e-4):
            continue
        dist = sum((_srgb(x) - t) ** 2 for x, t in zip(f[:3], rgb)) ** 0.5
        if best_d is None or dist < best_d:
            best, best_d = v, dist
    return best if best_d is not None and best_d <= max_dist else None


def _float_options(data, v, tol=0.04):
    """Byte encodings of a colour component close to v: exact, rounded, or a float already in the file."""
    exact = struct.pack("<f", v)
    opts = [exact]
    for mask in (0xFFFF0000, 0xFFFFFF00, 0xFFF00000):
        bits = (struct.unpack("<I", exact)[0] + ((~mask & 0xFFFFFFFF) + 1) // 2) & mask
        opts.append(struct.pack("<I", bits))
    for m in re.finditer(rb"(?s).{4}", data[: len(data) // 4 * 4]):
        pass
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
    return sorted(uniq, key=lambda o: abs(struct.unpack("<f", o)[0] - v))[:4]


def _linear_components(rgb):
    out = []
    for c in rgb:
        c /= 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def recolour_model(data, target_len=None, inks=None):
    """Change the inks of the material block that holds the 365 yellow.

    inks: {INK_x: (r, g, b)} - only these records change. The game only accepts an archive
    entry whose LZ4 block has exactly the original compressed length, so when target_len is
    given we try tiny, invisible variations of the colours (and reuse of colours already in
    the file) until the model can be packed at exactly that length."""
    import itertools
    inks = inks or {INK_G: ORANGE, INK_A: GREEN}
    key = b"environment_signage_emissive.materialbin"
    starts = [m.start() for m in re.finditer(re.escape(key), data)]
    pos = data.find(YELLOW_365)
    if pos < 0:
        raise ValueError("365 colour block not found")
    start = max(s for s in starts if s < pos)
    end = min([s for s in starts if s > pos] + [len(data)])
    slots, options, targets = {}, {}, {}
    for ink, rgb in inks.items():
        m = next(re.finditer(rb"\x03\x04" + re.escape(ink) + rb"\x01.{20}.", data[start:end], re.S))
        slots[ink] = start + m.end()
        targets[ink] = _linear_components(rgb)
        opts = [b"".join(c) for c in itertools.product(*[_float_options(data, v) for v in targets[ink]])]
        reuse = existing_colour(data, rgb)
        if reuse:
            opts.insert(0, reuse[:12])  # an existing colour record compresses almost for free
        options[ink] = opts

    def err(blob, target):
        return sum(abs(struct.unpack_from("<f", blob, k * 4)[0] - t) for k, t in enumerate(target))

    one = struct.pack("<f", 1.0)
    order = list(inks)
    combos = sorted(itertools.product(*[options[k] for k in order]),
                    key=lambda c: sum(err(v, targets[k]) for v, k in zip(c, order)))
    for combo in combos[:20000]:
        out = bytearray(data)
        for ink, val in zip(order, combo):
            out[slots[ink]:slots[ink] + 16] = val + one
        out = bytes(out)
        if target_len is None:
            return out
        try:
            install.lz4_exact(out, target_len, exact_only=True)
            return out
        except ValueError:
            continue
    raise ValueError("no colour encoding compresses to the exact original length")


def strip_bounds(mask):
    """Rows and centre-panel columns of the 365 strip at the top of mask a7."""
    g = mask[..., 1] > 128
    ink = (mask[..., 1:4] > 24).any(axis=2)
    top = np.where(g.any(axis=1))[0][0]
    y0 = top
    while y0 > 0 and ink[y0 - 1].any():  # include anti-aliased tops of the lettering
        y0 -= 1
    y1 = y0
    while y1 + 1 < mask.shape[0] and (g[y1 + 1].any() or (mask[y1 + 1, :, 3] > 128).any()) and y1 - y0 < 200:
        y1 += 1
    cols = np.where(~g[(y0 + y1) // 2])[0]
    mid = mask.shape[1] // 2
    gap = cols[(cols > mid - 300) & (cols < mid + 300)]
    return int(y0), int(y1) + 1, int(gap.min()), int(gap.max()) + 1


def design_7eleven(w, h, px0, px1, scale=4):
    """RGB design of the strip at `scale`x, using only the four inks."""
    W, H = w * scale, h * scale
    img = Image.new("RGB", (W, H), WHITE)
    a = np.asarray(img).copy()
    for top, bottom, col in ((0.03, 0.23, ORANGE), (0.315, 0.62, GREEN), (0.72, 0.95, RED)):
        a[round(top * H): round(bottom * H)] = col
    a[:, px0 * scale: px1 * scale] = WHITE
    img = Image.fromarray(a)
    logo = brand_station.clean_logo(os.path.join(brand.ASSETS, "7eleven_panel_logo.png"))
    logo.thumbnail(((px1 - px0) * scale - 8 * scale, int(H * 0.96)), Image.LANCZOS)
    img.paste(logo, (px0 * scale + ((px1 - px0) * scale - logo.width) // 2, (H - logo.height) // 2))
    return img


def to_masks(design, palette, scale=4):
    """palette: [base, G ink, B ink, A ink] colours (None = unused). Nearest-ink
    classification at high res, box-filtered down to soft G/B/A channel masks."""
    a = np.asarray(design).astype(np.float32)
    used = [(k, c) for k, c in enumerate(palette) if c is not None]
    inks = np.array([c for _, c in used], np.float32)
    idx = np.array([k for k, _ in used])[((a[:, :, None, :] - inks[None, None]) ** 2).sum(-1).argmin(-1)]
    h, w = idx.shape[0] // scale, idx.shape[1] // scale
    return [(idx == k).astype(np.float32).reshape(h, scale, w, scale).mean(axis=(1, 3)) for k in (1, 2, 3)]


LAWSON_BLUE, LAWSON_PINK = (0, 104, 183), (240, 160, 190)


def design_lawson(w, h, px0, px1, scale=4):
    """White fascia, thick Lawson-blue stripe, pink pinstripe, wide white wordmark panel."""
    W, H = w * scale, h * scale
    img = Image.new("RGB", (W, H), WHITE)
    a = np.asarray(img).copy()
    for top, bottom, col in ((0.23, 0.70, LAWSON_BLUE), (0.82, 0.89, LAWSON_PINK)):
        a[round(top * H): round(bottom * H)] = col
    cx = (px0 + px1) // 2
    half = int((px1 - px0) * 0.82)  # wider panel than the 365 one: the wordmark is wide
    a[:, (cx - half) * scale:(cx + half) * scale] = WHITE
    img = Image.fromarray(a)
    logo = Image.open(os.path.join(brand.ASSETS, "lawson_logo.png")).convert("RGBA")
    # flatten to pure Lawson blue so it maps onto the blue ink
    la = np.asarray(logo).copy()
    la[..., :3] = LAWSON_BLUE
    logo = Image.fromarray(la)
    logo.thumbnail((int(2 * half * scale * 0.9), int(H * 0.5)), Image.LANCZOS)
    img.paste(logo, ((cx * scale) - logo.width // 2, (H - logo.height) // 2), logo)
    return img


BRANDS = {
    # name: (model inks to change, design fn, palette [base, G, B, A])
    "7eleven": ({INK_G: ORANGE, INK_A: GREEN}, None, [WHITE, ORANGE, RED, GREEN]),
    "lawson": ({INK_G: LAWSON_BLUE, INK_B: LAWSON_PINK}, design_lawson, [WHITE, LAWSON_BLUE, LAWSON_PINK, None]),
}


def main():
    brand_name = sys.argv[1] if len(sys.argv) > 1 else "7eleven"
    inks, design_fn, palette = BRANDS[brand_name]
    design_fn = design_fn or design_7eleven
    out_root = os.path.join(ROOT, "build", brand_name)

    # 1) Models: recolour the 365 variant's inks.
    for c in range(4):
        names = fh6minizip.load_names(os.path.join(TRACK, f"ChunkContentsMiniZip{c}.txt"))
        mz = fh6minizip.MiniZip(os.path.join(TRACK, f"GeoChunk{c}.minizip"))
        for i, n in names.items():
            if "sgn_gbl_shop_hrzntl_6m_01_a_cluster" in n and n.endswith(".modelbin"):
                orig = install.original_entry(c, i)  # true original even if already patched
                if YELLOW_365 not in orig:
                    continue
                dest = os.path.join(out_root, n)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                e = mz.entries[i]
                mz.f.seek(e[0])
                slot = mz.f.read(e[4])
                target = len(slot) - install.lz4_padding(slot, e[1]) if e[2] & 0xFF == 0x1F else None
                built = recolour_model(orig, target, inks)  # compute first so a failure never truncates
                open(dest, "wb").write(built)
                print("built", os.path.basename(n))

    # 2) Mask a7: redraw the 365 strip.
    sources = glob.glob(os.path.join(ROOT, "extract", "**", "sgn_gbl_shop_hrzntl_6m_01_a7_pack_maskrgba_*.pb"),
                        recursive=True)
    big = max(sources, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
    full = np.asarray(swatch.to_image(open(big, "rb").read())[0]).copy()
    y0, y1, px0, px1 = strip_bounds(full)
    print(f"365 strip rows {y0}-{y1}, centre panel x {px0}-{px1}")
    w, h = full.shape[1], y1 - y0
    design = design_fn(w, h, px0, px1)
    g, b, a = to_masks(design, palette)
    full[y0:y1, :, 0] = 255
    full[y0:y1, :, 1] = (g * 255).round()
    full[y0:y1, :, 2] = (b * 255).round()
    full[y0:y1, :, 3] = (a * 255).round()
    new_full = Image.fromarray(full, "RGBA")
    design.resize((w, h), Image.LANCZOS).save(os.path.join(ROOT, "preview", f"mask_{brand_name}_design.png"))
    with tempfile.TemporaryDirectory() as tmp:
        for src in sources:
            orig = open(src, "rb").read()
            i = swatch.parse(orig)
            # Resize each channel on its own: resizing an RGBA image treats A as transparency
            # and would wipe R/G/B wherever A is 0, but here A is just another ink mask.
            img = Image.merge("RGBA", [ch.resize((i["width"], i["height"]), Image.LANCZOS)
                                       for ch in new_full.split()])
            new = brand.encode(img, orig, tmp, keep_alpha=False)
            rel = os.path.relpath(src, os.path.join(ROOT, "extract"))
            dest = os.path.join(out_root, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(new)
            print(f"built {os.path.basename(dest)} {i['width']}x{i['height']}")


if __name__ == "__main__":
    main()
