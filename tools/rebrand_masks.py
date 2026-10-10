"""Rebrand variants of shader-tinted ("pack_maskrgba") signs, stacking on build/final.

A tinted sign = mask texture (channels R/G/B/A say where each ink goes, layered over a base
colour in the order base < R < G < B < A) + per-variant ink colours stored in the sign
model's material blocks. Each job redraws one atlas cell of one mask sheet and makes the
variant's inks show the brand's colours.

Model slots in the archive are fixed-size with only a few bytes of slack, so ink changes
are planned per model:
  * every design colour is first matched to a layer that already has that colour (no change)
  * otherwise a layer is recoloured, preferring a colour value that already exists somewhere
    in the same model file (repeated bytes compress almost for free)
  * then colours are upgraded to the exact brand values while the model still fits.

Job: (model stem, mask stem, variant block, area, design)
  area   = (x0, y0, x1, y1) pixels in the largest mask, or ("cell", col, row, cols, rows)
  design = {"colours": {name: rgb}, "bg": name,
            "bands": [(start, end, name), ...],               # horizontal, fractions of height
            "panel": (x0, x1, name),                          # optional vertical panel
            "logo": file, "logo_colour": name | None (None = logo's own colours),
            "logo_box": (x0, y0, x1, y1) fractions, "rotate": 0, "squash": 1.0}
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
FINAL = os.path.join(ROOT, "build", "final")
KEY_RE = rb"environment_signage\w*\.materialbin"  # incl. _emissive, _emissive_animated, _mural
LAYERS = ["base", "R", "G", "B", "A"]
INK = {"base": b"\xd4\x13\xb0\x73", "R": b"\x2c\xe6\xce\x9c", "G": b"\xe8\x15\x44\xff",
       "B": b"\x41\x15\x7c\x29", "A": b"\x26\x15\x94\x64"}
SAME = 50      # colours this close count as "already right" (sRGB distance)
REUSE = 48     # an existing file colour this close may stand in for the brand colour


# ---------------------------------------------------------------- colour helpers

def srgb8(c):
    return int(round(255 * ((1.055 * max(c, 0) ** (1 / 2.4) - 0.055) if c > 0.0031308 else 12.92 * c)))


def linear(rgb):
    out = []
    for c in rgb:
        c /= 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def blocks(data):
    starts = [m.start() for m in re.finditer(KEY_RE, data)]
    return [(st, starts[k + 1] if k + 1 < len(starts) else len(data)) for k, st in enumerate(starts)]


def layer_slots(data, block):
    st, en = blocks(data)[block]
    out = {}
    for name, key in INK.items():
        m = next(re.finditer(rb"\x03\x04" + re.escape(key) + rb"\x01.{20}.", data[st:en], re.S), None)
        if m:
            out[name] = st + m.end()
    return out


def slot_rgb(data, slot):
    return tuple(srgb8(x) for x in struct.unpack_from("<3f", data, slot))


def file_palette(data):
    """Every opaque float4 colour record in the model: {12-byte rgb floats: srgb8 tuple}."""
    pal = {}
    for m in re.finditer(rb"\x03\x04.{4}\x01.{20}.", data, re.S):
        v = data[m.end():m.end() + 16]
        if len(v) == 16:
            f = struct.unpack("<4f", v)
            if all(0 <= x <= 1.0001 for x in f) and abs(f[3] - 1) < 1e-4:
                pal[v[:12]] = tuple(srgb8(x) for x in f[:3])
    return pal


# ---------------------------------------------------------------- planning

def assign_layers(data, block, design, forced=None):
    """Map each design colour to a layer of this variant, minimising ink changes.
    forced: a mapping to reuse (variants sharing one mask cell must share the layout).
    Returns ({colour name: layer}, {layer: target rgb for layers that must change})."""
    slots = layer_slots(data, block)
    current = {L: slot_rgb(data, s) for L, s in slots.items()}
    if forced:
        missing = [L for L in forced.values() if L not in slots]
        if missing:
            raise ValueError(f"block {block} lacks ink layers {missing} needed by a shared cell")
        return forced, {L: design["colours"][n] for n, L in forced.items()
                        if dist(current[L], design["colours"][n]) > SAME}
    names = list(design["colours"])
    usable = [L for L in LAYERS if L in slots]
    best = None
    for perm in itertools.permutations(usable, len(names)):
        mapping = dict(zip(names, perm))
        bg_rank = LAYERS.index(mapping[design["bg"]])
        if any(LAYERS.index(L) < bg_rank for n, L in mapping.items() if n != design["bg"]):
            continue  # the background must sit below everything drawn on top of it
        changes = sum(1 for n, L in mapping.items() if dist(current[L], design["colours"][n]) > SAME)
        err = sum(min(dist(current[L], design["colours"][n]), SAME + 1) for n, L in mapping.items())
        key = (changes, err)
        if best is None or key < best[0]:
            best = (key, mapping)
    mapping = best[1]
    changes = {L: design["colours"][n] for n, L in mapping.items()
               if dist(current[L], design["colours"][n]) > SAME}
    return mapping, changes


def plan_model(data, requests, target_len):
    """requests: [(block, layer, rgb)]. Choose byte values for every ink change so the model
    packs to exactly target_len. Starts with the cheapest (reused) values and upgrades to
    exact brand colours while it still fits."""
    pal = file_palette(data)
    slots = [(layer_slots(data, b)[L], rgb) for b, L, rgb in requests]
    one = struct.pack("<f", 1.0)

    def build(vals):
        out = bytearray(data)
        for (slot, _), v in zip(slots, vals):
            out[slot:slot + 16] = v + one
        return bytes(out)

    def fits(blob):
        try:
            install.lz4_exact(blob, target_len, exact_only=True)
            return True
        except ValueError:
            return False

    exact = [struct.pack("<3f", *linear(rgb)) for _, rgb in slots]
    vals = None
    for limit in (REUSE, 80, 120):  # progressively looser reuse of colours already in the file
        reuse = [[v for _, v in sorted((dist(c, rgb), v) for v, c in pal.items() if dist(c, rgb) <= limit)]
                 for _, rgb in slots]
        trial = [r[0] if r else e for r, e in zip(reuse, exact)]
        if fits(build(trial)):
            vals = trial
            break
        for k in range(len(slots)):
            for alt in reuse[k][1:]:
                t2 = trial[:k] + [alt] + trial[k + 1:]
                if fits(build(t2)):
                    vals = t2
                    break
            if vals:
                break
        if vals:
            break
    if vals is None:
        raise ValueError(f"ink changes do not fit this model's slot ({len(slots)} changes)")
    # upgrade to exact brand colours where it still fits, biggest colour error first
    def err(k):
        got = pal.get(vals[k]) or tuple(srgb8(x) for x in struct.unpack("<3f", vals[k]))
        return dist(got, slots[k][1])
    for k in sorted(range(len(slots)), key=lambda k: -err(k)):
        if vals[k] == exact[k]:
            continue
        trial = vals[:k] + [exact[k]] + vals[k + 1:]
        if fits(build(trial)):
            vals = trial
    used = [pal.get(v) or tuple(srgb8(x) for x in struct.unpack("<3f", v)) for v in vals]
    return build(vals), used


# ---------------------------------------------------------------- mask drawing

def draw(w, h, d, scale=4):
    W, H = w * scale, h * scale
    C = d["colours"]
    a = np.zeros((H, W, 3), np.uint8)
    a[:] = C[d["bg"]]
    for s, e, n in d.get("bands", []):
        a[round(s * H): round(e * H)] = C[n]
    if "panel" in d:
        p0, p1, n = d["panel"]
        a[:, round(p0 * W): round(p1 * W)] = C[n]
    img = Image.fromarray(a)
    if d.get("logo"):
        logo = Image.open(os.path.join(brand.ASSETS, d["logo"])).convert("RGBA")
        if d.get("logo_colour"):
            la = np.asarray(logo).copy()
            la[..., :3] = C[d["logo_colour"]]
            logo = Image.fromarray(la)
        if d.get("rotate"):
            logo = logo.rotate(d["rotate"], expand=True)
        bx0, by0, bx1, by1 = d.get("logo_box", (0.1, 0.25, 0.9, 0.75))
        bw, bh = int((bx1 - bx0) * W), int((by1 - by0) * H)
        sq = d.get("squash", 1.0)
        k = min(int(bw * sq) / logo.width, bh / logo.height)
        logo = logo.resize((max(1, round(logo.width * k)), max(1, round(logo.height * k))), Image.LANCZOS)
        if sq != 1.0:
            logo = logo.resize((max(1, round(logo.width / sq)), logo.height), Image.LANCZOS)
        img.paste(logo, (int(bx0 * W) + (bw - logo.width) // 2, int(by0 * H) + (bh - logo.height) // 2), logo)
    return img


def channels(design_img, d, mapping, scale=4):
    """Classify pixels to design colours -> layers; return R,G,B,A masks (0..1) that
    reproduce the coverage under over-compositing (base < R < G < B < A)."""
    a = np.asarray(design_img).astype(np.float32)
    names = list(d["colours"])
    cols = np.array([d["colours"][n] for n in names], np.float32)
    idx = ((a[:, :, None, :] - cols[None, None]) ** 2).sum(-1).argmin(-1)
    h, w = idx.shape[0] // scale, idx.shape[1] // scale
    cov = {L: np.zeros((h, w), np.float32) for L in LAYERS}
    for k, n in enumerate(names):
        cov[mapping[n]] += (idx == k).astype(np.float32).reshape(h, scale, w, scale).mean(axis=(1, 3))
    masks = {}
    below = cov["base"].copy()
    bg_layer = mapping[d["bg"]]
    for L in LAYERS[1:]:
        total = below + cov[L]
        m = np.where(total > 0, cov[L] / np.maximum(total, 1e-6), 0)
        # where a higher layer fully covers the pixel this mask is "don't care": keep the
        # background layer solid (1) and others empty (0) - smooth channels compress better
        m = np.where(total > 1e-6, m, 1.0 if L == bg_layer else 0.0)
        masks[L] = m
        below = total
    return masks["R"], masks["G"], masks["B"], masks["A"]


# ---------------------------------------------------------------- main

def current_bytes(rel, extract_path):
    cur = os.path.join(FINAL, rel)
    return open(cur if os.path.exists(cur) else extract_path, "rb").read()


def resolve_area(area, mask):
    if area[0] == "cell":
        _, col, row, ncols, nrows = area
        Hm, Wm = mask.shape[:2]
        return (round((col - 1) * Wm / ncols), round((row - 1) * Hm / nrows),
                round(col * Wm / ncols), round(row * Hm / nrows))
    return area


def run(jobs):
    lookup = install.chunk_lookup()
    names_cache = {}

    def rel_of(c, i):
        if c not in names_cache:
            names_cache[c] = fh6minizip.load_names(os.path.join(install.TRACK, f"ChunkContentsMiniZip{c}.txt"))
        return names_cache[c][i]

    # ---- 1) plan inks per model (all jobs for that model together)
    models = []
    for j in jobs:
        if j[0] not in models:
            models.append(j[0])
    mappings = {}
    cell_maps = {}  # (mask, area) -> layer layout shared by every variant drawing that cell
    for model in models:
        files = sorted((f, lookup[f]) for f in lookup if f.startswith(model + "_cluster") and f.endswith(".modelbin"))
        mjobs = [j for j in jobs if j[0] == model]
        for fname, (c, i) in files:
            rel = rel_of(c, i)
            final_path = os.path.join(FINAL, rel)
            data = open(final_path, "rb").read() if os.path.exists(final_path) else install.original_entry(c, i)
            requests = []
            for _, mask_stem, block, area, d in mjobs:
                shared = cell_maps.get((mask_stem, str(area)))
                mapping, changes = assign_layers(data, block, d, shared)
                cell_maps.setdefault((mask_stem, str(area)), mapping)
                mappings[(model, mask_stem, block)] = mapping
                requests += [(block, L, rgb) for L, rgb in changes.items()]
            mz = fh6minizip.MiniZip(os.path.join(install.TRACK, f"GeoChunk{c}.minizip"))
            off, size, flags, _, stored = mz.entries[i]
            bk = os.path.join(install.BACKUP, f"GeoChunk{c}_{i}_{off:x}.bin")
            slot = open(bk, "rb").read() if os.path.exists(bk) else (mz.f.seek(off), mz.f.read(stored))[1]
            target = len(slot) - install.lz4_padding(slot, size)
            new, used = plan_model(data, requests, target)
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            open(final_path, "wb").write(new)
            if fname.endswith("cluster000.i.modelbin"):
                for (b, L, want), got in zip(requests, used):
                    print(f"  {model} block {b:2} {L:4}: want #{'%02x%02x%02x' % want} -> #{'%02x%02x%02x' % got}")
        print(f"inks planned: {model} ({len(files)} files)")

    # ---- 2) masks
    done = set()
    with tempfile.TemporaryDirectory() as tmp:
        for model, mask_stem, block, area, d in jobs:
            if (mask_stem, str(area)) in done:
                continue
            done.add((mask_stem, str(area)))
            mapping = mappings[(model, mask_stem, block)]
            srcs = glob.glob(os.path.join(ROOT, "extract", "**", f"{mask_stem}_pack_maskrgba_*.pb"), recursive=True)
            big = max(srcs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
            rel_big = os.path.relpath(big, os.path.join(ROOT, "extract"))
            full = np.asarray(swatch.to_image(current_bytes(rel_big, big))[0]).copy()
            x0, y0, x1, y1 = resolve_area(area, full)

            def area_image(spec):
                f = full.copy()
                masks = channels(draw(x1 - x0, y1 - y0, spec), spec, mapping)
                for ch, m in enumerate(masks):
                    f[y0:y1, x0:x1, ch] = (m * 255).round()
                return Image.fromarray(f, "RGBA")
            draw(x1 - x0, y1 - y0, d).resize((x1 - x0, y1 - y0), Image.LANCZOS).save(
                os.path.join(ROOT, "preview", f"rm_{mask_stem}_{block}.png"))
            variants = [area_image(d), area_image({**d, "logo": None})]
            for src in srcs:
                orig = open(src, "rb").read()
                rel = os.path.relpath(src, os.path.join(ROOT, "extract"))
                base = current_bytes(rel, src)
                inf = swatch.parse(orig)
                W, H = inf["width"], inf["height"]
                for attempt, new_full in enumerate(variants):
                    if (W, H) == new_full.size:
                        img = new_full
                    else:
                        cur = np.asarray(swatch.to_image(base)[0]).copy()
                        sx, sy = W / new_full.width, H / new_full.height
                        ax0, ay0 = int(x0 * sx), int(y0 * sy)
                        ax1, ay1 = max(ax0 + 1, round(x1 * sx)), max(ay0 + 1, round(y1 * sy))
                        part = new_full.crop((x0, y0, x1, y1))
                        part = Image.merge("RGBA", [ch.resize((ax1 - ax0, ay1 - ay0), Image.LANCZOS) for ch in part.split()])
                        cur[ay0:ay1, ax0:ax1] = np.asarray(part)
                        img = Image.fromarray(cur, "RGBA")
                    data = brand.encode(img, orig, tmp, keep_alpha=False, base_bytes=base)
                    if install.fits_slot(os.path.basename(src), data):
                        break
                    print(f"   {os.path.basename(src)[-24:]} {W}x{H}: too big" + (", retry without logo" if attempt == 0 else " even without logo!"))
                dest = os.path.join(FINAL, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "wb").write(data)
            print(f"built {mask_stem} cell {(x0, y0, x1, y1)} for block {block}  layers {mapping}")


if __name__ == "__main__":
    import jobs_masks
    run(jobs_masks.JOBS)
