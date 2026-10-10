"""Neutralise the 365 store's yellow baked light (BC6H HDR lightmaps) so Lawson colours render true.

The konbini building's baked light/emission maps (bld_gbl_comm_03_a_lmbake_*, *_lightbake_plod_lmap) still
hold the original 365 sign's yellow glow. The game multiplies the sign colours by it, so Lawson blue showed
as green and white as yellow. Yellow light becomes white light of the same brightness.

  python tools/hdr_fix.py        (also run by build_all.py)
"""
import glob
import os
import struct
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import brand
import install
import swatch

ROOT = brand.ROOT
FINAL = os.path.join(ROOT, "build", "final")
STEMS = ["bld_gbl_comm_03_a_lmbake_emis", "bld_gbl_comm_03_a_lmbake_lmap", "bld_gbl_comm_03_a_lmbake_diff",
         "bld_gbl_comm_03_a_lightbake_plod_lmap"]
BC6H_UF16, R32G32B32A32_FLOAT = 95, 2


def dds(width, height, mips, dxgi, payload):
    flags = 0x1 | 0x2 | 0x4 | 0x1000 | (0x20000 if mips > 1 else 0)
    hdr = struct.pack("<4sIIIIIII44sII4s5I", b"DDS ", 124, flags, height, width, 0, 1, mips, b"\0" * 44,
                      32, 0x4, b"DX10", 0, 0, 0, 0, 0)
    caps = struct.pack("<IIIII", 0x1000 | (0x400008 if mips > 1 else 0), 0, 0, 0, 0)
    dx10 = struct.pack("<IIIII", dxgi, 3, 0, 1, 0)
    return hdr + caps + dx10 + payload


def texconv(args, cwd):
    os.makedirs(args[args.index("-o") + 1], exist_ok=True)
    subprocess.run([brand.TEXCONV, "-nologo", "-y", *args], check=True, stdout=subprocess.DEVNULL, cwd=cwd)


def decode_levels(bc_bytes, info, tmp):
    """All mip levels as float32 RGBA arrays (via texconv)."""
    path = os.path.join(tmp, "in.dds")
    open(path, "wb").write(dds(info["width"], info["height"], info["mips"], BC6H_UF16, bc_bytes))
    texconv(["-f", "R32G32B32A32_FLOAT", "-m", str(info["mips"]), "-o", os.path.join(tmp, "f"), path], tmp)
    d = open(os.path.join(tmp, "f", "in.dds"), "rb").read()
    pos = 148 if d[84:88] == b"DX10" else 128
    w, h, out = info["width"], info["height"], []
    for _ in range(info["mips"]):
        n = w * h * 16
        out.append(np.frombuffer(d[pos:pos + n], np.float32).reshape(h, w, 4).copy())
        pos += n
        w, h = max(1, w // 2), max(1, h // 2)
    return out


FASCIA_LIGHT = 0.5          # the sign light boxes were baked at ~2x; at 1x Lawson blue renders as itself, not cyan
# white-lit fascia segment (centre of the store front), as a fraction of the map: x0, y0, x1, y1
WHITE_FASCIA = [(239 / 512, 170 / 512, 316 / 512, 185 / 512)]


def neutralise(a):
    """Yellow light (blue far below red/green) -> white light; sign light boxes toned down. Returns changed mask."""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    rg = np.minimum(r, g)
    yellow = (rg > 0.02) & (b < 0.6 * rg) & (np.abs(r - g) < 0.35 * np.maximum(r, g))
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    for k in range(3):
        a[..., k] = np.where(yellow, lum * FASCIA_LIGHT, a[..., k])
    h, w = a.shape[:2]
    for x0, y0, x1, y1 in WHITE_FASCIA:
        sl = (slice(int(y0 * h), max(int(y0 * h) + 1, round(y1 * h))), slice(int(x0 * w), max(int(x0 * w) + 1, round(x1 * w))))
        lit = a[sl][..., :3].max(-1) > 0.5
        a[sl][..., :3][lit] *= FASCIA_LIGHT
        yellow[sl] |= lit
    return yellow


def encode_levels(levels, info, tmp):
    payload = b"".join(l.astype(np.float32).tobytes() for l in levels)
    path = os.path.join(tmp, "hdr.dds")
    open(path, "wb").write(dds(info["width"], info["height"], info["mips"], R32G32B32A32_FLOAT, payload))
    texconv(["-f", "BC6H_UF16", "-m", str(info["mips"]), "-o", os.path.join(tmp, "o"), path], tmp)
    d = open(os.path.join(tmp, "o", "hdr.dds"), "rb").read()
    return d[148 if d[84:88] == b"DX10" else 128:]


def fix(src):
    orig = open(src, "rb").read()
    info = swatch.parse(orig)
    if info["format"] != 7:
        print("   not BC6H:", os.path.basename(src)); return
    hs = info["header_size"]
    bc = orig[hs:]
    with tempfile.TemporaryDirectory() as tmp:
        levels = decode_levels(bc, info, tmp)
        masks = [neutralise(l) for l in levels]
        if not masks[0].any():
            print("   no yellow light in", os.path.basename(src)); return
        new = bytearray(encode_levels(levels, info, tmp))
    if len(new) < len(bc):
        new += bc[len(new):]
    new = new[:len(bc)]
    # keep original blocks wherever nothing changed (smaller, and byte-identical to the original)
    pos, w, h = 0, info["width"], info["height"]
    for m in masks:
        bw, bh = max(1, (w + 3) // 4), max(1, (h + 3) // 4)
        mm = np.zeros((bh * 4, bw * 4), bool)
        mm[:m.shape[0], :m.shape[1]] = m
        changed = mm.reshape(bh, 4, bw, 4).any(axis=(1, 3))
        for by in range(bh):
            for bx in range(bw):
                if not changed[by, bx]:
                    k = pos + (by * bw + bx) * 16
                    new[k:k + 16] = bc[k:k + 16]
        pos += bw * bh * 16
        w, h = max(1, w // 2), max(1, h // 2)
    data = orig[:hs] + bytes(new)
    if not install.fits_slot(os.path.basename(src), data):
        print("   too big for its slot, skipped:", os.path.basename(src)); return
    dest = os.path.join(FINAL, os.path.relpath(src, os.path.join(ROOT, "extract")))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(data)
    print(f"   fixed {os.path.basename(src)[-46:]} ({int(masks[0].sum())} yellow texels)")


def main():
    for stem in STEMS:
        for src in sorted(glob.glob(os.path.join(ROOT, "extract", "**", stem + "_*.pb"), recursive=True)):
            fix(src)


if __name__ == "__main__":
    main()
