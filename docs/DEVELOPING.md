# Developing

Everything runs on Windows with Python 3.10+.

```
pip install numpy pillow scipy lz4 texture2ddecoder opencv-python-headless pyinstaller
```

Download `texconv.exe` (Microsoft DirectXTex, MIT) from
<https://github.com/microsoft/DirectXTex/releases> into `tools/`.

Clone this repository **inside the game folder** (default: tools assume `<game>/<repo>/`), or set
`FH6_GAME` to the game folder.

## Pipeline

| Step | Command |
|---|---|
| Extract the textures/models used by the jobs | `python tools/fh6minizip.py ../media/Tracks/Brio "*<pattern>*" -o extract` (then `python tools/refresh_extract.py`) |
| Build every modded file into `build/final/` | `python tools/build_all.py` |
| Install on your own game (dev) | `python tools/install.py patch final` |
| Restore vanilla (dev) | `python tools/install.py uninstall` |
| Package a player release | `python tools/make_release.py <version>` → `dist/FH6JapaneseSigns-<version>.zip` |

`extract/` must always hold vanilla data; `install.py` keeps byte backups in `backup/` and a record
in `installed.json`. Builders read originals through `install.original_entry()` so rebuilding after
patching is safe.

### Hard rules (learnt the hard way)

* A patched LZ4 entry must have **exactly** the original compressed length, or the game crashes on
  startup (FHE01). `install.lz4_exact` / the patcher handle this; never write other lengths.
* Every texture version (quality1..5) must fit its slot. Builders fall back to smaller logos, then
  keep the previous/original version — never write a file that `install.fits_slot` rejects.
* Single-channel ink masks (BC4, format 3/4) decode with A=255; ignore G/B/A when previewing.

## Choosing what gets swapped

* `catalogue/choices/enabled_brands.json` — brands that are built. Everything else is skipped and the
  game's original shows (the jobs stay in the code; `disabled_swaps.json` records what was there).
* `catalogue/choices/choices.json` — per-sign decisions made in the sign catalogue
  (`Open sign catalogue.bat`, or `python tools/catalogue_server.py`): "keep original", custom images.
* Job definitions: `tools/jobs_plain.py` (plain textures), `tools/jobs_masks.py` (tinted signs),
  `tools/jobs_user.py` (per-sign choices, applied last).

## Dev tools (never shipped)

* **Sign catalogue** — `python tools/catalogue.py` builds `catalogue/index.html`, a numbered
  catalogue of every sign (permanent IDs in `catalogue/id_registry.json`).
* **In-game ID labels** — stamps each sign with its catalogue ID and a perfect circle (an oval in
  game = stretched):
  ```
  python tools/label_build.py && python tools/install.py patch labels   # labels ON
  python tools/install.py patch final                                    # labels OFF
  ```
  `make_release.py` only ever packages `build/final`, so labels cannot leak into a release.

## Releasing

1. `python tools/build_all.py`
2. `python tools/install.py patch final`, test in game.
3. `python tools/make_release.py 0.1.0` and test the zip on a vanilla game:
   `python tools/install.py uninstall`, extract the zip into the game folder,
   run `Enable mod.bat`, check in game, run `Disable mod.bat`.
4. Upload `dist/FH6JapaneseSigns-<version>.zip` to Nexus Mods / GitHub Releases.

## Dev install vs. player patcher

Use one at a time on the same game. The player patcher (`FH6JapaneseSigns/`) keeps its own backups
and `state.json`; the dev installer keeps `backup/` + `installed.json`. Before switching, disable
with the one that enabled it (`Disable mod.bat` or `python tools/install.py uninstall`).
