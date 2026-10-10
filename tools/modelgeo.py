"""Minimal ForzaTech .modelbin geometry reader (enough to measure how textures map onto meshes).

Bundle: 'burG' header, then 24-byte blob entries (tag, version, metadata count/offset, data offset/size).
  VLay  vertex layout: semantic names + D3D12-style elements (name, index, slot, class, DXGI format, offset, step)
  VerB  vertex buffer: u32 count, u32 size, u16 stride, u16, u32 -> data
  IndB  index buffer:  u32 count, u32 size, u16 stride, u16, u32 -> data
  Mesh  ... IndexStart, BaseVertex, IndexCount, PrimCount, ..., vertex-buffer usages {VerB, slot, stride, offset},
        tail: 5 x UV transform (4 floats: min/max u, min/max v), position scale (4f), position offset (4f)
Positions are R16G16B16A16_SNORM * scale + offset; texcoords R16G16_UNORM remapped by the UV transform.
"""
import struct

import numpy as np

FMT_SIZE = {2: 16, 6: 12, 10: 8, 13: 8, 16: 8, 24: 4, 28: 4, 31: 4, 34: 4, 35: 4, 37: 4, 41: 4, 54: 2, 56: 2, 61: 1}


def blobs(d):
    if d[:4] != b"burG":
        raise ValueError("not a bundle")
    n = struct.unpack_from("<I", d, 16)[0]
    out = []
    for k in range(n):
        tag, va, vb, mc, mo, do, ds, us = struct.unpack_from("<4sBBHIIII", d, 20 + 24 * k)
        out.append((tag[::-1].decode("latin1"), do, ds))
    return out


def vlay(b):
    n = struct.unpack_from("<H", b, 0)[0]
    p, names = 2, []
    for _ in range(n):
        ln = struct.unpack_from("<I", b, p)[0]
        names.append(b[p + 4:p + 4 + ln].decode("latin1"))
        p += 4 + ln
    ne = struct.unpack_from("<H", b, p)[0]
    p += 2
    els, slot_off = [], {}
    for _ in range(ne):
        ni, si, slot, cls, fmt, off, step = struct.unpack_from("<HHHHIII", b, p)
        p += 20
        o = slot_off.get(slot, 0) if off == 0xFFFFFFFF else off
        slot_off[slot] = o + FMT_SIZE.get(fmt, 4)
        els.append({"name": names[ni], "index": si, "slot": slot, "fmt": fmt, "offset": o})
    return els, slot_off


def _mesh_ranges(b):
    """(IndexStart, BaseVertex, IndexCount, PrimCount, position of that record)."""
    for p in range(0, len(b) - 16, 2):
        s, base, cnt, prim = struct.unpack_from("<iiII", b, p)
        if prim and cnt == 3 * prim and cnt < 10 ** 7 and 0 <= s < 10 ** 7 and abs(base) < 10 ** 7:
            return s, base, cnt, prim, p
    return None


def _usages(b, after):
    """Vertex buffer usages: count, then {VerB index, slot, stride, offset, 0} (u32 each)."""
    for p in range(after, len(b) - 20, 2):
        c = struct.unpack_from("<I", b, p)[0]
        if not 1 <= c <= 6 or p + 4 + 20 * c > len(b) - 112:
            continue
        us = [struct.unpack_from("<IIII", b, p + 4 + 20 * k) for k in range(c)]
        if all(u[2] in (4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48) and u[0] < 64 and u[1] < 8 for u in us) and us[0][1] == 0:
            return us
    return None


def meshes(d):
    """[{'pos': (n,3,3) float, 'uv': {k: (n,3,2)}}] triangles of every mesh."""
    bl = blobs(d)
    verbs = [(do, ds) for t, do, ds in bl if t == "VerB"]
    lays = [vlay(d[do:do + ds]) for t, do, ds in bl if t == "VLay"]
    ib = next(((do, ds) for t, do, ds in bl if t == "IndB"), None)
    if ib is None:
        return []
    icount, isize, istride = struct.unpack_from("<IIH", d, ib[0])
    idx = np.frombuffer(d, np.uint16 if istride == 2 else np.uint32, icount, ib[0] + 16).astype(np.int64)
    out = []
    for t, do, ds in bl:
        if t != "Mesh":
            continue
        b = d[do:do + ds]
        r = _mesh_ranges(b)
        if not r:
            continue
        s, base, cnt, prim, rp = r
        us = _usages(b, rp + 16)
        if not us:
            continue
        tail = np.frombuffer(b[-112:], np.float32)
        uvt, scale, offset = tail[:20].reshape(5, 4), tail[20:23], tail[24:27]
        tri = idx[s:s + cnt] + base
        pos_u = next((u for u in us if u[1] == 0), None)
        attr = [u for u in us if u[1] != 0]
        if pos_u is None:
            continue
        vb_off = verbs[pos_u[0]][0] + 16 + pos_u[3]
        nv = int(tri.max()) + 1
        raw = np.frombuffer(d, np.int16, nv * pos_u[2] // 2, vb_off).reshape(nv, pos_u[2] // 2)[:, :3] / 32767.0
        pos = raw * scale + offset
        # layout whose slot-1 stride matches this mesh's attribute buffer
        uv = {}
        for a in attr:
            lay = next((L for L, so in lays if so.get(a[1]) == a[2]), None)
            if not lay:
                continue
            base_off = verbs[a[0]][0] + 16 + a[3]
            for e in lay:
                if e["slot"] == a[1] and e["name"] == "TEXCOORD" and e["fmt"] in (35, 37, 34):
                    rows = np.frombuffer(d, np.uint8, nv * a[2], base_off).reshape(nv, a[2])[:, e["offset"]:e["offset"] + 4]
                    if e["fmt"] == 34:
                        v = rows.copy().view(np.float16).astype(np.float32)
                    else:
                        v = rows.copy().view(np.uint16 if e["fmt"] == 35 else np.int16).astype(np.float32)
                        v = v / (65535.0 if e["fmt"] == 35 else 32767.0)
                    k = e["index"]
                    if k < 5:
                        u0, u1, v0, v1 = uvt[k]
                        v = np.stack([u0 + v[:, 0] * (u1 - u0), v0 + v[:, 1] * (v1 - v0)], 1)
                    uv[k] = v
        tris = tri.reshape(-1, 3)
        out.append({"pos": pos[tris], "uv": {k: v[tris] for k, v in uv.items()}})
    return out


def stretch(ms, region=None, tex=0):
    """Area-weighted median of (metres per unit U) / (metres per unit V) over triangles whose UV
    centroid lies in region (u0, v0, u1, v1). Returns (ratio, world area used) or (None, 0)."""
    ratios, weights = [], []
    for m in ms:
        if tex not in m["uv"]:
            continue
        P, T = m["pos"], m["uv"][tex]
        e1, e2 = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0]
        d1, d2 = T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]
        det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
        ok = np.abs(det) > 1e-9
        if region is not None:
            c = T.mean(1)
            ok &= (c[:, 0] >= region[0]) & (c[:, 0] <= region[2]) & (c[:, 1] >= region[1]) & (c[:, 1] <= region[3])
        if not ok.any():
            continue
        e1, e2, d1, d2, det = e1[ok], e2[ok], d1[ok], d2[ok], det[ok]
        dPdu = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) / det[:, None]
        dPdv = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) / det[:, None]
        lu, lv = np.linalg.norm(dPdu, axis=1), np.linalg.norm(dPdv, axis=1)
        area = 0.5 * np.linalg.norm(np.cross(e1, e2), axis=1)
        good = (lu > 0) & (lv > 0)
        ratios.append(lu[good] / lv[good])
        weights.append(area[good])
    if not ratios:
        return None, 0.0
    r, w = np.concatenate(ratios), np.concatenate(weights)
    if w.sum() <= 0:
        return None, 0.0
    o = np.argsort(r)
    cw = np.cumsum(w[o])
    return float(r[o][np.searchsorted(cw, cw[-1] / 2)]), float(w.sum())
