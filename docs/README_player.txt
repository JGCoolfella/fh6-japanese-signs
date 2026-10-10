FH6 JAPANESE SIGNS  -  immersion / asset swap pack (WORK IN PROGRESS)
=====================================================================

Replaces the game's fictional shop signs with real Japanese brands.
This first release covers mainly convenience stores:

  365 Konbini        -> LAWSON  (incl. the standalone stores, e.g. near Mt Fuji)
  Kadomart           -> FamilyMart
  CHROMA             -> UNIQLO
  GAME / Level Up    -> Taito Station

Single-player / offline immersion mod. Not affiliated with any of these brands,
Microsoft or Playground Games.


INSTALL
-------
1. Close Forza Horizon 6.
2. Extract the "FH6JapaneseSigns" folder into your game folder
   (the folder that contains forzahorizon6.exe).
3. Double-click  "Enable mod.bat".

Takes a minute or two. Nothing is changed unless every texture checks out.


SWITCH BACK TO VANILLA / UNINSTALL
----------------------------------
Close the game, double-click "Disable mod.bat". The original bytes are restored
exactly from the backup/ folder. Then you can delete the FH6JapaneseSigns folder.
"Status.bat" shows whether the mod is currently enabled.

Keep the FH6JapaneseSigns folder (its backup/ subfolder) while the mod is enabled.
If it is ever lost, Steam > Forza Horizon 6 > Properties > Installed Files >
"Verify integrity of game files" restores the vanilla game.


HOW IT WORKS / SAFETY
---------------------
FH6 stores its world textures inside large archive files and ignores loose
override files, so the mod patches those archives in place - carefully:

 - every texture is found by name and only patched if it is exactly the vanilla
   version the mod was made for (checked with SHA-256);
 - the original bytes are backed up before anything is written;
 - new data is written at exactly the original size, then read back and checked;
 - if anything fails, the whole run is rolled back automatically.


GAME UPDATES
------------
Disable the mod before updating the game if you can. After an update the patcher
checks every texture first: if the update changed any of them it patches nothing
and asks for a newer version of the mod (it never half-applies). If an update
already replaced the archives, the mod is simply gone - re-enable it.


ONLINE PLAY
-----------
Made for single-player/offline use. Modifying game files may be against the
game's terms for online play - disable the mod before playing online. Use at
your own risk.


Source, issues, how to build: https://github.com/JGCoolfella/fh6-japanese-signs
