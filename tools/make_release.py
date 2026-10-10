"""Package build/final as a player release (no dev labels, no catalogue).

  python tools/make_release.py 0.1.0

Writes dist/FH6JapaneseSigns-<version>/ and dist/FH6JapaneseSigns-<version>.zip:
  FH6JapaneseSigns/
    FH6JapaneseSigns.exe        patcher (built from patcher/fh6_signs.py with PyInstaller)
    Enable mod.bat / Disable mod.bat / Status.bat
    mod/manifest.json           per texture: name, vanilla SHA-256, mod SHA-256, size
    mod/files/<texture>         modded textures
    README.txt, LICENSE.txt
"""
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import install

ROOT = install.ROOT
DIST = os.path.join(ROOT, "dist")
APPDIR = "FH6JapaneseSigns"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def build_exe():
    exe = os.path.join(ROOT, "patcher", "dist", "FH6JapaneseSigns.exe")
    src = os.path.join(ROOT, "patcher", "fh6_signs.py")
    if not os.path.exists(exe) or os.path.getmtime(exe) < os.path.getmtime(src):
        subprocess.run([sys.executable, "-m", "PyInstaller", "--onefile", "--console", "--clean", "--noconfirm",
                        "--name", "FH6JapaneseSigns", "--distpath", os.path.join(ROOT, "patcher", "dist"),
                        "--workpath", os.path.join(ROOT, "patcher", "build"),
                        "--specpath", os.path.join(ROOT, "patcher", "build"), src], check=True)
    return exe


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "0.0.0-dev"
    out = os.path.join(DIST, f"{APPDIR}-{version}")
    app = os.path.join(out, APPDIR)
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(app, "mod", "files"))
    lookup = install.chunk_lookup()
    entries = []
    for src, rel in sorted(install.built_files("final")):
        name = os.path.basename(src)
        data = open(src, "rb").read()
        vanilla = install.original_entry(*lookup[name])
        if data == vanilla:
            continue
        if not name.endswith(".modelbin") and not install.fits_slot(name, data):
            sys.exit(f"{name}: does not fit its archive slot - fix the build first")
        shutil.copy(src, os.path.join(app, "mod", "files", name))
        entries.append({"name": name, "file": name, "path": rel, "size": len(data),
                        "vanilla_sha256": sha(vanilla), "mod_sha256": sha(data)})
    manifest = {"mod": "FH6 Japanese Signs", "version": version,
                "built": datetime.date.today().isoformat(), "archive_format": "PGZP v101",
                "entries": entries}
    json.dump(manifest, open(os.path.join(app, "mod", "manifest.json"), "w", encoding="utf-8"), indent=1)
    shutil.copy(build_exe(), app)
    for bat, cmd in (("Enable mod.bat", "enable"), ("Disable mod.bat", "disable"), ("Status.bat", "status")):
        open(os.path.join(app, bat), "w").write(f'@echo off\r\ncd /d "%~dp0"\r\nFH6JapaneseSigns.exe {cmd}\r\n')
    shutil.copy(os.path.join(ROOT, "docs", "README_player.txt"), os.path.join(app, "README.txt"))
    shutil.copy(os.path.join(ROOT, "LICENSE"), os.path.join(app, "LICENSE.txt"))
    zpath = shutil.make_archive(out, "zip", out)
    print(f"{len(entries)} textures -> {zpath} ({os.path.getsize(zpath) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
