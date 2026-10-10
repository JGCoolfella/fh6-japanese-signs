"""Find textures by appearance: flags any colour texture that contains the 365 Konbini
fascia pattern (yellow band with a red stripe and a blue stripe stacked vertically).

Scans GeoChunk*.minizip and media/Stripped/gs/swatchbins.zip, decoding one modest-size
version of each texture. Writes hits to preview/look_hits.txt and thumbnails to preview/look_*.png.
"""
import os
import re
import sys
import zipfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import fh6minizip
import swatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MEDIA = os.path.join(os.path.dirname(ROOT), "media")
TRACK = os.path.join(MEDIA, "Tracks", "Brio")
SKIP = re.compile(r"nrml|extra|_mask|lmap|lmbake|autoterrain|submap|mainmap|wdepth|road_|gen_grs|tre_|bsh_|roc_|geology|gcr_|_vc_", re.I)


def classify(a):
    r, g, b = a[..., 0].astype(int), a[..., 1].astype(int), a[..., 2].astype(int)
    yellow = (r > 200) & (g > 170) & (b < 90)
    red = (r > 190) & (g < 80) & (b < 90)
    blue = (b > 110) & (r < 80) & (g < 110)
    return yellow, red, blue


def has_fascia(img):
    a = np.asarray(img.convert("RGB"))
    if a.shape[0] < 32 or a.shape[1] < 32:
        return False
    y, r, b = classify(a)
    # Rows that are mostly one colour across a decent run of columns.
    w = a.shape[1]
    ry, rr, rb = y.mean(axis=1), r.mean(axis=1), b.mean(axis=1)
    # Look column-strip-wise so atlases with several panels still match.
    for x0 in range(0, w, max(16, w // 8)):
        sl = slice(x0, min(w, x0 + max(16, w // 8)))
        cy, cr, cb = y[:, sl].mean(axis=1), r[:, sl].mean(axis=1), b[:, sl].mean(axis=1)
        seq = []
        for v_y, v_r, v_b in zip(cy, cr, cb):
            k = "Y" if v_y > 0.8 else "R" if v_r > 0.8 else "B" if v_b > 0.8 else "."
            if not seq or seq[-1] != k:
                seq.append(k)
        s = "".join(seq).replace(".", "")
        if "YRYBY" in s or "YBYRY" in s:
            return True
    return False


def pick_versions(names):
    """name stem -> list of (key, size) choosing one version around 512px."""
    groups = {}
    for key, name in names:
        base = os.path.basename(name)
        if not base.endswith(".pb") or SKIP.search(base):
            continue
        stem = re.sub(r"_quality\d+\.pb$", "", base)
        groups.setdefault(stem, []).append((key, base))
    return groups


def main():
    hits = []
    seen = 0
    # Map archives
    for c in range(16):
        txt = os.path.join(TRACK, f"ChunkContentsMiniZip{c}.txt")
        mzp = os.path.join(TRACK, f"GeoChunk{c}.minizip")
        if not os.path.exists(txt):
            continue
        names = fh6minizip.load_names(txt)
        mz = fh6minizip.MiniZip(mzp)
        groups = pick_versions(names.items())
        for stem, vers in groups.items():
            # Prefer a mid-size version: smallest entry above ~40 KB, else the largest.
            vers = sorted(vers, key=lambda v: mz.entries[v[0]][1])
            choice = next((v for v in vers if mz.entries[v[0]][1] > 40000), vers[-1])
            try:
                data = mz.read(choice[0])
                img, _ = swatch.to_image(data)
            except Exception:
                continue
            seen += 1
            if has_fascia(img):
                hits.append(f"GeoChunk{c}\t{names[choice[0]]}")
                img.convert("RGB").save(os.path.join(ROOT, "preview", f"look_{len(hits)}.png"))
                print("HIT", hits[-1], flush=True)
    # Stripped/gs/swatchbins.zip
    zpath = os.path.join(MEDIA, "Stripped", "gs", "swatchbins.zip")
    z = zipfile.ZipFile(zpath)
    infos = {i.filename: i for i in z.infolist()}
    groups = pick_versions([(n, n) for n in infos])
    for stem, vers in groups.items():
        vers = sorted(vers, key=lambda v: infos[v[0]].file_size)
        choice = next((v for v in vers if infos[v[0]].file_size > 40000), vers[-1])
        try:
            img, _ = swatch.to_image(z.read(choice[0]))
        except Exception:
            continue
        seen += 1
        if has_fascia(img):
            hits.append(f"swatchbins.zip\t{choice[0]}")
            img.convert("RGB").save(os.path.join(ROOT, "preview", f"look_{len(hits)}.png"))
            print("HIT", hits[-1], flush=True)
    open(os.path.join(ROOT, "preview", "look_hits.txt"), "w").write("\n".join(hits))
    print(f"scanned {seen} textures, {len(hits)} hits")


if __name__ == "__main__":
    main()
