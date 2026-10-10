"""TEMPORARY in-game labels: stamp every catalogued sign with its catalogue ID inside a perfect
circle (an oval in game = the sign is stretched). Built on top of build/final into build/labels.

  python tools/label_build.py            # -> build/labels  (then: python tools/install.py patch labels)
  python tools/install.py patch final    # back to the normal mod (labels removed)

Plain textures: black badge with yellow frame, ring and ID (alpha forced opaque so cut-out decals show it).
Tinted masks: the two ink layers with the most contrast across all the sign's colourways; frame + ring + ID in one, fill in the other.
"""
import glob
import json
import os
import shutil
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import brand
import catalogue
import install
import rebrand_cells
import rebrand_masks as rm
import swatch

ROOT = brand.ROOT
FINAL = os.path.join(ROOT, "build", "final")
OUT = os.path.join(ROOT, "build", "labels")
FONT = "C:/Windows/Fonts/arialbd.ttf"


def badge(size, text):
    """Hard-edged L mask (1 = foreground) of a square badge: solid frame, perfect circle, ID."""
    S = max(8, int(size)) * 4
    ink = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(ink)
    fw = max(4, S // 10)                      # outline frame: keeps the badge visible on any background
    d.rectangle((0, 0, S - 1, S - 1), outline=255, width=fw)
    w = max(2, S // 18)
    inset = fw + S // 24
    d.ellipse((inset, inset, S - inset, S - inset), outline=255, width=w)
    fs = S
    while fs > 6:
        f = ImageFont.truetype(FONT, fs)
        x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
        if x1 - x0 <= S * 0.56 and y1 - y0 <= S * 0.32:
            break
        fs -= 2
    d.text(((S - (x1 - x0)) / 2 - x0, (S - (y1 - y0)) / 2 - y0), text, fill=255, font=f)
    n = max(8, int(size))
    # hard edges (no anti-aliasing): far cheaper to compress, so labels fit the fixed slots
    return (np.asarray(ink.resize((n, n), Image.LANCZOS)) > 110).astype(np.float32)


def show_layer(reg, mask, layer, single):
    """Make pixels where mask is set display one ink layer (topmost layer whose channel is 1 wins)."""
    sel = mask > 0
    reg[sel, :] = 0
    if layer != "base":
        k = 0 if single else rm.LAYERS.index(layer) - 1
        reg[sel, k] = 255
    if single:
        reg[sel, 1:3] = reg[sel, 0:1]
        reg[sel, 3] = 255


def stamp(img, entries, scale, plain, single, k_size):
    a = np.asarray(img.convert("RGBA")).copy()
    H, W = a.shape[:2]
    for e in entries:
        x0, y0, x1, y1 = (round(v * scale) for v in e["box"])
        w, h = x1 - x0, y1 - y0
        frac = 0.9 if e["section"] == "S" else 0.8 if max(w, h) > 3 * min(w, h) else 0.45   # thin strips: bigger badge
        size = int(min(w, h) * frac * k_size) // 4 * 4
        if size < 8:
            continue
        m = badge(size, e["id"])
        bx, by = (x0 + (w - size) // 2) // 4 * 4, (y0 + (h - size) // 2) // 4 * 4   # whole 4x4 blocks
        bx, by = max(0, min(W - size, bx)), max(0, min(H - size, by))
        reg = a[by:by + size, bx:bx + size].astype(np.float32)
        if plain:
            # yellow frame/ring/ID on black
            reg[..., :3] = np.where(m[..., None] > 0, np.array([255, 220, 0], np.float32), 0)
            reg[..., 3] = 255
        else:
            bg, fg = e.get("layers", ("base", "R"))
            show_layer(reg, 1 - m, bg, single)
            show_layer(reg, m, fg, single)
        a[by:by + size, bx:bx + size] = reg.clip(0, 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def pick_layers(entries_by_stem):
    """For every tinted sign pick the two ink layers with the most contrast in ALL its colourways."""
    import pickle
    cache = os.path.join(ROOT, "catalogue", "variant_index.pkl")
    lookup = install.chunk_lookup()
    if os.path.exists(cache):
        index = pickle.load(open(cache, "rb"))
    else:
        index = rebrand_cells.build_index(lookup)
        pickle.dump(index, open(cache, "wb"))
    models = {}

    def model(m):
        if m not in models:
            alt = glob.glob(os.path.join(FINAL, "**", m + "_cluster000.i.modelbin"), recursive=True)
            models[m] = open(alt[0], "rb").read() if alt else install.original_entry(*lookup[m + "_cluster000.i.modelbin"])
        return models[m]

    for stem, entries in entries_by_stem.items():
        if "mask" not in stem:
            continue
        fs = catalogue.versions(stem)
        big = catalogue.largest(fs)
        inf = swatch.parse(open(big, "rb").read())
        single = inf["format"] in (3, 4)
        shape = (inf["height"], inf["width"])
        layers = ["base", "R"] if single else rm.LAYERS
        users = [v for v in index if v[2] == stem]
        for e in entries:
            mine = [v for v in users if list(rm.resolve_area(("cell", v[4][0], v[4][1], v[3][0], v[3][1]), np.zeros(shape))) == e["box"]] or users
            inks = []
            for m, b, *_ in mine[:24]:
                data = model(m)
                slots = rm.layer_slots(data, b)
                inks.append({L: (rm.slot_rgb(data, slots[L]) if L in slots else None) for L in layers})
            best, best_c = ("base", "R"), -1
            for bgL in layers:
                for fgL in layers:
                    if bgL == fgL:
                        continue
                    cs = [np.linalg.norm(np.subtract(i[bgL], i[fgL])) if i.get(bgL) is not None and i.get(fgL) is not None else -1
                          for i in inks]
                    c = min(cs) if cs else -1
                    if c > best_c + 1e-6:
                        best, best_c = (bgL, fgL), c
            e["layers"] = best
            e["contrast"] = best_c


def main():
    index = json.load(open(os.path.join(ROOT, "catalogue", "index.json")))
    index = [e for e in index if e["section"] != "X"]   # whole-sheet extras: no badge
    by_stem = {}
    for e in index:
        by_stem.setdefault(e["source"], []).append(e)
    pick_layers(by_stem)
    low = [(e["id"], round(e["contrast"])) for es in by_stem.values() for e in es if e.get("contrast", 999) < 60]
    print("tinted signs with weak best contrast (<60):", low)
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(FINAL, OUT)
    done = skipped = 0
    with tempfile.TemporaryDirectory() as tmp:
        for stem, entries in sorted(by_stem.items()):
            fs = catalogue.versions(stem)
            if not fs:
                print("!! not extracted:", stem)
                continue
            W0 = swatch.parse(open(catalogue.largest(fs), "rb").read())["width"]
            plain = "mask" not in stem
            for src in fs:
                orig = open(src, "rb").read()
                inf = swatch.parse(orig)
                cur_path = catalogue.final_of(src) or src
                base = open(cur_path, "rb").read()
                single = inf["format"] in (3, 4)
                img = swatch.to_image(base)[0]
                for k in (1.0, 0.8, 0.65, 0.5, 0.38):
                    data = brand.encode(stamp(img, entries, inf["width"] / W0, plain, single, k), orig, tmp,
                                        keep_alpha=False, base_bytes=base)
                    if install.fits_slot(os.path.basename(src), data):
                        break
                else:
                    skipped += 1
                    print(f"   no room for labels: {os.path.basename(src)[-40:]} ({inf['width']}x{inf['height']})")
                    continue
                dest = os.path.join(OUT, os.path.relpath(src, os.path.join(ROOT, "extract")))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "wb").write(data)
                done += 1
            print(f"labelled {stem} ({len(entries)} signs, {len(fs)} versions)")
    n = sum(len(f) for _, _, f in os.walk(OUT))
    print(f"build/labels ready: {n} files ({done} labelled versions, {skipped} versions without room)")


if __name__ == "__main__":
    main()
