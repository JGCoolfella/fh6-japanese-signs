"""Install / uninstall built texture mods.

  python tools/install.py loose <brand>     copy textures into <game>/mediapc (originals untouched)
  python tools/install.py patch <brand>     write textures into the GeoChunk archive in place
                                            (backs up every byte it overwrites first)
  python tools/install.py uninstall         remove loose files and restore any patched bytes

Everything installed is recorded in _modwork/installed.json.
"""
import glob
import json
import os
import shutil
import struct
import sys
import zlib

import lz4.block

sys.path.insert(0, os.path.dirname(__file__))
import fh6minizip

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GAME = os.environ.get("FH6_GAME") or os.path.dirname(ROOT)  # game folder (default: parent of the repo)
TRACK = os.path.join(GAME, "media", "Tracks", "Brio")
STATE = os.path.join(ROOT, "installed.json")
BACKUP = os.path.join(ROOT, "backup")


def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"loose": [], "patch": []}


def save_state(state):
    json.dump(state, open(STATE, "w"), indent=1)


def built_files(brand):
    base = os.path.join(ROOT, "build", brand)
    files = [f for f in glob.glob(os.path.join(base, "**", "*"), recursive=True)
             if f.endswith((".pb", ".modelbin"))]
    if not files:
        sys.exit(f"Nothing built for {brand}. Run: python tools/brand.py {brand}")
    # rel looks like tracks/brio/scene/models/...
    return [(f, os.path.relpath(f, base).replace("\\", "/")) for f in files]


def install_loose(brand):
    state = load_state()
    for src, rel in built_files(brand):
        # Mirror media/Tracks/Brio/... under mediapc/, as .pb and as .swatchbin.
        parts = rel.split("/")
        rel_media = "/".join(["Tracks", "Brio"] + parts[2:])
        for ext in (".pb", ".swatchbin"):
            dest = os.path.join(GAME, "mediapc", os.path.splitext(rel_media)[0] + ext)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copyfile(src, dest)
            if dest not in state["loose"]:
                state["loose"].append(dest)
            print("installed", os.path.relpath(dest, GAME))
    save_state(state)


def chunk_lookup():
    """basename -> (chunk number, entry index)"""
    table = {}
    for n in range(16):
        txt = os.path.join(TRACK, f"ChunkContentsMiniZip{n}.txt")
        if os.path.exists(txt):
            for i, path in fh6minizip.load_names(txt).items():
                table[os.path.basename(path)] = (n, i)
    return table


def install_patch(brand):
    state = load_state()
    lookup = chunk_lookup()
    os.makedirs(BACKUP, exist_ok=True)
    for src, rel in built_files(brand):
        name = os.path.basename(rel)
        chunk, idx = lookup[name]
        path = os.path.join(TRACK, f"GeoChunk{chunk}.minizip")
        mz = fh6minizip.MiniZip(path)
        off, size, flags, _, stored = mz.entries[idx]
        new = open(src, "rb").read()
        if len(new) != size:
            sys.exit(f"{name}: size {len(new)} != original {size}")
        codec = flags & 0xFF
        mz.f.seek(off)
        original = mz.f.read(stored)
        mz.f.close()
        if codec == 0:
            payload = new
        elif codec == 0x1F:
            # Match the original block's exact length so the slot keeps its original
            # (tiny) padding; a decoder given the whole slot then still decodes cleanly.
            target = stored - lz4_padding(original, size)
            payload = lz4_exact(new, target, exact_only=True)  # the game rejects any other length
        elif codec == 0x08:
            co = zlib.compressobj(9, zlib.DEFLATED, -15)
            payload = co.compress(new) + co.flush()
        else:
            sys.exit(f"{name}: unsupported codec {flags:#x}")
        if len(payload) > stored:
            sys.exit(f"{name}: new data {len(payload)} bytes does not fit slot {stored}")
        backup = os.path.join(BACKUP, f"GeoChunk{chunk}_{idx}_{off:x}.bin")
        if not os.path.exists(backup):
            open(backup, "wb").write(original)
        with open(path, "r+b") as f:
            f.seek(off)
            # Keep the original slot's trailing bytes after our data (padding stays as shipped).
            tail = original[len(payload):] if codec == 0x1F else b"\0" * (stored - len(payload))
            f.write(payload + tail)
        # Verify the game would read back exactly our texture; restore on any failure.
        try:
            ok = fh6minizip.MiniZip(path).read(idx) == new
        except Exception:
            ok = False
        if not ok:
            with open(path, "r+b") as f:
                f.seek(off)
                f.write(original)
            save_state(state)
            sys.exit(f"{name}: verification failed, restored original bytes")
        state["patch"].append({"archive": path, "offset": off, "backup": backup, "name": name})
        save_state(state)
        print(f"patched GeoChunk{chunk}[{idx}] {name} ({len(payload)}/{stored} bytes)")


_LOOKUP = None
_MZ = {}


def fits_slot(name, data):
    """Would `data` pack into the archive slot of the entry called `name`?"""
    global _LOOKUP
    if _LOOKUP is None:
        _LOOKUP = chunk_lookup()
    c, i = _LOOKUP[name]
    if c not in _MZ:
        _MZ[c] = fh6minizip.MiniZip(os.path.join(TRACK, f"GeoChunk{c}.minizip"))
    mz = _MZ[c]
    off, size, flags, _, stored = mz.entries[i]
    codec = flags & 0xFF
    if codec == 0:
        return len(data) == size
    bk = os.path.join(BACKUP, f"GeoChunk{c}_{i}_{off:x}.bin")
    slot = open(bk, "rb").read() if os.path.exists(bk) else (mz.f.seek(off), mz.f.read(stored))[1]
    if codec == 0x08:
        co = zlib.compressobj(9, zlib.DEFLATED, -15)
        return len(co.compress(data) + co.flush()) <= stored
    try:
        lz4_exact(data, stored - lz4_padding(slot, size), exact_only=True)
        return True
    except ValueError:
        return False


def original_entry(chunk, idx):
    """Decompressed original contents of an archive entry, from the backup if it was patched."""
    if chunk not in _MZ:
        _MZ[chunk] = fh6minizip.MiniZip(os.path.join(TRACK, f"GeoChunk{chunk}.minizip"))
    mz = _MZ[chunk]
    off, size, flags, _, stored = mz.entries[idx]
    backup = os.path.join(BACKUP, f"GeoChunk{chunk}_{idx}_{off:x}.bin")
    if not os.path.exists(backup):
        return mz.read(idx)
    raw = open(backup, "rb").read()
    codec = flags & 0xFF
    if codec == 0:
        return raw[:size]
    if codec == 0x08:
        return zlib.decompressobj(-15).decompress(raw)[:size]
    return lz4.block.decompress(raw[: len(raw) - lz4_padding(raw, size)], uncompressed_size=size)


def lz4_padding(block, size):
    """How many trailing bytes of a stored LZ4 slot are padding after the real block."""
    for trim in range(0, 64):
        try:
            lz4.block.decompress(block[: len(block) - trim], uncompressed_size=size)
            return trim
        except lz4.block.LZ4BlockError:
            continue
    raise ValueError("could not find the end of the original LZ4 block")


def _extend_last_literals(block, extra):
    """Append raw bytes to the final (literal-only) sequence of an LZ4 block."""
    p, last = 0, 0
    while True:
        last = p
        token = block[p]
        p += 1
        lit = token >> 4
        if lit == 15:
            while True:
                b = block[p]
                p += 1
                lit += b
                if b != 255:
                    break
        lit_start = p
        p += lit
        if p >= len(block):
            break
        p += 2  # match offset
        if token & 15 == 15:
            while block[p] == 255:
                p += 1
            p += 1
    total = lit + len(extra)
    head = bytes([min(total, 15) << 4])
    if total >= 15:
        rem = total - 15
        head += b"\xff" * (rem // 255) + bytes([rem % 255])
    return block[:last] + head + block[lit_start:lit_start + lit] + extra


def _lz4_parse(block):
    """LZ4 block -> list of [literal_len, match_offset, match_len] (last has match_len 0)."""
    seqs, p = [], 0
    while p < len(block):
        token = block[p]
        p += 1
        lit = token >> 4
        if lit == 15:
            while True:
                b = block[p]
                p += 1
                lit += b
                if b != 255:
                    break
        p += lit
        if p >= len(block):
            seqs.append([lit, 0, 0])
            break
        off = block[p] | block[p + 1] << 8
        p += 2
        ml = token & 15
        if ml == 15:
            while True:
                b = block[p]
                p += 1
                ml += b
                if b != 255:
                    break
        seqs.append([lit, off, ml + 4])
    return seqs


def _lz4_build(seqs, data):
    """Serialize sequences (literal bytes taken from data)."""
    out, pos = bytearray(), 0
    for lit, off, ml in seqs:
        mcode = 0 if ml == 0 else ml - 4
        out.append((min(lit, 15) << 4) | min(mcode, 15))
        if lit >= 15:
            r = lit - 15
            out += bytes([255]) * (r // 255) + bytes([r % 255])
        out += data[pos:pos + lit]
        pos += lit
        if ml:
            out += bytes([off & 255, off >> 8])
            if mcode >= 15:
                r = mcode - 15
                out += bytes([255]) * (r // 255) + bytes([r % 255])
            pos += ml
    return bytes(out)


def _seq_size(lit, ml):
    n = 1 + lit
    if lit >= 15:
        n += (lit - 15) // 255 + 1
    if ml:
        n += 2
        if ml - 4 >= 15:
            n += (ml - 4 - 15) // 255 + 1
    return n


def _lz4_inflate(block, data, target):
    """Grow a valid LZ4 block to exactly `target` bytes by writing short matches out as
    literals (each conversion adds a few bytes and decodes to the same output)."""
    seqs = _lz4_parse(block)
    size = len(block)
    while size < target:
        need = target - size
        best = None
        for i in range(len(seqs) - 1):  # never fold away the final literal-only sequence
            l0, _, m0 = seqs[i]
            l1, o1, m1 = seqs[i + 1]
            delta = _seq_size(l0 + m0 + l1, m1) - _seq_size(l0, m0) - _seq_size(l1, m1)
            if 0 < delta <= need and (best is None or delta > best[0]):
                best = (delta, i)
                if delta == need:
                    break
        if best is None:
            return None
        d, i = best
        seqs[i:i + 2] = [[seqs[i][0] + seqs[i][2] + seqs[i + 1][0], seqs[i + 1][1], seqs[i + 1][2]]]
        size += d
    out = _lz4_build(seqs, data)
    return out if len(out) == target else None


def lz4_exact(data, target, exact_only=False):
    """LZ4 block of exactly `target` bytes that decodes to data: compress, then grow it to
    the exact size by writing short matches out as literals. Several compression levels are
    tried because each yields a different mix of matches to work with."""
    cands = []
    for level in (12, 11, 10, 9, 8, 6, 4, 3):
        cands.append(lz4.block.compress(data, store_size=False, mode="high_compression", compression=level))
    cands.append(lz4.block.compress(data, store_size=False))
    cands = sorted({c for c in cands if len(c) <= target}, key=len, reverse=True)
    if not cands:
        raise ValueError(f"compressed size exceeds slot {target}")
    for blk in cands:
        if _lz4_build(_lz4_parse(blk), data) != blk:
            continue
        out = blk if len(blk) == target else _lz4_inflate(blk, data, target)
        if out is not None and lz4.block.decompress(out, uncompressed_size=len(data)) == data:
            return out
    if exact_only:
        raise ValueError(f"could not fit {len(data)} bytes into exactly {target}")
    return cands[0]


def prune(brand):
    """Restore original bytes for patched entries that are no longer in build/<brand>
    (e.g. a sign the user switched back to "keep original")."""
    built = {os.path.basename(f) for f, _ in built_files(brand)}
    state = load_state()
    keep, restored, done = [], 0, set()
    for p in reversed(state["patch"]):
        key = (p["archive"], p["offset"])
        if p["name"] in built:
            keep.append(p)
            continue
        if key not in done:
            done.add(key)
            data = open(p["backup"], "rb").read()
            with open(p["archive"], "r+b") as f:
                f.seek(p["offset"])
                f.write(data)
            print("restored original:", p["name"])
            restored += 1
    state["patch"] = list(reversed(keep))
    save_state(state)
    print(f"pruned {restored} entries no longer in build/{brand}")


def uninstall():
    state = load_state()
    for dest in state["loose"]:
        if os.path.exists(dest):
            os.remove(dest)
            print("removed", os.path.relpath(dest, GAME))
    done = set()
    for p in reversed(state["patch"]):
        key = (p["archive"], p["offset"])
        if key in done:
            continue
        done.add(key)
        data = open(p["backup"], "rb").read()
        with open(p["archive"], "r+b") as f:
            f.seek(p["offset"])
            f.write(data)
        print("restored", p["name"])
    # Remove now-empty folders under mediapc.
    mediapc = os.path.join(GAME, "mediapc")
    for d, _, _ in sorted(os.walk(mediapc), key=lambda t: -len(t[0])):
        if os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)
    save_state({"loose": [], "patch": []})


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "loose":
        install_loose(sys.argv[2])
    elif cmd == "patch":
        install_patch(sys.argv[2])
        prune(sys.argv[2])
    elif cmd == "prune":
        prune(sys.argv[2])
    elif cmd == "uninstall":
        uninstall()
    else:
        sys.exit(__doc__)
