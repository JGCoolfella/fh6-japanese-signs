"""Unpack an export from the catalogue page (fh6_sign_choices.json).

Writes catalogue/choices/choices.csv and catalogue/choices/<ID>_custom.png for every custom image,
plus <ID>_original.png next to it for side-by-side work.
Usage: python tools/import_choices.py path/to/fh6_sign_choices.json
"""
import base64
import csv
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "catalogue", "choices")


def main():
    j = json.load(open(sys.argv[1], encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for sid, s in sorted(j["signs"].items()):
        img = s.pop("custom_image", None)
        if img:
            open(os.path.join(OUT, f"{sid}_custom.png"), "wb").write(base64.b64decode(img.split(",", 1)[1]))
            src = os.path.join(ROOT, "catalogue", "img", f"{sid}.webp")
            if os.path.exists(src):
                shutil.copy(src, os.path.join(OUT, f"{sid}_original.webp"))
        rows.append({"id": sid, **s, "custom_image": f"{sid}_custom.png" if img else ""})
    keys = ["id", "original_sign", "current_swap", "your_choice", "custom_image", "fit", "rotate", "source_texture", "where"]
    with open(os.path.join(OUT, "choices.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} signs, {sum(1 for r in rows if r['custom_image'])} custom images -> {OUT}")


if __name__ == "__main__":
    main()
