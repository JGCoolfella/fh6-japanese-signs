"""Split an atlas texture into its individual sign pieces (boxes in full-res pixels).

Recursive XY-cut: a region is cut along rows/columns that are either a uniform gutter
or a hard straight seam spanning the whole region (tiles packed edge to edge). Plain
single-colour strips produced by the cuts are merged back into their neighbour, so a sign
with full-width stripes stays one piece.
"""
import numpy as np

MIN = 12          # smallest piece side (in work pixels)
WORK = 512        # analysis resolution (longest side)
GUTTERS = False   # also cut at uniform gutters (decal sheets on a shared background)


def _lines(sub, axis):
    """Cut candidates along one axis: list of (start, end) of 'separator' runs."""
    a = sub if axis == 0 else sub.transpose(1, 0, 2)
    n = a.shape[0]
    std = a.std(axis=1).mean(axis=1)                          # per row: variation along the row
    diff = np.abs(np.diff(a, axis=0)).sum(axis=2)            # (n-1, w)
    seam = (diff > 45).mean(axis=1)                          # fraction of the row that is a hard edge
    sep = []
    gut = (std < 4.0) & GUTTERS
    y = 0
    while y < n:
        if gut[y]:
            e = y
            while e + 1 < n and gut[e + 1]:
                e += 1
            sep.append((y, e + 1))
            y = e + 1
        else:
            y += 1
    for y in np.nonzero(seam > 0.92)[0]:
        sep.append((y + 1, y + 1))                           # zero-width cut between rows y and y+1
    return sorted(sep)


def _split(sep, n):
    parts, cur = [], 0
    for s, e in sep:
        if s - cur >= MIN:
            parts.append((cur, s))
        cur = max(cur, e)
    if n - cur >= MIN:
        parts.append((cur, n))
    return parts


def _plain(sub):
    return sub.reshape(-1, 3).std(axis=0).mean() < 9


def _xycut(img, box, depth, out):
    x0, y0, x1, y1 = box
    sub = img[y0:y1, x0:x1]
    if depth > 8 or min(x1 - x0, y1 - y0) < 2 * MIN:
        out.append(box)
        return
    for axis in (0, 1):
        n = sub.shape[axis]
        parts = _split(_lines(sub, axis), n)
        if len(parts) >= 2 or (len(parts) == 1 and parts[0] != (0, n)):
            parts = _merge_plain(sub, parts, axis)
            if len(parts) == 1 and parts[0] == (0, n):
                continue
            for s, e in parts:
                nb = (x0, y0 + s, x1, y0 + e) if axis == 0 else (x0 + s, y0, x0 + e, y1)
                _xycut(img, nb, depth + 1, out)
            return
    out.append(box)


def _merge_plain(sub, parts, axis):
    """Fold thin single-colour stripes into the neighbouring piece (keeps striped signs whole)."""
    def piece(p):
        s, e = p
        return sub[s:e] if axis == 0 else sub[:, s:e]
    merged = list(parts)
    changed = True
    while changed and len(merged) > 1:
        changed = False
        for k, p in enumerate(merged):
            span = p[1] - p[0]
            other = sub.shape[1 - axis]
            if _plain(piece(p)) and span < 0.35 * other:
                # merge with the touching neighbour (gap-free) if any
                nb = None
                if k + 1 < len(merged) and merged[k + 1][0] - p[1] <= 1:
                    nb = k + 1
                elif k > 0 and p[0] - merged[k - 1][1] <= 1:
                    nb = k - 1
                if nb is None:
                    continue
                a, b = sorted((k, nb))
                merged[a:b + 1] = [(merged[a][0], merged[b][1])]
                changed = True
                break
    return merged


def _trim(img, box):
    x0, y0, x1, y1 = box
    sub = img[y0:y1, x0:x1]
    rows = sub.std(axis=1).mean(axis=1) >= 4
    cols = sub.std(axis=0).mean(axis=1) >= 4
    if rows.any() and cols.any():
        ys, xs = np.nonzero(rows)[0], np.nonzero(cols)[0]
        return (x0 + xs[0], y0 + ys[0], x0 + xs[-1] + 1, y0 + ys[-1] + 1)
    return box


def segment(rgb, region=None):
    """rgb: HxWx3 uint8. Returns [(x0, y0, x1, y1)] in rgb pixel coords."""
    H, W = rgb.shape[:2]
    k = min(1.0, WORK / max(H, W))
    from PIL import Image
    small = np.asarray(Image.fromarray(rgb).resize((max(1, round(W * k)), max(1, round(H * k))), Image.BOX)).astype(np.float32)
    h, w = small.shape[:2]
    if region:
        rx0, ry0, rx1, ry1 = region
        box = (round(rx0 * k), round(ry0 * k), round(rx1 * k), round(ry1 * k))
    else:
        box = (0, 0, w, h)
    out = []
    _xycut(small, box, 0, out)
    res = []
    for b in out:
        sub = small[b[1]:b[3], b[0]:b[2]]
        if _plain(sub):
            continue
        b = _trim(small, b)
        x0, y0, x1, y1 = (round(v / k) for v in b)
        res.append((max(0, x0), max(0, y0), min(W, x1), min(H, y1)))
    return res
