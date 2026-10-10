"""List sign models whose material variant blocks use a given ink colour (default: 365 yellow)."""
import os, re, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
import fh6minizip, install

TARGET = tuple(int(sys.argv[1][i:i + 2], 16) for i in (1, 3, 5)) if len(sys.argv) > 1 else (0xef, 0xd7, 0x28)
TOL = 40

def srgb(c):
    return int(round(255 * ((1.055 * max(c, 0) ** (1 / 2.4) - 0.055) if c > 0.0031308 else 12.92 * c)))

hits = {}
for c in range(4):
    names = fh6minizip.load_names(os.path.join(install.TRACK, f"ChunkContentsMiniZip{c}.txt"))
    mz = fh6minizip.MiniZip(os.path.join(install.TRACK, f"GeoChunk{c}.minizip"))
    for i, n in names.items():
        if not n.endswith(".modelbin") or b"" is None:
            continue
        base = os.path.basename(n)
        if not re.search(r"^(sgn|bld|prp|inf)_", base):
            continue
        try:
            d = mz.read(i)
        except Exception:
            continue
        if b"materialbin" not in d:
            continue
        found = []
        for m in re.finditer(rb"\x03\x04(.{4})\x01.{20}.", d, re.S):
            v = d[m.end():m.end() + 16]
            if len(v) < 16:
                continue
            f = struct.unpack("<4f", v)
            if not (all(0 <= x <= 1.0001 for x in f) and abs(f[3] - 1) < 1e-4):
                continue
            rgb = tuple(srgb(x) for x in f[:3])
            if sum((a - b) ** 2 for a, b in zip(rgb, TARGET)) ** 0.5 <= TOL:
                found.append("#%02x%02x%02x" % rgb)
        if found:
            key = re.sub(r"_cluster\d+|_square\d+|\.i\.modelbin|\.modelbin", "", base)
            hits.setdefault(key, set()).update(found)
for k, v in sorted(hits.items()):
    print(k, sorted(v))
print(len(hits), "assets")
