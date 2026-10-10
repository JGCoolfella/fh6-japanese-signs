# FH6 Japanese Signs

Replaces fictional signs in **Forza Horizon 6** with real Japanese brands — a work-in-progress
immersion / asset-swap pack. The first release covers mainly convenience stores:

| In game | Becomes |
|---|---|
| 365 Konbini (incl. the standalone stores, e.g. near Mt Fuji) | Lawson |
| Kadomart | FamilyMart |
| CHROMA | UNIQLO |
| GAME / Level Up Station | Taito Station |

**Players:** download the release from Nexus Mods (or GitHub Releases) and read its `README.txt` —
drop the folder in the game folder, click *Enable mod*, click *Disable mod* to go back to vanilla.

This repository contains **source only** — the build tools, the sign job definitions and the patcher.
No game files are included; you build the textures from your own copy of the game.

## How it works

FH6 keeps world textures in large `media/Tracks/Brio/GeoChunk*.minizip` archives (format PGZP v101)
and does not load loose override files for them, so the mod patches entries in place. The player
patcher is a plain PowerShell script (`patcher/FH6JapaneseSigns.ps1`, run by the `.bat` files — no
executables). Compression is done at release time, so the script only checks and swaps bytes:

* entries are located **by name** (`ChunkContentsMiniZip*.txt`), never by offset;
* a slot is only patched if its bytes hash (SHA-256) to the **exact vanilla slot** the mod was built
  for (`mod/manifest.json`); if a game update changed anything, nothing is patched;
* original slot bytes are backed up before writing; replacements are pre-built at **exactly the
  original slot length** (the game refuses to start otherwise);
* every write is read back and verified; any failure rolls the whole run back;
* *Disable* restores the backups byte for byte, only where the mod's data is still present.

## Repository layout

| Path | What |
|---|---|
| `patcher/FH6JapaneseSigns.ps1` | player patcher (enable / disable / status), shipped with `.bat` launchers |
| `patcher/fh6_signs.py` | alternative Python patcher (name lookup + on-the-fly re-encoding, `--partial`); dev use |
| `tools/` | extraction, texture decoding/encoding, sign builders, release packaging |
| `tools/jobs_*.py` | what gets replaced where (plain textures, tinted sign masks, user choices) |
| `catalogue/choices/` | per-sign decisions + custom artwork from the sign catalogue; `enabled_brands.json` switches brands on/off |
| `assets/` | logo artwork (see [ASSETS.md](ASSETS.md)) |
| `docs/` | [developer workflow](docs/DEVELOPING.md), player readme |

## Building

See [docs/DEVELOPING.md](docs/DEVELOPING.md).

## Legal

Code: MIT (see `LICENSE`). Brand names and logos are trademarks of their owners and are used for a
non-commercial fan modification; this project is not affiliated with them, Microsoft or Playground
Games. Intended for single-player / offline play.
