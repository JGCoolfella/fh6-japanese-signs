"""Turn the user's custom images (catalogue/choices/<ID>_custom.png) into clean, high-res assets
in assets/custom/. Flat two-colour artwork is rebuilt sharp: upscale, snap every pixel to the
artwork's own colours, then downsample (anti-aliased edges). UNIQLO layouts are recomposed from
the high-res logo files using the proportions of the user's image.
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(ROOT, "catalogue", "choices")
ASSETS = os.path.join(ROOT, "assets")
OUT = os.path.join(ASSETS, "custom")


def palette_snap(src, colours, up=8, down=2):
    """Rebuild flat artwork: upscale, assign each pixel its nearest palette colour, downsample."""
    im = Image.open(src).convert("RGB")
    big = im.resize((im.width * up, im.height * up), Image.BICUBIC)
    a = np.asarray(big, np.float32)
    pal = np.array(colours, np.float32)
    idx = ((a[:, :, None, :] - pal[None, None]) ** 2).sum(-1).argmin(-1)
    snapped = Image.fromarray(pal[idx].astype(np.uint8))
    return snapped.resize((big.width // down, big.height // down), Image.LANCZOS)


def dominant(src, n=2):
    a = np.asarray(Image.open(src).convert("RGB")).reshape(-1, 3) // 8 * 8 + 4
    vals, cnt = np.unique(a, axis=0, return_counts=True)
    return [tuple(int(x) for x in v) for v in vals[np.argsort(-cnt)[:n]]]


def red_boxes(src):
    """Bounding boxes (x0, y0, x1, y1) of the red squares in a UNIQLO layout image."""
    from scipy import ndimage
    a = np.asarray(Image.open(src).convert("RGBA")).astype(int)
    red = (a[..., 0] > 180) & (a[..., 1] < 90) & (a[..., 3] > 128)
    red = ndimage.binary_closing(red, iterations=6)
    lab, n = ndimage.label(ndimage.binary_fill_holes(red))
    sl = sorted(ndimage.find_objects(lab), key=lambda s: -(s[0].stop - s[0].start) * (s[1].stop - s[1].start))[:2]
    return sorted(((s[1].start, s[0].start, s[1].stop, s[0].stop) for s in sl), key=lambda b: (b[1], b[0])), a.shape[1], a.shape[0]


def uniqlo_layout(src, dest, bg=(255, 255, 255, 255)):
    """Recreate the user's arrangement of the two UNIQLO squares at high resolution."""
    boxes, W, H = red_boxes(src)
    k = 1600 / max(b[2] - b[0] for b in boxes)
    canvas = Image.new("RGBA", (round(W * k), round(H * k)), bg)
    for b, f in zip(boxes, ("uniqlo_logo.png", "uniqlo_logo_en.png")):
        logo = Image.open(os.path.join(ASSETS, f)).convert("RGBA")
        bw, bh = round((b[2] - b[0]) * k), round((b[3] - b[1]) * k)
        canvas.alpha_composite(logo.resize((bw, bh), Image.LANCZOS), (round(b[0] * k), round(b[1] * k)))
    canvas.save(dest)
    return [tuple(round(v * k) for v in b) for b in boxes], canvas.size


def main():
    os.makedirs(OUT, exist_ok=True)
    print("uniqlo_stack", uniqlo_layout(os.path.join(CH, "P001_custom.png"), os.path.join(OUT, "uniqlo_stack.png")))
    print("uniqlo_pair", uniqlo_layout(os.path.join(CH, "T071_custom.png"), os.path.join(OUT, "uniqlo_pair.png")))
    print("uniqlo_pair_wide", uniqlo_layout(os.path.join(CH, "P214_custom.png"), os.path.join(OUT, "uniqlo_pair_wide.png")))
    Image.open(os.path.join(ASSETS, "uniqlo_logo.png")).convert("RGBA").save(os.path.join(OUT, "uniqlo_square.png"))
    for name, src in (("lawson_station", "P021"), ("taito_game", "P167"), ("taito_wide", "P129")):
        f = os.path.join(CH, src + "_custom.png")
        cols = dominant(f, 2)
        img = palette_snap(f, cols)
        img.save(os.path.join(OUT, name + ".png"))
        print(name, cols, img.size)
    # Starbucks wordmark: already large; keep the user's art (transparent background)
    Image.open(os.path.join(CH, "T118_custom.png")).convert("RGBA").save(os.path.join(OUT, "starbucks_word.png"))
    # SoftBank: high-res logo file with the user's colours (yellow bars, dark grey wordmark)
    sb = np.asarray(Image.open(os.path.join(ASSETS, "softbank_logo.png")).convert("RGBA")).copy()
    cols = np.nonzero(sb[..., 3].max(0) > 128)[0]
    bar_end = cols[np.nonzero(np.diff(cols) > 5)[0][0]] + 1          # the "=" mark is the first glyph
    sb[:, :bar_end, :3] = (248, 188, 8)
    sb[:, bar_end:, :3] = (80, 80, 80)
    Image.fromarray(sb).save(os.path.join(OUT, "softbank.png"))
    # 64px stickers: upright logo on white, built from the high-res logo files
    for logo, name, fill in (("tomica_logo.png", "tomica_sticker", 0.9), ("mitsuya_logo.png", "mitsuya_sticker", 0.9)):
        S = 512
        img = Image.new("RGBA", (S, S), (246, 246, 246, 255))
        lg = Image.open(os.path.join(ASSETS, logo)).convert("RGBA")
        k = min(S * fill / lg.width, S * fill / lg.height)
        lg = lg.resize((round(lg.width * k), round(lg.height * k)), Image.LANCZOS)
        img.alpha_composite(lg, ((S - lg.width) // 2, (S - lg.height) // 2))
        img.convert("RGB").save(os.path.join(OUT, name + ".png"))


if __name__ == "__main__":
    main()


def trim_all():
    """<name>_t.png = artwork cropped to its content (plus a small margin); bg colour recorded in
    custom/bg.json so signs can be filled with the artwork's own background colour."""
    import glob
    import json
    bgs = {}
    for f in sorted(glob.glob(os.path.join(OUT, "*.png"))):
        name = os.path.basename(f)[:-4]
        if name.endswith("_t"):
            continue
        a = np.asarray(Image.open(f).convert("RGBA")).astype(int)
        border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
        if border[:, 3].min() < 250:
            bg = (246, 246, 246)
            content = a[..., 3] > 16
        else:
            vals, cnt = np.unique(border[:, :3] // 4 * 4, axis=0, return_counts=True)
            bg = tuple(int(v) + 2 for v in vals[cnt.argmax()])
            content = np.abs(a[..., :3] - np.array(bg)).max(-1) > 40
        ys, xs = np.nonzero(content)
        m = round(0.02 * max(a.shape[:2]))
        box = (max(0, xs.min() - m), max(0, ys.min() - m), min(a.shape[1], xs.max() + 1 + m), min(a.shape[0], ys.max() + 1 + m))
        Image.open(f).convert("RGBA").crop(box).save(os.path.join(OUT, name + "_t.png"))
        bgs[name] = bg
    json.dump(bgs, open(os.path.join(OUT, "bg.json"), "w"), indent=1)
    print(bgs)


if __name__ == "__main__":
    trim_all()


def familymart_blade(box_w=193, box_h=654):
    """P197 high-rise blade sign: the user's FamilyMart logo turned to read top-to-bottom, spanning
    the full height; the extra width goes into the white either side of the lettering (no stretching)."""
    im = Image.open(os.path.join(CH, "P197_custom.png")).convert("RGBA")
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
    flat.alpha_composite(im)
    rot = np.asarray(flat.convert("RGB").rotate(-90, expand=True))       # clockwise, like the original sign
    H, W = rot.shape[:2]
    need = round(box_w * H / box_h)                                       # width for the box aspect at this height
    # band columns from the first row (the logo's left edge holds only the two colour bands)
    edge = np.abs(rot[2].astype(int) - 255).max(-1) > 60
    cols = np.nonzero(edge)[0]
    split = np.nonzero(np.diff(cols) > 1)[0][0]
    left_gap, right_gap = cols[split] + 1, cols[split + 1]          # right after the left band / before the right band
    pad = max(0, need - W)
    col = np.full((H, 1, 3), 255, np.uint8)
    out = np.concatenate([rot[:, :left_gap], np.repeat(col, pad // 2, 1), rot[:, left_gap:right_gap],
                          np.repeat(col, pad - pad // 2, 1), rot[:, right_gap:]], 1)
    out = out.copy()
    out[(out.astype(int).min(-1) > 225)] = 255          # clean faint anti-alias seams to pure white
    Image.fromarray(out).save(os.path.join(OUT, "familymart_blade.png"))
    print("familymart_blade", out.shape[1], "x", out.shape[0], "(box", box_w, "x", box_h, ")")


def lawson_word():
    """T125: just the LAWSON lettering from the user's image (the pink band is drawn full-length separately)."""
    a = np.asarray(Image.open(os.path.join(CH, "T125_custom.png")).convert("RGB")).astype(int)
    blue = (a[..., 2] > 150) & (a[..., 0] < 80)
    ys, xs = np.nonzero(blue)
    m = 6
    crop = a[ys.min() - m:ys.max() + 1 + m, xs.min() - m:xs.max() + 1 + m]
    # transparent background: alpha = how blue the pixel is (white -> 0), so it can be re-inked
    alpha = np.clip((255 - crop[..., 0]) / (255 - 0.0) * 255 * 1.05, 0, 255).astype(np.uint8)
    rgba = np.dstack([np.zeros_like(alpha), np.full_like(alpha, 88), np.full_like(alpha, 207), alpha])
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "lawson_word_t.png"))
    print("lawson_word rows", ys.min(), ys.max(), "of", a.shape[0])


if __name__ == "__main__":
    familymart_blade()
    lawson_word()


def lawson_t125_wide(area_w=1024, area_h=72):
    """T125: the user's improved strip (blue side bands, LAWSON, pink line), widened to the strip's
    shape by extending the bands outward (the lettering keeps its proportions)."""
    im = Image.open(os.path.join(CH, "T125_custom.png")).convert("RGBA")
    flat = Image.new("RGBA", im.size, (255, 255, 255, 255))
    flat.alpha_composite(im)
    a = np.asarray(flat.convert("RGB"))
    H, W = a.shape[:2]
    need = round(area_w * H / area_h)
    pad = max(0, need - W)
    left = np.repeat(a[:, 4:5], pad // 2, 1)
    right = np.repeat(a[:, W - 5:W - 4], pad - pad // 2, 1)
    out = np.concatenate([left, a, right], 1)
    Image.fromarray(out).save(os.path.join(OUT, "lawson_t125_wide.png"))
    print("lawson_t125_wide", out.shape[1], "x", out.shape[0])


def familymart_word():
    """Just the FamilyMart lettering (transparent) from the user's logo, for strips with full-length bands."""
    a = np.asarray(Image.open(os.path.join(CH, "T073_custom.png")).convert("RGB")).astype(int)
    H = a.shape[0]
    rows = slice(int(H * 0.27), int(H * 0.91))          # between the green top band and the blue bottom band
    c = a[rows]
    alpha = np.clip((255 - c.min(-1)) / (255 - 150) * 255, 0, 255).astype(np.uint8)
    ys, xs = np.nonzero(alpha > 60)
    alpha = alpha[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    rgba = np.dstack([np.full_like(alpha, 20), np.full_like(alpha, 170), np.full_like(alpha, 226), alpha])
    Image.fromarray(rgba, "RGBA").save(os.path.join(OUT, "familymart_word_t.png"))
    print("familymart_word", alpha.shape[::-1])


def uniqlo_pair_vertical():
    """P216: the user's side-by-side UNIQLO pair turned 270 deg clockwise (as set in the catalogue)."""
    im = Image.open(os.path.join(OUT, "uniqlo_pair_t.png")).convert("RGBA").rotate(90, expand=True)
    im.save(os.path.join(OUT, "uniqlo_pair_v.png"))
    print("uniqlo_pair_v", im.size)


if __name__ == "__main__":
    lawson_t125_wide()
    familymart_word()
    uniqlo_pair_vertical()
