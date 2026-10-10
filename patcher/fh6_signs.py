"""FH6 Japanese Signs - patcher (enable / disable / status).

Forza Horizon 6 keeps its world textures inside large GeoChunk*.minizip archives and does not load
loose override files, so the mod has to write into those archives. This patcher does that safely:

  * every texture is found by NAME (ChunkContentsMiniZip*.txt), never by a fixed offset;
  * it is only patched if it still matches, byte for byte, the vanilla texture the mod was built
    from (SHA-256 in mod/manifest.json). If the game was updated and anything changed, nothing is
    patched at all, so you can never end up with a half-applied or mismatched mod;
  * the original bytes of every slot are saved in backup/ before they are touched, and the new data
    is written at exactly the original compressed length (the game rejects anything else);
  * each write is read back and verified; on any failure the whole run is rolled back;
  * Disable restores the saved bytes exactly, and only where the mod's data is still in place.
Steam's "Verify integrity of game files" also restores vanilla at any time.

Usage:  FH6JapaneseSigns.exe [enable|disable|status] [--game "D:\\path\\to\\Forza Horizon 6"]
        (no arguments: interactive menu)
"""
import argparse
import bisect
import hashlib
import json
import os
import struct
import subprocess
import sys
import time
import zlib

import lz4.block

APP = "FH6 Japanese Signs"
GAME_EXE = "forzahorizon6.exe"
TRACK_REL = os.path.join("media", "Tracks", "Brio")


def here():
    return os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))


# ------------------------------------------------------------------ archive format (PGZP v101)

class MiniZip:
    """Read-only view of a .minizip archive's entry table."""

    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            magic, ver, _, count, index_count, block_size, blocks, _ = struct.unpack("<4sIIIIIII", f.read(0x20))
            if magic != b"PGZP":
                raise ValueError(f"{path}: not a PGZP archive")
            if ver != 101:
                raise ValueError(f"{path}: unsupported archive version {ver} (mod supports 101)")
            pos = 0x20 + index_count * 4
            f.seek(pos)
            table = f.read(16 + count * 12 + blocks * 16 + 16)
        p = 0
        (n,) = struct.unpack_from("<I", table, p)
        p += 4
        if n != count:
            raise ValueError(f"{path}: corrupt entry table")
        self.entries, bases = [], []
        for b in range(blocks):
            p += (-(pos + p)) % 8
            (base,) = struct.unpack_from("<Q", table, p)
            p += 8
            bases.append(base)
            for _ in range(min(block_size, count - b * block_size)):
                off, size, c = struct.unpack_from("<III", table, p)
                p += 12
                self.entries.append([base + off, size, c & 0xFFFF])
        p += (-(pos + p)) % 8
        (end,) = struct.unpack_from("<Q", table, p)
        bases.append(max(end, os.path.getsize(path)))
        starts = sorted({e[0] for e in self.entries} | set(bases))
        for e in self.entries:  # stored length = distance to the next distinct start
            e.append(starts[bisect.bisect_right(starts, e[0])] - e[0])

    def slot(self, i):
        off, size, flags, stored = self.entries[i]
        with open(self.path, "rb") as f:
            f.seek(off)
            return f.read(stored)

    def decode(self, i, raw):
        _, size, flags, _ = self.entries[i]
        codec = flags & 0xFF
        if codec == 0x08:
            return zlib.decompressobj(-15).decompress(raw)[:size]
        if codec:
            return lz4.block.decompress(raw[:len(raw) - lz4_padding(raw, size)], uncompressed_size=size)
        return raw[:size]


def load_names(txt):
    """Entry index -> file name (line i of ChunkContentsMiniZip<N>.txt is entry i)."""
    names, i = {}, 0
    with open(txt, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            names[i] = line.rsplit("|", 1)[0].replace("\\", "/").rsplit("/", 1)[-1]
            i += 1
    return names


# ------------------------------------------------------------------ exact-length LZ4

def lz4_padding(block, size):
    for trim in range(0, 64):
        try:
            lz4.block.decompress(block[:len(block) - trim], uncompressed_size=size)
            return trim
        except lz4.block.LZ4BlockError:
            continue
    raise ValueError("could not find the end of the LZ4 block")


def _parse(block):
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


def _build(seqs, data):
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
    n = 1 + lit + ((lit - 15) // 255 + 1 if lit >= 15 else 0)
    if ml:
        n += 2 + ((ml - 4 - 15) // 255 + 1 if ml - 4 >= 15 else 0)
    return n


def _inflate(block, data, target):
    seqs, size = _parse(block), len(block)
    while size < target:
        need, best = target - size, None
        for i in range(len(seqs) - 1):
            l0, _, m0 = seqs[i]
            l1, _, m1 = seqs[i + 1]
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
    out = _build(seqs, data)
    return out if len(out) == target else None


def lz4_exact(data, target):
    """An LZ4 block of exactly `target` bytes that decodes to `data`."""
    cands = [lz4.block.compress(data, store_size=False, mode="high_compression", compression=lv)
             for lv in (12, 11, 10, 9, 8, 6, 4, 3)] + [lz4.block.compress(data, store_size=False)]
    for blk in sorted({c for c in cands if len(c) <= target}, key=len, reverse=True):
        if _build(_parse(blk), data) != blk:
            continue
        out = blk if len(blk) == target else _inflate(blk, data, target)
        if out is not None and lz4.block.decompress(out, uncompressed_size=len(data)) == data:
            return out
    raise ValueError("does not fit the archive slot")


# ------------------------------------------------------------------ patcher

def sha(b):
    return hashlib.sha256(b).hexdigest()


class Patcher:
    def __init__(self, game, mod_dir):
        self.game, self.mod = game, mod_dir
        self.track = os.path.join(game, TRACK_REL)
        self.manifest = json.load(open(os.path.join(mod_dir, "mod", "manifest.json"), encoding="utf-8"))
        self.backup_dir = os.path.join(mod_dir, "backup")
        self.state_path = os.path.join(mod_dir, "state.json")
        self.state = json.load(open(self.state_path)) if os.path.exists(self.state_path) else {"applied": {}}
        self._archives, self._lookup = {}, None

    def save(self):
        tmp = self.state_path + ".tmp"
        json.dump(self.state, open(tmp, "w"), indent=1)
        os.replace(tmp, self.state_path)

    def lookup(self):
        if self._lookup is None:
            wanted = {e["name"] for e in self.manifest["entries"]}
            self._lookup = {}
            for c in range(64):
                txt = os.path.join(self.track, f"ChunkContentsMiniZip{c}.txt")
                if not os.path.exists(txt):
                    continue
                for i, n in load_names(txt).items():
                    if n in wanted:
                        self._lookup[n] = (c, i)
        return self._lookup

    def archive(self, c):
        if c not in self._archives:
            self._archives[c] = MiniZip(os.path.join(self.track, f"GeoChunk{c}.minizip"))
        return self._archives[c]

    def survey(self, progress=True):
        """name -> (status, chunk, index, slot bytes); status: vanilla | modded | changed | missing."""
        lk, out = self.lookup(), {}
        ents = self.manifest["entries"]
        for k, e in enumerate(ents, 1):
            if progress:
                print(f"\r  checking textures {k}/{len(ents)}", end="", flush=True)
            if e["name"] not in lk:
                out[e["name"]] = ("missing", None, None, None)
                continue
            c, i = lk[e["name"]]
            mz = self.archive(c)
            raw = mz.slot(i)
            try:
                h = sha(mz.decode(i, raw))
            except Exception:
                h = None
            st = "vanilla" if h == e["vanilla_sha256"] else "modded" if h == e["mod_sha256"] else "changed"
            out[e["name"]] = (st, c, i, raw)
        if progress:
            print()
        return out

    def _write(self, c, i, payload, expect_sha):
        mz = self.archive(c)
        off, size, flags, stored = mz.entries[i]
        if len(payload) > stored:
            raise ValueError("payload larger than slot")
        with open(mz.path, "r+b") as f:
            f.seek(off)
            f.write(payload)
            f.flush()
            os.fsync(f.fileno())
        if sha(mz.decode(i, mz.slot(i))) != expect_sha:
            raise ValueError("read-back verification failed")

    def enable(self, partial=False):
        sv = self.survey()
        counts = {s: sum(1 for v in sv.values() if v[0] == s) for s in ("vanilla", "modded", "changed", "missing")}
        print(f"  vanilla {counts['vanilla']}, already modded {counts['modded']}, changed by a game update "
              f"{counts['changed']}, not found {counts['missing']}")
        if (counts["changed"] or counts["missing"]) and not partial:
            print("\n  The game files don't match the version this mod was built for (a game update changed\n"
                  "  some textures). Nothing was patched. Please check for an updated version of the mod.\n"
                  "  (Advanced: 'enable --partial' patches only the unchanged textures.)")
            return False
        os.makedirs(self.backup_dir, exist_ok=True)
        done = []
        try:
            todo = [e for e in self.manifest["entries"] if sv[e["name"]][0] == "vanilla"]
            for k, e in enumerate(todo, 1):
                print(f"\r  patching {k}/{len(todo)}", end="", flush=True)
                _, c, i, raw = sv[e["name"]]
                bpath = os.path.join(self.backup_dir, f"{e['name']}.{e['vanilla_sha256'][:12]}.bin")
                if not os.path.exists(bpath):
                    open(bpath, "wb").write(raw)
                mz = self.archive(c)
                _, size, flags, stored = mz.entries[i]
                data = open(os.path.join(self.mod, "mod", "files", e["file"]), "rb").read()
                if sha(data) != e["mod_sha256"] or len(data) != size:
                    raise ValueError(f"mod file damaged: {e['file']}")
                codec = flags & 0xFF
                if codec == 0x1F:
                    payload = lz4_exact(data, len(raw) - lz4_padding(raw, size))
                elif codec == 0x08:
                    co = zlib.compressobj(9, zlib.DEFLATED, -15)
                    payload = co.compress(data) + co.flush()
                    payload += b"\0" * (stored - len(payload))
                else:
                    payload = data
                self._write(c, i, payload, e["mod_sha256"])
                done.append((e, c, i, raw))
                self.state["applied"][e["name"]] = {"backup": os.path.basename(bpath), "vanilla_sha256": e["vanilla_sha256"]}
                self.save()
            print()
        except Exception as ex:
            print(f"\n  ERROR: {ex}\n  Rolling back this run...")
            for e, c, i, raw in reversed(done):
                self._write(c, i, raw, e["vanilla_sha256"])
                self.state["applied"].pop(e["name"], None)
            self.save()
            print("  Rolled back - the game files are unchanged.")
            return False
        print(f"  Enabled: {len(done)} textures patched.")
        return True

    def disable(self):
        sv = self.survey()
        restored = missing_backup = 0
        mods = [e for e in self.manifest["entries"] if sv[e["name"]][0] == "modded"]
        for k, e in enumerate(mods, 1):
            print(f"\r  restoring {k}/{len(mods)}", end="", flush=True)
            _, c, i, raw = sv[e["name"]]
            bpath = os.path.join(self.backup_dir, f"{e['name']}.{e['vanilla_sha256'][:12]}.bin")
            if not os.path.exists(bpath):
                missing_backup += 1
                continue
            orig = open(bpath, "rb").read()
            if len(orig) != len(raw):
                missing_backup += 1
                continue
            self._write(c, i, orig, e["vanilla_sha256"])
            self.state["applied"].pop(e["name"], None)
            self.save()
            restored += 1
        if mods:
            print()
        for n, v in sv.items():  # drop records for textures that are no longer ours
            if v[0] != "modded":
                self.state["applied"].pop(n, None)
        self.save()
        print(f"  Disabled: {restored} textures restored to vanilla.")
        if missing_backup:
            print(f"  {missing_backup} modded textures have no backup here - use Steam's 'Verify integrity of game files'.")
        return not missing_backup

    def status(self):
        sv = self.survey()
        counts = {}
        for v in sv.values():
            counts[v[0]] = counts.get(v[0], 0) + 1
        total = len(sv)
        if counts.get("modded", 0) == total:
            state = "ENABLED"
        elif counts.get("vanilla", 0) == total:
            state = "DISABLED (vanilla)"
        elif counts.get("changed", 0) or counts.get("missing", 0):
            state = "GAME UPDATED - mod needs an update"
        else:
            state = "PARTIAL"
        print(f"  {APP} {self.manifest['version']}: {state}")
        print("  " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
        return state


def game_running():
    try:
        out = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {GAME_EXE}"], capture_output=True, text=True).stdout
        return GAME_EXE.lower() in out.lower()
    except Exception:
        return False


def find_game(arg):
    cands = [arg] if arg else []
    d = here()
    for _ in range(4):
        cands.append(d)
        d = os.path.dirname(d)
    cands.append(os.getcwd())
    for c in cands:
        if c and os.path.isdir(os.path.join(c, TRACK_REL)) and os.path.exists(os.path.join(c, TRACK_REL, "GeoChunk0.minizip")):
            return os.path.abspath(c)
    return None


def main():
    ap = argparse.ArgumentParser(description=APP)
    ap.add_argument("command", nargs="?", choices=["enable", "disable", "status"])
    ap.add_argument("--game", help="Forza Horizon 6 install folder")
    ap.add_argument("--partial", action="store_true", help="enable: patch only textures that still match")
    ap.add_argument("--no-pause", action="store_true")
    a = ap.parse_args()
    print(f"{APP}\n" + "-" * len(APP))
    game = find_game(a.game)
    ok = False
    if not game:
        print("Could not find Forza Horizon 6. Put this folder inside the game folder (next to\n"
              f"{GAME_EXE}) or run with --game \"<game folder>\".")
    elif game_running() and a.command != "status":
        print("Please close Forza Horizon 6 first.")
    else:
        print(f"Game: {game}")
        p = Patcher(game, here())
        cmd = a.command
        if not cmd:
            p.status()
            print("\n  [1] Enable mod   [2] Disable mod (vanilla)   [3] Exit")
            cmd = {"1": "enable", "2": "disable"}.get(input("  Choice: ").strip())
        t = time.time()
        if cmd == "enable":
            ok = p.enable(a.partial)
        elif cmd == "disable":
            ok = p.disable()
        elif cmd == "status":
            p.status()
            ok = True
        if cmd in ("enable", "disable"):
            print(f"  ({time.time() - t:.0f}s)")
    if not a.no_pause and sys.stdin.isatty():
        input("\nPress Enter to close.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
