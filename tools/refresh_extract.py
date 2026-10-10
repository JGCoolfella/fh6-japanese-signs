"""Make sure extract/ holds the ORIGINAL game files for every entry that has been patched.

Re-extracting from the archive after patching would otherwise give the modded version, and
builders use extract/ as their source of originals.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import fh6minizip
import install

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    fixed = same = 0
    names = {}
    for b in sorted(os.listdir(install.BACKUP)):
        m = re.match(r"GeoChunk(\d+)_(\d+)_[0-9a-f]+\.bin$", b)
        if not m:
            continue
        c, i = int(m[1]), int(m[2])
        if c not in names:
            names[c] = fh6minizip.load_names(os.path.join(install.TRACK, f"ChunkContentsMiniZip{c}.txt"))
        rel = names[c][i]
        dest = os.path.join(ROOT, "extract", rel)
        orig = install.original_entry(c, i)
        if os.path.exists(dest) and open(dest, "rb").read() == orig:
            same += 1
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "wb").write(orig)
        fixed += 1
        print("restored original:", os.path.basename(rel))
    print(f"{fixed} restored, {same} already original")


if __name__ == "__main__":
    main()
