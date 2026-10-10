"""Cell-based rebranding of shader-tinted signs (replaces the per-model rebrand_masks run).

A job targets one mask *cell* (mask texture stem + atlas cell). Every model/variant in the
map that draws that cell (found via each variant's texture SourceHash in AssetManifest.xml)
gets the brand's ink colours, so the same sign looks the same wherever it is used.

Job dict:
  {"mask": stem, "cell": (col, row)}            or  {"via": (model stem, block)}
  "area": (x0, y0, x1, y1)   optional pixel area (largest mask) instead of the whole cell
  "design": {...}            see rebrand_masks.draw (colours/bg/bands/panel/logo/...)
Jobs live in jobs_masks.py (JOBS). Stacks on build/final.
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
import rebrand_masks as rm
import swatch
import variants

ROOT = brand.ROOT
FINAL = os.path.join(ROOT, "build", "final")
LAYERS = rm.LAYERS
try:
    from jobs_user import KEEP_CELLS
except ImportError:
    KEEP_CELLS = set()
MASKLIKE = {"tex_gbl_sgn_com_v_01_c_bclr", "tex_tst_tile_changeme_01_a_bclr"}  # named bclr but hold R/G/B ink masks


# ---------------------------------------------------------------- index of all tinted variants

def hash_table():
    x = open(os.path.join(install.TRACK, "AssetManifest.xml"), encoding="utf-8", errors="replace").read()
    out = {}
    for m in re.finditer(r'Source="([^"]+?)\.swatch" SourceHash="(\d+)"', x):
        name = m.group(1).split("\\")[-1]
        out[int(m.group(2))] = re.sub(r"_[0-9a-f]{8}-[0-9a-f-]{27}$", "", name)
    return out


def build_index(lookup):
    """[(model stem, block, mask stem, grid, cell)] for every signage variant in the map."""
    hashes = hash_table()
    out = []
    stems = sorted({re.sub(r"_cluster\d+\.i\.modelbin$", "", n) for n in lookup
                    if re.match(r"(sgn|sng|bld|prp|inf)_.*_cluster000\.i\.modelbin$", n)})
    for model in stems:
        c, i = lookup[model + "_cluster000.i.modelbin"]
        data = install.original_entry(c, i)
        if b"environment_signage" not in data:
            continue
        for b, tex, grid, cell, _ in variants.variant_table(data):
            if not tex:
                continue
            raw = bytes.fromhex(tex)
            stem = hashes.get(struct.unpack(">I", raw)[0]) or hashes.get(struct.unpack("<I", raw)[0])
            if stem:
                out.append((model, b, stem, grid, cell))
    return out


# ---------------------------------------------------------------- helpers

def mask_files(stem):
    return [f for f in glob.glob(os.path.join(ROOT, "extract", "**", f"{stem}_*.pb"), recursive=True)
            if open(f, "rb").read(4) == b"burG"]


def current(src):
    cur = os.path.join(FINAL, os.path.relpath(src, os.path.join(ROOT, "extract")))
    return cur if os.path.exists(cur) else src


def model_files(lookup, model):
    return sorted((f, lookup[f]) for f in lookup if f.startswith(model + "_cluster") and f.endswith(".modelbin"))


def mask_channels(stem):
    fs = mask_files(stem)
    fmt = swatch.parse(open(fs[0], "rb").read())["format"]
    return ["R"] if fmt in (3, 4) else ["R", "G", "B", "A"]


def choose_mapping(datas_blocks, design, channels):
    """One colour->layer mapping valid for every variant drawing the cell.
    datas_blocks: [(model bytes, block)]. Minimises ink changes over all variants."""
    names = list(design["colours"])
    usable = ["base"] + channels
    best = None
    for perm in itertools.permutations(usable, len(names)):
        mapping = dict(zip(names, perm))
        bg_rank = LAYERS.index(mapping[design["bg"]])
        if any(LAYERS.index(L) < bg_rank for n, L in mapping.items() if n != design["bg"]):
            continue
        changes, err, ok = 0, 0.0, True
        for data, b in datas_blocks:
            slots = rm.layer_slots(data, b)
            for n, L in mapping.items():
                if L not in slots:
                    ok = False
                    break
                d = rm.dist(rm.slot_rgb(data, slots[L]), design["colours"][n])
                changes += d > rm.SAME
                err += min(d, rm.SAME + 1)
            if not ok:
                break
        if not ok:
            continue
        key = (changes, err)
        if best is None or key < best[0]:
            best = (key, mapping)
    return best[1] if best else None


# ---------------------------------------------------------------- main

def run(jobs):
    lookup = install.chunk_lookup()
    index = build_index(lookup)
    print(f"index: {len(index)} tinted variants")
    originals = {}

    def model_data(model):
        if model not in originals:
            c, i = lookup[model + "_cluster000.i.modelbin"]
            fp = os.path.join(FINAL, fh6minizip.load_names(os.path.join(install.TRACK, f"ChunkContentsMiniZip{c}.txt"))[i]) \
                if False else None
            originals[model] = install.original_entry(c, i)
        return originals[model]

    # resolve jobs -> (mask, cell, area, design, variants)
    resolved = []
    for job in jobs:
        if "via" in job:
            model, block = job["via"]
            hit = [v for v in index if v[0] == model and v[1] == block]
            if not hit:
                print("!! no variant for", job["via"])
                continue
            _, _, stem, grid, cell = hit[0]
        else:
            stem, cell = job["mask"], job["cell"]
            grid = next((v[3] for v in index if v[2] == stem and v[4] == cell), None)
            if grid is None:
                print("!! no variant uses", stem, cell)
                continue
        if "mask" not in stem and stem not in MASKLIKE:
            print("!! skipped (colour texture, not an ink mask):", stem, cell)
            continue
        users = [v for v in index if v[2] == stem and v[4] == cell and v[3] == grid]
        if (stem, tuple(cell)) in KEEP_CELLS:
            print("   keep original:", stem, cell)
            continue
        # a later job for the same cell replaces an earlier one (user choices come last)
        resolved = [r for r in resolved if (r[0], r[1], r[2]) != (stem, cell, grid)]
        resolved.append((stem, cell, grid, job.get("area"), job["design"], users))

    # ink planning per model
    requests = {}  # model -> [(block, layer, rgb)]
    mappings = []
    for stem, cell, grid, area, d, users in resolved:
        chans = mask_channels(stem)
        mapping = choose_mapping([(model_data(m), b) for m, b, *_ in users], d, chans)
        if mapping is None:
            # fall back: only variants that have every needed layer
            good = [u for u in users if choose_mapping([(model_data(u[0]), u[1])], d, chans)]
            mapping = choose_mapping([(model_data(m), b) for m, b, *_ in good], d, chans) if good else None
            users = good
        if mapping is None:
            print("!! no layer mapping for", stem, cell)
            mappings.append(None)
            continue
        mappings.append(mapping)
        for m, b, *_ in users:
            data = model_data(m)
            slots = rm.layer_slots(data, b)
            for n, L in mapping.items():
                if rm.dist(rm.slot_rgb(data, slots[L]), d["colours"][n]) > rm.SAME:
                    requests.setdefault(m, []).append((b, L, d["colours"][n]))
        print(f"cell {stem} {cell}: {len(users)} variants  layers {mapping}")

    _mz, _names = {}, {}

    def mz_of(c):
        if c not in _mz:
            _mz[c] = fh6minizip.MiniZip(os.path.join(install.TRACK, f"GeoChunk{c}.minizip"))
        return _mz[c]

    def names_of(c):
        if c not in _names:
            _names[c] = fh6minizip.load_names(os.path.join(install.TRACK, f"ChunkContentsMiniZip{c}.txt"))
        return _names[c]

    for model, reqs in requests.items():
        # de-duplicate (same block/layer requested twice)
        seen = {}
        for b, L, rgb in reqs:
            seen[(b, L)] = rgb
        reqs = [(b, L, rgb) for (b, L), rgb in seen.items()]
        for fname, (c, i) in model_files(lookup, model):
            rel = names_of(c)[i]
            final_path = os.path.join(FINAL, rel)
            mz = mz_of(c)
            off0 = mz.entries[i][0]
            bk0 = os.path.join(install.BACKUP, f"GeoChunk{c}_{i}_{off0:x}.bin")
            data = install.original_entry(c, i) if os.path.exists(bk0) else mz.read(i)
            off, size, flags, _, stored = mz.entries[i]
            bk = os.path.join(install.BACKUP, f"GeoChunk{c}_{i}_{off:x}.bin")
            slot = open(bk, "rb").read() if os.path.exists(bk) else (mz.f.seek(off), mz.f.read(stored))[1]
            target = len(slot) - install.lz4_padding(slot, size) if flags & 0xFF == 0x1F else None
            # block numbers can differ between cluster files: match blocks by their bytes
            ref = model_data(model)
            ref_blocks = rm.blocks(ref)
            file_blocks = rm.blocks(data)
            by_bytes = {data[st:en]: k for k, (st, en) in enumerate(file_blocks)}
            file_reqs = []
            for b, L, rgb in reqs:
                if b < len(ref_blocks):
                    st, en = ref_blocks[b]
                    k = by_bytes.get(ref[st:en])
                    if k is not None:
                        file_reqs.append((k, L, rgb))
            if not file_reqs:
                continue
            reqs_here = file_reqs
            try:
                new, used = rm.plan_model(data, reqs_here, target)
            except ValueError:
                # too many changes for the slot: keep the most important (fewest) per block
                print(f"   {fname}: ink changes don't fit ({len(reqs_here)}), trying fewer")
                new = None
                for k in range(len(reqs_here) - 1, 0, -1):
                    try:
                        new, used = rm.plan_model(data, reqs_here[:k], target)
                        print(f"   kept {k}/{len(reqs_here)} ink changes")
                        break
                    except ValueError:
                        continue
                if new is None:
                    continue
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            open(final_path, "wb").write(new)
        print(f"inks: {model} {len(reqs)} changes")

    # masks
    with tempfile.TemporaryDirectory() as tmp:
        for (stem, cell, grid, area, d, users), mapping in zip(resolved, mappings):
            if mapping is None:
                continue
            srcs = mask_files(stem)
            big = max(srcs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
            full = np.asarray(swatch.to_image(open(current(big), "rb").read())[0]).copy()
            if area:
                x0, y0, x1, y1 = area
            else:
                x0, y0, x1, y1 = rm.resolve_area(("cell", cell[0], cell[1], grid[0], grid[1]), full)

            def area_image(spec):
                f = full.copy()
                masks = rm.channels(rm.draw(x1 - x0, y1 - y0, spec), spec, mapping)
                for ch, m in enumerate(masks):
                    f[y0:y1, x0:x1, ch] = (m * 255).round()
                return Image.fromarray(f, "RGBA")
            def shrink(box, k):
                x0_, y0_, x1_, y1_ = box
                cx, cy = (x0_ + x1_) / 2, (y0_ + y1_) / 2
                return (cx - (cx - x0_) * k, cy - (cy - y0_) * k, cx + (x1_ - cx) * k, cy + (y1_ - cy) * k)
            lb = d.get("logo_box", (0.1, 0.25, 0.9, 0.75))
            variants_img = [area_image(d), area_image({**d, "logo_box": shrink(lb, 0.7)}),
                            area_image({**d, "logo_box": shrink(lb, 0.5)}), area_image({**d, "logo": None})]
            rm.draw(x1 - x0, y1 - y0, d).resize((x1 - x0, y1 - y0)).save(
                os.path.join(ROOT, "preview", f"cell_{stem}_{cell[0]}{cell[1]}.png"))
            for src in srcs:
                orig = open(src, "rb").read()
                base = open(current(src), "rb").read()
                inf = swatch.parse(orig)
                W, H = inf["width"], inf["height"]
                for attempt, nf in enumerate(variants_img):
                    if (W, H) == nf.size:
                        img = nf
                    else:
                        cur = np.asarray(swatch.to_image(base)[0]).copy()
                        sx, sy = W / nf.width, H / nf.height
                        ax0, ay0 = int(x0 * sx), int(y0 * sy)
                        ax1, ay1 = max(ax0 + 1, round(x1 * sx)), max(ay0 + 1, round(y1 * sy))
                        part = nf.crop((x0, y0, x1, y1))
                        part = Image.merge("RGBA", [ch.resize((ax1 - ax0, ay1 - ay0), Image.LANCZOS) for ch in part.split()])
                        cur[ay0:ay1, ax0:ax1] = np.asarray(part)
                        img = Image.fromarray(cur, "RGBA")
                    data = brand.encode(img, orig, tmp, keep_alpha=False, base_bytes=base)
                    if install.fits_slot(os.path.basename(src), data):
                        break
                    print(f"   {os.path.basename(src)[-24:]} {W}x{H}: too big" + ("" if attempt < 3 else " even without logo!") + f" (attempt {attempt + 1})")
                else:
                    print(f"   {os.path.basename(src)[-24:]}: nothing fits, keeping the previous version")
                    continue
                dest = os.path.join(FINAL, os.path.relpath(src, os.path.join(ROOT, "extract")))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "wb").write(data)
            print(f"built {stem} cell {cell} ({len(users)} variants)")


if __name__ == "__main__":
    import jobs_masks
    run(jobs_masks.CELL_JOBS)
