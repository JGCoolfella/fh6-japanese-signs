"""List which mask sheet and which atlas cell every material variant of a tinted sign uses.

Material params (per variant block):
  e857e8a4  float2  atlas grid (columns, rows)
  f9b99d7c  float2  cell (column, row), 1-based; absent = (1, 1)
  53e6b395  5 bytes texture reference (00 + 4-byte id) -> which mask sheet
Usage: python tools/variants.py <model stem>
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import install
import list_inks


def variant_table(data):
    starts = [m.start() for m in re.finditer(list_inks.KEY_RE, data)]
    out = []
    for bi, st in enumerate(starts):
        en = starts[bi + 1] if bi + 1 < len(starts) else len(data)
        blk = data[st:en]
        grid, cell, tex = (1.0, 1.0), (1.0, 1.0), None
        ms = list(re.finditer(rb"\x03\x04(.{4})\x01(.{20})(.)", blk, re.S))
        for k, m in enumerate(ms):
            vs = m.end()
            ve = ms[k + 1].start() if k + 1 < len(ms) else min(len(blk), vs + 16)
            val = blk[vs:ve]
            key = m.group(1).hex()
            if key == "e857e8a4" and len(val) == 8:
                grid = struct.unpack("<2f", val)
            elif key == "f9b99d7c" and len(val) == 8:
                cell = struct.unpack("<2f", val)
            elif key == "53e6b395":
                tex = val[1:5].hex()
        cols = list_inks.blocks(data)[bi][2]
        out.append((bi, tex, tuple(int(g) for g in grid), tuple(int(c) for c in cell),
                    {k: "#%02x%02x%02x" % cols[k] for k in list_inks.ORDER if k in cols}))
    return out


def main():
    model = sys.argv[1]
    lookup = install.chunk_lookup()
    c, i = lookup[next(n for n in lookup if n.startswith(model + "_cluster000"))]
    for bi, tex, grid, cell, cols in variant_table(install.original_entry(c, i)):
        print(f"block {bi:2}  tex {tex}  grid {grid}  cell {cell}  inks {cols}")


if __name__ == "__main__":
    main()
