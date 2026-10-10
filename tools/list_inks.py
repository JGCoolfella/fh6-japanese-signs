"""Print the ink colours of every signage material block in a sign model (by asset name)."""
import os, re, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
import fh6minizip, install

KEY_RE = rb"environment_signage\w*\.materialbin"  # incl. _emissive, _emissive_animated, _mural
ORDER = ["d413b073", "2ce6ce9c", "e81544ff", "41157c29", "26159464"]  # base, R, G, B, A

def srgb(c):
    return int(round(255 * ((1.055 * max(c, 0) ** (1 / 2.4) - 0.055) if c > 0.0031308 else 12.92 * c)))

def blocks(data):
    starts = [m.start() for m in re.finditer(KEY_RE, data)]
    out = []
    for bi, st in enumerate(starts):
        en = starts[bi + 1] if bi + 1 < len(starts) else len(data)
        cols = {}
        for m in re.finditer(rb"\x03\x04(.{4})\x01.{20}.", data[st:en], re.S):
            v = data[st + m.end(): st + m.end() + 16]
            if len(v) == 16:
                f = struct.unpack("<4f", v)
                if all(0 <= x <= 1.0001 for x in f) and abs(f[3] - 1) < 1e-4:
                    cols[m.group(1).hex()] = tuple(srgb(x) for x in f[:3])
        out.append((st, en, cols))
    return out

if __name__ == "__main__":
    want = sys.argv[1]
    lookup = install.chunk_lookup()
    name = next(n for n in sorted(lookup) if want in n and n.endswith("cluster000.i.modelbin"))
    c, i = lookup[name]
    for bi, (st, en, cols) in enumerate(blocks(install.original_entry(c, i))):
        print(f"block {bi:2}: " + " ".join(("#%02x%02x%02x" % cols[k]) if k in cols else "   -   " for k in ORDER))
