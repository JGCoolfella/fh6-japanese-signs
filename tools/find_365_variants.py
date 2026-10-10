"""Find sign material variant blocks whose ink set looks like 365 Konbini (yellow + red + blue)."""
import os, re, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
import fh6minizip, install

def srgb(c):
    return int(round(255 * ((1.055 * max(c, 0) ** (1 / 2.4) - 0.055) if c > 0.0031308 else 12.92 * c)))

def near(rgb, t, tol):
    return sum((a - b) ** 2 for a, b in zip(rgb, t)) ** 0.5 <= tol

KEY = b"environment_signage_emissive.materialbin"
backups = {}
for b in os.listdir(install.BACKUP):
    m = re.match(r"GeoChunk(\d+)_(\d+)_", b)
    if m:
        backups[(int(m[1]), int(m[2]))] = True
for c in range(4):
    names = fh6minizip.load_names(os.path.join(install.TRACK, f"ChunkContentsMiniZip{c}.txt"))
    mz = fh6minizip.MiniZip(os.path.join(install.TRACK, f"GeoChunk{c}.minizip"))
    for i, n in names.items():
        base = os.path.basename(n)
        if not (base.startswith("sgn_") and "_cluster000" in base and base.endswith(".modelbin")):
            continue
        d = install.original_entry(c, i) if (c, i) in backups else mz.read(i)
        starts = [m.start() for m in re.finditer(re.escape(KEY), d)]
        for bi, st in enumerate(starts):
            en = starts[bi + 1] if bi + 1 < len(starts) else len(d)
            cols = {}
            for m in re.finditer(rb"\x03\x04(.{4})\x01.{20}.", d[st:en], re.S):
                v = d[st + m.end(): st + m.end() + 16]
                f = struct.unpack("<4f", v) if len(v) == 16 else None
                if f and all(0 <= x <= 1.0001 for x in f) and abs(f[3] - 1) < 1e-4:
                    cols[m.group(1).hex()] = tuple(srgb(x) for x in f[:3])
            vals = list(cols.values())
            has_y = any(near(v, (0xef, 0xd7, 0x28), 45) for v in vals)
            has_r = any(near(v, (0xee, 0x28, 0x2c), 45) for v in vals)
            has_b = any(near(v, (0x28, 0x40, 0x9a), 60) for v in vals)
            if has_y and has_r and has_b:
                print(f"{base.replace('_cluster000.i.modelbin','')} block {bi}: " +
                      " ".join(f"{k}=#%02x%02x%02x" % v for k, v in cols.items()))
