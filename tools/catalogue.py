"""Numbered catalogue of every original sign, split out of the shared texture files.

Sections
  P  plain signs   (pieces of colour textures, see catalogue_spec.PIECES)
  T  tinted signs  (one per mask-sheet cell; every colourway the game uses is shown)
  D  directory boards (6 x 6 tenant tiles of sgn_cty_billboard_sqre_x9)
  S  POI stickers  (64 px cells of city_poi_decals_atlas_a..j)

Each entry: original image, current (modded) image if it changed, the swap it got.
Writes _modwork/catalogue/: index.html, catalogue.csv, img/*.webp
Usage: python tools/catalogue.py
"""
import base64
import csv
import glob
import html
import json
import os
import re
import struct
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, os.path.dirname(__file__))
import catalogue_spec
import gallery
import install
import jobs_masks
import jobs_plain
import mask_preview
import rebrand_cells
import rebrand_masks as rm
import rebrand_poi
import rebrand_x9
import swatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "catalogue")
IMG = os.path.join(OUT, "img")
FINAL = os.path.join(ROOT, "build", "final")
THUMB = 420
MASKLIKE = {"tex_gbl_sgn_com_v_01_c_bclr", "tex_tst_tile_changeme_01_a_bclr"}  # named bclr but are R/G/B ink masks

BRANDS = [("lawson", "Lawson"), ("familymart", "FamilyMart"), ("japanpost", "Japan Post"), ("jp_postal", "Japan Post"),
          ("maruetsu", "Maruetsu"), ("matsukiyo", "Matsumoto Kiyoshi"), ("welcia", "Welcia"), ("smbc", "SMBC"),
          ("eneos", "ENEOS"), ("autobacs", "Autobacs"), ("starbucks", "Starbucks"), ("uniqlo", "UNIQLO"),
          ("docomo", "docomo"), ("nakau", "Nakau"), ("ichiran", "Ichiran"), ("ohsho", "Gyoza no Ohsho"),
          ("tokyofm", "TOKYO FM"), ("hks", "HKS"), ("motul", "Motul"), ("tomica", "Tomica"), ("taito", "Taito Station"),
          ("rays", "RAYS"), ("spoon", "Spoon"), ("mitsuya", "Mitsuya Cider"), ("cclemon", "C.C. Lemon"),
          ("softbank", "SoftBank"), ("beams", "BEAMS"), ("seiyu", "Seiyu"), ("yellowhat", "Yellow Hat"),
          ("boss", "BOSS"), ("kirin", "Kirin"), ("bigecho", "Big Echo"), ("7eleven", "7-Eleven")]


def brand_of(logo_file):
    if not logo_file:
        return ""
    if logo_file.startswith("custom/"):  # the user's own artwork (assets/custom)
        return brand_of(logo_file[len("custom/"):]) + " (your image)"
    for key, name in BRANDS:
        if logo_file.startswith(key):
            return name
    return logo_file


def versions(stem):
    fs = [f for f in glob.glob(os.path.join(ROOT, "extract", "**", stem + "_*.pb"), recursive=True)
          if re.match(re.escape(stem) + r"_[0-9a-z]{7,8}", os.path.basename(f)) and open(f, "rb").read(4) == b"burG"]
    return fs


def largest(fs):
    return max(fs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])


def final_of(src):
    p = os.path.join(FINAL, os.path.relpath(src, os.path.join(ROOT, "extract")))
    return p if os.path.exists(p) else None


def save(im, name):
    im = im.convert("RGB")
    if im.width < 2 or im.height < 2 or im.width / im.height > 60 or im.height / im.width > 60:
        print("!! odd image", name, im.size)
        im = im.resize((max(2, im.width), max(2, im.height)))
    im.thumbnail((THUMB, THUMB), Image.LANCZOS)
    if min(im.size) < 1:
        im = im.resize((max(1, im.width), max(1, im.height)))
    path = os.path.join(IMG, name)
    im.save(path, "WEBP", quality=85)
    return "data:image/webp;base64," + base64.b64encode(open(path, "rb").read()).decode()  # page is one self-contained file


def differs(a, b):
    a = np.asarray(a.convert("RGB"), np.int16)
    b = np.asarray(b.convert("RGB").resize(a.shape[1::-1]), np.int16)
    return float(np.abs(a - b).mean()) > 2.0


# ---------------------------------------------------------------- P: plain signs

def plain_brand(stem, box):
    """Brand of the job op (logo) that covers most of this piece."""
    best, best_cov = "", 0.0
    x0, y0, x1, y1 = box
    for op in jobs_plain.JOBS.get(stem, []):
        if op["op"] != "logo":
            continue
        a0, b0, a1, b1 = op["box"]
        iw, ih = max(0, min(x1, a1) - max(x0, a0)), max(0, min(y1, b1) - max(y0, b0))
        cov = iw * ih / max(1, (a1 - a0) * (b1 - b0))
        if cov > best_cov:
            best, best_cov = brand_of(op["file"]), cov
    if not best and stem.startswith("bld_gbl_comm_03_a_features"):
        best = "Lawson"
    if not best:
        # recolour-only ops (e.g. stripes) -> brand of any logo in the same texture
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        near = min(((((op["box"][0] + op["box"][2]) / 2 - cx) ** 2 + ((op["box"][1] + op["box"][3]) / 2 - cy) ** 2, op["file"])
                    for op in jobs_plain.JOBS.get(stem, []) if op["op"] == "logo"), default=None)
        best = brand_of(near[1]) + " (recoloured to match)" if near else "modified"
    return best


def swap_label(stem, box, a, b):
    sa = np.asarray(a.convert("RGB"), np.float32).reshape(-1, 3).std(axis=0).mean()
    sb = np.asarray(b.convert("RGB"), np.float32).reshape(-1, 3).std(axis=0).mean()
    if sb < 3 and sa > 10:
        return "BROKEN: blank in the installed mod (fixed in next patch -> " + plain_brand(stem, box) + ")"
    return plain_brand(stem, box)


def components(rgb):
    flat = rgb.reshape(-1, 3)
    vals, counts = np.unique(flat // 4, axis=0, return_counts=True)
    bg = vals[counts.argmax()] * 4 + 2
    mask = np.abs(rgb.astype(np.int16) - bg).max(axis=2) > 18
    mask = ndimage.binary_dilation(mask, iterations=3)
    lab, n = ndimage.label(mask)
    boxes = []
    for sl in ndimage.find_objects(lab):
        y, x = sl
        if (x.stop - x.start) * (y.stop - y.start) >= 300:
            boxes.append((x.start, y.start, x.stop, y.stop))
    return sorted(boxes, key=lambda b: (b[1] // 64, b[0]))


def plain_entries():
    out = []
    for stem, pieces in catalogue_spec.PIECES.items():
        fs = versions(stem)
        if not fs:
            print("!! not extracted:", stem)
            continue
        src = largest(fs)
        orig = gallery.shown(open(src, "rb").read(), stem)
        fin = final_of(src)
        now = gallery.shown(open(fin, "rb").read(), stem) if fin else None
        if pieces == "components":
            pieces = [("window sticker", b) for b in components(np.asarray(orig))]
        for label, box in pieces:
            box = (max(0, box[0]), max(0, box[1]), min(orig.width, box[2]), min(orig.height, box[3]))
            if box[2] - box[0] < 4 or box[3] - box[1] < 4:
                print("!! empty piece:", stem, label, orig.size)
                continue
            a = orig.crop(box)
            b = now.crop(box) if now is not None else None
            changed = b is not None and differs(a, b)
            out.append({"label": label, "source": stem, "box": list(box), "where": "x%d-%d y%d-%d" % (box[0], box[2], box[1], box[3]),
                        "orig": a, "now": b if changed else None,
                        "swap": swap_label(stem, box, a, b) if changed else "", "group": stem})
    return out


# ---------------------------------------------------------------- T: tinted signs

def job_brands(index):
    """(mask stem, cell, grid) -> brand, from the tinted-sign jobs."""
    out = {}
    for job in jobs_masks.CELL_JOBS:
        logo = brand_of(job["design"].get("logo"))
        if "via" in job:
            hit = [v for v in index if v[0] == job["via"][0] and v[1] == job["via"][1]]
            if not hit:
                continue
            _, _, stem, grid, cell = hit[0]
        else:
            stem, cell = job["mask"], job["cell"]
            grid = next((v[3] for v in index if v[2] == stem and v[4] == cell), None)
        out[(stem, tuple(cell), tuple(grid))] = logo
    return out


def tinted_entries():
    lookup = install.chunk_lookup()
    index = rebrand_cells.build_index(lookup)
    brands = job_brands(index)
    model_cache, mask_cache = {}, {}

    def model(m, final):
        key = (m, final)
        if key not in model_cache:
            data = install.original_entry(*lookup[m + "_cluster000.i.modelbin"])
            if final:
                alt = glob.glob(os.path.join(FINAL, "**", m + "_cluster000.i.modelbin"), recursive=True)
                if alt:
                    data = open(alt[0], "rb").read()
            model_cache[key] = data
        return model_cache[key]

    def mask(stem, final):
        key = (stem, final)
        if key not in mask_cache:
            fs = rebrand_cells.mask_files(stem)
            if not fs:
                mask_cache[key] = None
            else:
                src = largest(fs)
                f = (final_of(src) or src) if final else src
                img, inf = swatch.to_image(open(f, "rb").read())
                a = np.asarray(img).copy()
                if inf["format"] in (3, 4):
                    a[..., 1:] = 0  # single-channel (BC4) ink mask: only R exists; the decoder fills A=255
                mask_cache[key] = a
        return mask_cache[key]

    def render(m, b, stem, area, final):
        mk = mask(stem, final)
        data = model(m, final)
        slots = rm.layer_slots(data, b)
        inks = [rm.slot_rgb(data, slots[L]) if L in slots else None for L in rm.LAYERS]
        x0, y0, x1, y1 = area
        return mask_preview.composite(mk[y0:y1, x0:x1], inks), tuple(tuple(i) if i else None for i in inks)

    cells = {}
    for m, b, stem, grid, cell in index:
        cells.setdefault((stem, tuple(cell), tuple(grid)), []).append((m, b))
    out, boards = [], []
    for (stem, cell, grid), users in sorted(cells.items()):
        mk = mask(stem, False)
        if mk is None:
            continue
        if stem in catalogue_spec.PIECES or not ("mask" in stem or stem in MASKLIKE):
            continue  # colour textures are split in the P section
        if stem.startswith(rebrand_x9.STEM):
            boards.append((stem, users))
            continue
        if not (1 <= cell[0] <= grid[0] and 1 <= cell[1] <= grid[1]):
            continue
        area = rm.resolve_area(("cell", cell[0], cell[1], grid[0], grid[1]), mk)
        if area[2] - area[0] < 4 or area[3] - area[1] < 4:
            continue
        seen, strip = set(), []
        for m, b in users:
            img, inks = render(m, b, stem, area, False)
            key = tuple(tuple(round(c / 12) for c in i) if i else None for i in inks)
            if key in seen:
                continue
            seen.add(key)
            strip.append(img)
        if max(np.asarray(im, np.float32).reshape(-1, 3).std(axis=0).mean() for im in strip) < 6:
            continue  # blank cell in every colourway
        m0, b0 = users[0]
        a, _ = render(m0, b0, stem, area, False)
        now, _ = render(m0, b0, stem, area, True)
        changed = differs(a, now) or any(differs(render(m, b, stem, area, False)[0], render(m, b, stem, area, True)[0])
                                         for m, b in users[1:6])
        swap = brands.get((stem, cell, grid), "") if changed else ""
        if changed and not swap:
            swap = "modified"
        sheet = stem.replace("_pack_maskrgba", "").replace("_mask", "")
        out.append({"label": "", "source": stem, "box": [int(v) for v in area], "where": f"cell col {cell[0]} row {cell[1]} of {grid[0]}x{grid[1]}",
                    "orig": a, "now": now if changed else None, "swap": swap, "group": sheet,
                    "colourways": strip, "models": sorted({m for m, _ in users}), "n_variants": len(users)})
    return out, boards, render, mask


def board_entries(boards, render, mask):
    out = []
    if not boards:
        return out
    stem = boards[0][0]
    users = [u for _, us in boards for u in us]
    mk = mask(stem, False)
    H, W = mk.shape[:2]
    T = W / 6
    for r in range(6):
        for c in range(6):
            area = (round(c * T), round(r * T), round((c + 1) * T), round((r + 1) * T))
            m0, b0 = users[0]
            a, _ = render(m0, b0, stem, area, False)
            now, _ = render(m0, b0, stem, area, True)
            changed = differs(a, now)
            t = rebrand_x9.TILES.get((r, c))
            strip, seen = [], set()
            for m, b in users[:40]:
                img, inks = render(m, b, stem, area, False)
                key = tuple(tuple(round(v / 12) for v in i) if i else None for i in inks)
                if key not in seen:
                    seen.add(key)
                    strip.append(img)
                if len(strip) >= 6:
                    break
            out.append({"label": "", "source": stem, "box": [int(v) for v in area], "where": f"tile row {r + 1} col {c + 1} of 6x6",
                        "orig": a, "now": now if changed else None,
                        "swap": (brand_of(t[0]) if t else "modified") if changed else "", "group": "directory boards",
                        "colourways": strip, "n_variants": len(users)})
    return out


# ---------------------------------------------------------------- S: POI stickers

def poi_entries():
    out = []
    C = rebrand_poi.CELL
    for L in "abcdefghij":
        fs = rebrand_poi.atlas_path(L)
        src = largest(fs)
        orig = swatch.to_image(open(src, "rb").read())[0].convert("RGB")
        fin = final_of(src)
        now = swatch.to_image(open(fin, "rb").read())[0].convert("RGB") if fin else None
        k = orig.width // 512 or 1
        for r in range(orig.height // (C * k)):
            for c in range(orig.width // (C * k)):
                box = (c * C * k, r * C * k, (c + 1) * C * k, (r + 1) * C * k)
                a = orig.crop(box)
                arr = np.asarray(a, np.float32)
                if arr.reshape(-1, 3).std(axis=0).mean() < 6:
                    continue
                b = now.crop(box) if now is not None else None
                changed = b is not None and differs(a, b)
                kind = rebrand_poi.TILES.get(f"{L}{r}{c}")
                swap = (brand_of(rebrand_poi.DESIGN[kind][1]) if kind else "modified") if changed else ""
                out.append({"label": "", "source": f"city_poi_decals_atlas_{L}_diff", "box": list(box),
                            "where": f"cell row {r} col {c} (64px)", "orig": a.resize((192, 192), Image.NEAREST),
                            "now": b.resize((192, 192), Image.NEAREST) if changed else None, "swap": swap,
                            "group": f"city_poi_decals_atlas_{L}"})
    return out


# ---------------------------------------------------------------- X: everything else that was discovered

def other_entries(known):
    """Whole-sheet entries for every other sign-related texture (tools/catalogue_extra.txt): seasonal
    versions, building features, stalls, tents, masks... not split into individual signs."""
    out = []
    path = os.path.join(os.path.dirname(__file__), "catalogue_extra.txt")
    if not os.path.exists(path):
        return out
    for stem in open(path).read().split():
        if stem in known:
            continue
        fs = versions(stem)
        if not fs:
            continue
        try:
            src = largest(fs)
            data = open(src, "rb").read()
            orig = swatch.to_image(data)[0]
        except Exception:
            continue  # formats the decoder can't show (HDR etc.)
        fin = final_of(src)
        now = swatch.to_image(open(fin, "rb").read())[0] if fin else None
        changed = now is not None and differs(orig, now)
        kind = "seasonal version" if re.search(r"x(winter|autumn|spring)x", stem) else "whole texture"
        out.append({"label": stem, "source": stem, "box": [0, 0, orig.width, orig.height],
                    "where": f"{kind} {orig.width}x{orig.height}", "orig": orig.convert("RGB"),
                    "now": now.convert("RGB") if changed else None, "swap": "modified" if changed else "",
                    "group": re.sub(r"_\d+.*$", "", stem)[:40]})
    return out


# ---------------------------------------------------------------- output

def strip_image(imgs, h=56):
    tiles = []
    for im in imgs[:10]:
        t = im.copy()
        t.thumbnail((h * 4, h))
        tiles.append(t)
    W = sum(t.width for t in tiles) + 4 * (len(tiles) - 1)
    s = Image.new("RGB", (max(1, W), h), (24, 24, 26))
    x = 0
    for t in tiles:
        s.paste(t, (x, (h - t.height) // 2))
        x += t.width + 4
    return s


REG_PATH = os.path.join(OUT, "id_registry.json")


def load_registry():
    if os.path.exists(REG_PATH):
        return json.load(open(REG_PATH))
    seed = os.path.join(OUT, "id_registry_seed.json")   # IDs as first published
    return {f"{e['section']}|{e['source']}|{','.join(str(int(v)) for v in e['box'])}": e["id"]
            for e in json.load(open(seed))} if os.path.exists(seed) else {}


REG = {}


def main():
    REG.update(load_registry())
    os.makedirs(IMG, exist_ok=True)
    for f in glob.glob(os.path.join(IMG, "*.webp")):
        os.remove(f)
    print("plain..."); P = plain_entries()
    print("tinted..."); T, boards, render, mask = tinted_entries()
    print("boards..."); D = board_entries(boards, render, mask)
    print("poi..."); S = poi_entries()
    print("other..."); X = other_entries({e["source"] for es in (P, T, D, S) for e in es})
    rows_, cards = [], []
    sections = [("P", "Plain signs (shop signs, posters, billboards, stickers)", P),
                ("T", "Tinted signs (game-coloured shop signs: one image per sign design, all colourways shown)", T),
                ("D", "Building directory boards (tenant tiles)", D),
                ("S", "Small POI stickers (city decal sheets)", S),
                ("X", "Other textures (whole sheets: seasonal versions, building features, stalls, tents, masks)", X)]
    was = {}
    rec = os.path.join(OUT, "choices", "disabled_swaps.json")
    if os.path.exists(rec):
        was = {k: v["was_swapped_to"] for k, v in json.load(open(rec, encoding="utf-8"))["signs"].items()}
    for prefix, title, entries in sections:
        # IDs are permanent (the user's choices are keyed by them): reuse the registered ID for the same
        # sign (section + texture + box); brand-new signs get the next free number in their section
        used = [int(v[1:]) for v in REG.values() if v[0] == prefix]
        nxt = max(used, default=0) + 1
        for e in entries:
            key = f"{prefix}|{e['source']}|{','.join(str(int(v)) for v in e['box'])}"
            if key not in REG:
                REG[key] = f"{prefix}{nxt:03d}"
                nxt += 1
            e["id"] = REG[key]
        entries.sort(key=lambda e: int(e["id"][1:]))
        for e in entries:
            e["section"] = prefix
            e["orig_url"] = save(e["orig"], e["id"] + ".webp")
            e["now_url"] = save(e["now"], e["id"] + "_now.webp") if e.get("now") is not None else ""
            print(e["id"], e["orig"].size, len(e.get("colourways", []))) if e["orig"].width * e["orig"].height == 0 else None
            e["cw_url"] = save(strip_image(e["colourways"]), e["id"] + "_cw.webp") if len(e.get("colourways", [])) > 1 else ""
            rows_.append({"id": e["id"], "section": title.split(" (")[0], "original": e["label"], "current_swap": e["swap"],
                          "source_texture": e["source"], "where": e["where"],
                          "colourways": len(e.get("colourways", [])) or "", "switched_off_was": was.get(e["id"], ""),
                          "your_choice": ""})
    json.dump(REG, open(REG_PATH, "w"), indent=0)
    # positions of every sign (pixels of the largest texture version) for tools/label_build.py
    json.dump([{"id": e["id"], "section": e["section"], "source": e["source"], "box": e["box"]}
               for _, _, es in sections for e in es], open(os.path.join(OUT, "index.json"), "w"), indent=0)
    with open(os.path.join(OUT, "catalogue.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_[0]))
        w.writeheader()
        w.writerows(rows_)
    data = [{k: e[k] for k in ("id", "section", "label", "swap", "source", "where", "group", "orig_url", "now_url", "cw_url")}
            | {"n_cw": len(e.get("colourways", [])), "models": e.get("models", []), "was": was.get(e["id"], "")}
            for _, _, es in sections for e in es]
    tpl = open(os.path.join(os.path.dirname(__file__), "catalogue_template.html"), encoding="utf-8").read()
    page = tpl.replace("/*DATA*/", json.dumps(data, ensure_ascii=False)).replace(
        "/*SECTIONS*/", json.dumps([(p, t) for p, t, _ in sections], ensure_ascii=False))
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(page)
    for p, t, es in sections:
        print(f"{p}: {len(es)} signs, {sum(1 for e in es if e['swap'])} swapped")


if __name__ == "__main__":
    main()
