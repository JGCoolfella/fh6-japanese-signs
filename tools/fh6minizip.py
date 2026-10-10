"""Selective extractor for Forza Horizon 6 PGZP (.minizip) archives.

Layout (version 101), worked out from media/Tracks/Brio/GeoChunk*.minizip:
  0x00  'PGZP', u32 version, u32 header size (0x20), u32 entry count, u32 index count,
        u32 block size (512), u32 block count, u32 0
  0x20  u32[index count] index table (identity unless the archive de-duplicates data)
  then  u32 count, followed by `block count` blocks. Each block starts with an
        8-byte-aligned u64 data base, then up to 512 entries of 12 bytes:
          u32 offset (relative to block base), u32 size, u32 (index << 16) | flags
        flags low byte 0x1f = LZ4 block, 0x08 = raw deflate (size = uncompressed size),
        0x00 = stored (size = stored size).
        After the last block comes one more u64: the end of the data.
Entry names come from the matching ChunkContentsMiniZip<N>.txt: line i names entry i.
"""
import argparse
import fnmatch
import os
import struct
import sys
import zlib

import lz4.block


class MiniZip:
    def __init__(self, path):
        self.path = path
        self.f = open(path, "rb")
        magic, ver, _, count, index_count, block_size, blocks, _ = struct.unpack("<4sIIIIIII", self.f.read(0x20))
        if magic != b"PGZP":
            raise ValueError(f"{path}: not a PGZP archive")
        self.version, self.count, self.block_size = ver, count, block_size
        # Group table: group N (the "|N" in ChunkContentsMiniZip*.txt) starts at entry index[N].
        self.index = list(struct.unpack(f"<{index_count}I", self.f.read(index_count * 4)))
        pos = 0x20 + index_count * 4
        self.f.seek(pos)
        table = self.f.read(16 + count * 12 + blocks * 16 + 16)
        p = 0
        (n,) = struct.unpack_from("<I", table, p)
        p += 4
        if n != count:
            raise ValueError(f"{path}: table count {n} != header count {count}")
        self.entries = []  # (abs_offset, size, flags, block_base, block_index)
        bases = []
        for b in range(blocks):
            p += (-(pos + p)) % 8
            (base,) = struct.unpack_from("<Q", table, p)
            p += 8
            bases.append(base)
            for _ in range(min(block_size, count - b * block_size)):
                off, size, c = struct.unpack_from("<III", table, p)
                p += 12
                self.entries.append([base + off, size, c & 0xFFFF, b])
        p += (-(pos + p)) % 8
        (end,) = struct.unpack_from("<Q", table, p)
        bases.append(max(end, os.path.getsize(path)))
        # Entries can share data (GeoChunk0 de-duplicates), so the stored length of an
        # entry is the distance to the next distinct start offset or block boundary.
        import bisect
        starts = sorted({e[0] for e in self.entries} | set(bases))
        for e in self.entries:
            e.append(starts[bisect.bisect_right(starts, e[0])] - e[0])

    def read(self, i):
        off, size, flags, _, stored = self.entries[i]
        self.f.seek(off)
        data = self.f.read(stored)
        codec = flags & 0xFF
        if codec == 0x08:
            return zlib.decompressobj(-15).decompress(data)[:size]
        if codec:
            # Stored length includes alignment padding; trim until LZ4 decodes cleanly.
            for trim in range(0, 64):
                try:
                    return lz4.block.decompress(data[: stored - trim], uncompressed_size=size)
                except lz4.block.LZ4BlockError:
                    continue
            raise ValueError(f"entry {i}: LZ4 decode failed (flags {flags:#x})")
        return data[:size]


def load_names(contents_txt):
    """Entry index -> path. Line i of ChunkContentsMiniZip<N>.txt is entry i of the archive
    (the trailing "|N" is a group number, equal to i only when every group has one entry)."""
    names = {}
    with open(contents_txt, encoding="utf-8", errors="replace") as f:
        i = 0
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            path = line.rsplit("|", 1)[0].replace("<PREZIPPED>", "")
            # Keep the path from 'tracks\' onwards, matching the game's media layout.
            cut = path.lower().find("\\tracks\\")
            rel = path[cut + 1:] if cut >= 0 else path
            names[i] = rel.replace("\\", "/")
            i += 1
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("track_dir", help="e.g. media/Tracks/Brio")
    ap.add_argument("pattern", help="fnmatch pattern on the file path, e.g. '*sgn_cty_shop_*bclr*'")
    ap.add_argument("-o", "--out", default="extract", help="output directory")
    ap.add_argument("--list", action="store_true", help="only list matches")
    args = ap.parse_args()

    total = 0
    for chunk in range(16):
        mz_path = os.path.join(args.track_dir, f"GeoChunk{chunk}.minizip")
        txt = os.path.join(args.track_dir, f"ChunkContentsMiniZip{chunk}.txt")
        if not (os.path.exists(mz_path) and os.path.exists(txt)):
            continue
        names = load_names(txt)
        hits = [i for i, n in names.items() if fnmatch.fnmatch(n.lower(), args.pattern.lower())]
        if not hits:
            continue
        mz = MiniZip(mz_path)
        for i in sorted(hits):
            name = names[i]
            if args.list:
                e = mz.entries[i]
                print(f"GeoChunk{chunk}[{i}] {e[1]:>9} flags={e[2]:#06x} {name}")
            else:
                dest = os.path.join(args.out, name)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as out:
                    out.write(mz.read(i))
            total += 1
    print(f"{total} matching entries", file=sys.stderr)


if __name__ == "__main__":
    main()
