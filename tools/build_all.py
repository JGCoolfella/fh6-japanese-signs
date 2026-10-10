"""Rebuild every modded texture/model from the originals, in the right order, into build/final.

  python tools/build_all.py          # then: python tools/install.py patch final

Order matters because several textures carry more than one brand:
 1. Lawson standalone-building builder (fascia + glow + far LOD) -> build/lawson, copied to build/final
 2. plain-colour region jobs (jobs_plain.py), stacking on build/final
 3. tinted-sign variant jobs (jobs_masks.py), stacking on build/final
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PY = sys.executable


def step(*args):
    print(">>", " ".join(args), flush=True)
    subprocess.run([PY, os.path.join(HERE, args[0]), *args[1:]], check=True)


def main():
    step("refresh_extract.py")  # extract/ must hold originals
    for d in ("lawson", "final"):
        shutil.rmtree(os.path.join(ROOT, "build", d), ignore_errors=True)
    step("brand_konbini_bld.py", "lawson")
    shutil.copytree(os.path.join(ROOT, "build", "lawson"), os.path.join(ROOT, "build", "final"))
    step("rebrand_plain.py")
    step("rebrand_poi.py")
    step("rebrand_cells.py")
    step("rebrand_x9.py")
    step("hdr_fix.py")      # konbini baked light: 365 yellow -> neutral white
    n = sum(len(f) for _, _, f in os.walk(os.path.join(ROOT, "build", "final")))
    print(f"build/final ready: {n} files")


if __name__ == "__main__":
    main()
