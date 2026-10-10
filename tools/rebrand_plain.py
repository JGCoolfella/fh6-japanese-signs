"""Region-based rebranding of plain-colour textures (signs, posters, facades).

Jobs live in jobs_plain.py: {texture stem: [ops]}. Each texture is processed at full
resolution starting from build/final (if an earlier step already changed it) or the
original in extract/, then every quality version is re-encoded into build/final.

Ops (boxes are (x0, y0, x1, y1) in the largest version):
  {"op": "remap", "box": b, "map": [(src_rgb, dst_rgb), ...]}
      recolour by nearest palette colour; anti-aliased edges between two palette colours
      are kept smooth by projecting each pixel onto the closest palette segment.
  {"op": "fill", "box": b, "rgb": c}
  {"op": "bands", "box": b, "bg": c, "bands": [(start, end, rgb), ...], "vertical": False}
      start/end are fractions of the box height (or width when vertical).
  {"op": "restore", "box": b}  -- put the original game pixels back (user chose "keep original")
  {"op": "logo", "box": b, "file": f, "colour": c|None, "bg": c|None, "rotate": 0,
   "fill": 0.9}  -- logo fitted inside the box (fill = fraction of box used)
"""
import glob
import os
import shutil
import sys
import tempfile

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
import brand
import install
import swatch

ROOT = brand.ROOT
FINAL = os.path.join(ROOT, "build", "final")
ASSETS = brand.ASSETS


def _remap(a, box, pairs):
    x0, y0, x1, y1 = box
    reg = a[y0:y1, x0:x1, :3].astype(np.float32)
    src = np.array([p[0] for p in pairs], np.float32)
    dst = np.array([p[1] for p in pairs], np.float32)
    n = len(src)
    flat = reg.reshape(-1, 3)
    best_d = np.full(len(flat), np.inf, np.float32)
    out = np.zeros_like(flat)
    for i in range(n):
        for j in range(i, n):
            a0, b0 = src[i], src[j]
            seg = b0 - a0
            L = float((seg ** 2).sum())
            t = np.zeros(len(flat), np.float32) if L == 0 else np.clip(((flat - a0) @ seg) / L, 0, 1)
            proj = a0 + t[:, None] * seg
            d = ((flat - proj) ** 2).sum(1)
            m = d < best_d
            best_d[m] = d[m]
            out[m] = dst[i] + t[m, None] * (dst[j] - dst[i])
    # keep shading/grime: add back the residual from the palette fit
    resid = flat - (src[0] * 0)  # placeholder to keep shapes explicit
    a[y0:y1, x0:x1, :3] = np.clip(out, 0, 255).reshape(reg.shape).astype(np.uint8)


def _bands(a, box, bg, bands, vertical=False):
    x0, y0, x1, y1 = box
    a[y0:y1, x0:x1, :3] = bg
    span = (x1 - x0) if vertical else (y1 - y0)
    for s, e, c in bands:
        p0, p1 = round(s * span), round(e * span)
        if vertical:
            a[y0:y1, x0 + p0:x0 + p1, :3] = c
        else:
            a[y0 + p0:y0 + p1, x0:x1, :3] = c


def _logo(a, box, file, colour=None, bg=None, rotate=0, fill=0.9, valign=0.5, squash=1.0):
    x0, y0, x1, y1 = box
    if bg is not None:
        a[y0:y1, x0:x1, :3] = bg
    logo = Image.open(os.path.join(ASSETS, file)).convert("RGBA")
    if colour is not None:
        la = np.asarray(logo).copy()
        la[..., :3] = colour
        logo = Image.fromarray(la)
    if rotate:
        logo = logo.rotate(rotate, expand=True)
    w, h = x1 - x0, y1 - y0
    bw, bh = max(1, int(w * fill * squash)), max(1, int(h * fill))
    k = min(bw / logo.width, bh / logo.height)  # scale to fit, up or down
    logo = logo.resize((max(1, round(logo.width * k)), max(1, round(logo.height * k))), Image.LANCZOS)
    if squash != 1.0:  # the mesh stretches this area; pre-squash so it looks right in game
        logo = logo.resize((max(1, round(logo.width / squash)), logo.height), Image.LANCZOS)
    canvas = Image.fromarray(a[y0:y1, x0:x1, :3])
    canvas.paste(logo, ((w - logo.width) // 2, int((h - logo.height) * valign)), logo)
    a[y0:y1, x0:x1, :3] = np.asarray(canvas)


def apply_ops(img, ops, orig=None):
    a = np.asarray(img.convert("RGBA")).copy()
    o = np.asarray(orig.convert("RGBA")) if orig is not None else None
    for op in ops:
        kind = op["op"]
        if kind == "remap":
            _remap(a, op["box"], op["map"])
        elif kind == "fill":
            x0, y0, x1, y1 = op["box"]
            a[y0:y1, x0:x1, :3] = op["rgb"]
        elif kind == "bands":
            _bands(a, op["box"], op["bg"], op["bands"], op.get("vertical", False))
        elif kind == "restore":  # back to the original game pixels
            x0, y0, x1, y1 = op["box"]
            a[y0:y1, x0:x1] = o[y0:y1, x0:x1]
        elif kind == "logo":
            _logo(a, op["box"], op["file"], op.get("colour"), op.get("bg"), op.get("rotate", 0),
                  op.get("fill", 0.9), op.get("valign", 0.5), op.get("squash", 1.0))
        else:
            raise ValueError(kind)
    return Image.fromarray(a, "RGBA")


def sources(stem):
    fs = glob.glob(os.path.join(ROOT, "extract", "**", f"{stem}_*.pb"), recursive=True)
    return [f for f in fs if open(f, "rb").read(4) == b"burG"]


def current(src):
    rel = os.path.relpath(src, os.path.join(ROOT, "extract"))
    cur = os.path.join(FINAL, rel)
    return cur if os.path.exists(cur) else src


def run(jobs, only=None):
    with tempfile.TemporaryDirectory() as tmp:
        for stem, ops in jobs.items():
            if only and only not in stem:
                continue
            srcs = sources(stem)
            if not srcs:
                print("!! not extracted:", stem)
                continue
            big = max(srcs, key=lambda f: swatch.parse(open(f, "rb").read())["width"])
            canvas = swatch.to_image(open(current(big), "rb").read())[0]
            orig_full = swatch.to_image(open(big, "rb").read())[0]
            new_full = apply_ops(canvas, ops, orig_full)
            # fallbacks when a version won't fit its slot: step the logos down, then no logos
            ladder = [new_full] + [apply_ops(canvas, [dict(o, fill=o.get("fill", 0.9) * k) if o["op"] == "logo" else o for o in ops], orig_full)
                                   for k in (0.9, 0.8, 0.7, 0.6)]
            ladder.append(apply_ops(canvas, [o for o in ops if o["op"] != "logo"], orig_full))
            new_full.convert("RGB").save(os.path.join(ROOT, "preview", f"final_{stem}.png"))
            if np.array_equal(np.asarray(new_full), np.asarray(orig_full.convert("RGBA"))):
                # every op on this texture was undone (e.g. user chose keep original): ship the original
                for src in srcs:
                    dest = os.path.join(FINAL, os.path.relpath(src, os.path.join(ROOT, "extract")))
                    if os.path.exists(dest):
                        os.remove(dest)
                print(f"unchanged (all original) {stem}")
                continue
            old_full = np.asarray(canvas.convert("RGBA")).astype(np.int16)
            changed = np.abs(np.asarray(new_full).astype(np.int16) - old_full).max(axis=2) > 0
            for src in srcs:
                orig = open(src, "rb").read()
                base = open(current(src), "rb").read()
                inf = swatch.parse(orig)
                W, H = inf["width"], inf["height"]
                for attempt, full_img in enumerate(ladder):
                    resized = Image.merge("RGBA", [ch.resize((W, H), Image.LANCZOS) for ch in full_img.split()])
                    if (W, H) == full_img.size:
                        img = full_img
                    else:
                        # only replace where something changed; elsewhere keep this version's own pixels
                        cur = np.asarray(swatch.to_image(base)[0].convert("RGBA"))
                        m = Image.fromarray((changed * 255).astype(np.uint8)).resize((W, H), Image.BOX)
                        m = np.asarray(m.filter(ImageFilter.MaxFilter(5))) > 0
                        img = Image.fromarray(np.where(m[..., None], np.asarray(resized), cur), "RGBA")
                    data = brand.encode(img, orig, tmp, keep_alpha=False, base_bytes=base)
                    if install.fits_slot(os.path.basename(src), data):
                        break
                    print(f"   {os.path.basename(src)[-24:]} {W}x{H}: too big at step {attempt}" + (" (no logo left!)" if attempt == len(ladder) - 1 else ""))
                else:
                    print(f"   {os.path.basename(src)[-24:]}: nothing fits, keeping the previous version")
                    continue
                rel = os.path.relpath(src, os.path.join(ROOT, "extract"))
                dest = os.path.join(FINAL, rel)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "wb").write(data)
            print(f"built {stem} x{len(srcs)}")


if __name__ == "__main__":
    import jobs_plain
    run(jobs_plain.JOBS, sys.argv[1] if len(sys.argv) > 1 else None)
