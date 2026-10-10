"""Package build/final as a player release (no dev labels, no catalogue, no executables).

  python tools/make_release.py 0.1.0        (the game must be vanilla: disable the mod first)

The compression is done here, so the player-side patcher (patcher/FH6JapaneseSigns.ps1, plain
PowerShell) only has to check and swap bytes. For every texture this stores the complete replacement
slot - exactly as long as the vanilla slot - plus SHA-256s of the vanilla and modded slot bytes.

Writes dist/FH6JapaneseSigns-<version>/ and dist/FH6JapaneseSigns-<version>.zip:
  FH6JapaneseSigns/
    FH6JapaneseSigns.ps1, Enable mod.bat, Disable mod.bat, Status.bat
    mod/manifest.json, mod/files/<texture>.bin
    README.txt, LICENSE.txt
"""
import datetime
import hashlib
import json
import os
import shutil
import struct
import sys
import zlib

import lz4.block

sys.path.insert(0, os.path.dirname(__file__))
import fh6minizip
import install

ROOT = install.ROOT
DIST = os.path.join(ROOT, "dist")
APPDIR = "FH6JapaneseSigns"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def ps_offset(path, idx):
    """Same slot-offset arithmetic as Get-EntryOffset in the PowerShell patcher (self-check)."""
    with open(path, "rb") as f:
        _, ver, _, count, index_count, block_size = struct.unpack("<4sIIIII", f.read(24))
        p = 0x20 + 4 * index_count + 4
        p += (8 - p % 8) % 8
        bb = 8 + 12 * block_size
        b, k = divmod(idx, block_size)
        f.seek(p + b * bb)
        (base,) = struct.unpack("<Q", f.read(8))
        f.seek(p + b * bb + 8 + 12 * k)
        (off,) = struct.unpack("<I", f.read(4))
    return base + off


def decode(raw, size, codec):
    if codec == 0x08:
        return zlib.decompressobj(-15).decompress(raw)[:size]
    if codec:
        return lz4.block.decompress(raw[:len(raw) - install.lz4_padding(raw, size)], uncompressed_size=size)
    return raw[:size]


def slot_payload(data, raw, size, codec):
    """A full replacement slot (same length as raw) that decodes to data."""
    if codec == 0x1F:
        body = install.lz4_exact(data, len(raw) - install.lz4_padding(raw, size), exact_only=True)
        out = body + raw[len(body):]
    elif codec == 0x08:
        co = zlib.compressobj(9, zlib.DEFLATED, -15)
        body = co.compress(data) + co.flush()
        if len(body) > len(raw):
            raise ValueError("deflate data larger than slot")
        out = body + b"\0" * (len(raw) - len(body))
    else:
        out = data + raw[len(data):]
    if len(out) != len(raw) or decode(out, size, codec) != data:
        raise ValueError("payload check failed")
    return out


def game_version():
    """FileVersion of forzahorizon6.exe (e.g. 6.440.853.0), read from its version resource."""
    exe = os.path.join(install.GAME, "forzahorizon6.exe")
    try:
        import subprocess
        return subprocess.run(["powershell", "-NoProfile", "-Command", f"(Get-Item '{exe}').VersionInfo.FileVersion"],
                              capture_output=True, text=True).stdout.strip() or None
    except Exception:
        return None


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "0.0.0-dev"
    out = os.path.join(DIST, f"{APPDIR}-{version}")
    app = os.path.join(out, APPDIR)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(app, "mod", "files"))
    lookup = install.chunk_lookup()
    mzs, entries = {}, []
    for src, rel in sorted(install.built_files("final")):
        name = os.path.basename(src)
        data = open(src, "rb").read()
        c, i = lookup[name]
        vanilla = install.original_entry(c, i)
        if data == vanilla:
            continue
        if c not in mzs:
            mzs[c] = fh6minizip.MiniZip(os.path.join(install.TRACK, f"GeoChunk{c}.minizip"))
        mz = mzs[c]
        off, size, flags, _, stored = mz.entries[i]
        if ps_offset(mz.path, i) != off:
            sys.exit(f"{name}: slot offset self-check failed")
        mz.f.seek(off)
        raw = mz.f.read(stored)
        if decode(raw, size, flags & 0xFF) != vanilla:
            sys.exit(f"{name}: the game is not vanilla here - disable the mod / run install.py uninstall first")
        payload = slot_payload(data, raw, size, flags & 0xFF)
        fname = name + ".bin"
        open(os.path.join(app, "mod", "files", fname), "wb").write(payload)
        entries.append({"name": name, "file": fname, "chunk": c, "slot_length": len(raw),
                        "vanilla_slot_sha256": sha(raw), "mod_slot_sha256": sha(payload),
                        "vanilla_sha256": sha(vanilla), "mod_sha256": sha(data), "path": rel})
    manifest = {"mod": "FH6 Japanese Signs", "version": version, "built": datetime.date.today().isoformat(),
                "game_version": game_version(),
                "archive_format": "PGZP v101", "entries": entries}
    json.dump(manifest, open(os.path.join(app, "mod", "manifest.json"), "w", encoding="utf-8"), indent=1)
    shutil.copy(os.path.join(ROOT, "patcher", "FH6JapaneseSigns.ps1"), app)
    for bat, cmd in (("Enable mod.bat", "enable"), ("Disable mod.bat", "disable"), ("Status.bat", "status")):
        open(os.path.join(app, bat), "w", newline="\r\n").write(
            f'@echo off\npowershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0FH6JapaneseSigns.ps1" {cmd}\n')
    shutil.copy(os.path.join(ROOT, "docs", "README_player.txt"), os.path.join(app, "README.txt"))
    shutil.copy(os.path.join(ROOT, "LICENSE"), os.path.join(app, "LICENSE.txt"))
    zpath = shutil.make_archive(out, "zip", out)
    print(f"{len(entries)} textures -> {zpath} ({os.path.getsize(zpath) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
