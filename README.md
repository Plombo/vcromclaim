vcromclaim
==========

Intro
-----
vcromclaim is a program to extract game ROMs from Wii Virtual Console games. 
It does this by analyzing an extracted Wii NAND filesystem, locating the ROMs, 
and extracting them.  It automatically detects and decompresses compressed ROMs.
It also extracts the game manual and save files for each Virtual Console game 
it encounters.

Features
--------
* Extracts virtually all NES/Famicom/Disk System, SNES, PC Engine /
  TurboGrafx16 / TurboGrafx CD, Mega Drive/Genesis, Master System, and
  Nintendo 64 games without fail!
* Extracts several Neo Geo games, along with the AES/MVS BIOS, so that they are
  playable in MAME (note - extra steps may be required, see below)
  * NAM-1975
  * Magician Lord
  * King of the Monsters
  * Spinmaster
  * Neo Turf Masters
  * Metal Slug
  * Real Bout Fatal Fury Special
  * Magical Drop 3
  * Shock Troopers
  * Metal Slug 2
  * The King of Fighters '98
  * The Last Blade 2
  * Shock Troopers 2
  * Metal Slug X
  * ...and support for many other Neo Geo games can be added relatively easily.
    Lots of caveats though - see below!
* Can extract Space Harrier (Arcade).
* Automatically extracts the built-in manuals in VC games.
* Automatically extracts saves for most formats.
* Cross-platform - compatible with Linux, Windows, Mac OS X, and any other 
  platform supported by Python. Some games may require additional libraries to extract.

Requirements
------------
* [Python](http://python.org) 3.11.4 or newer. Older versions may work but
  are not tested or supported.
* A NAND dump dumped by [BootMii](http://bootmii.org) and extracted by 
  [ShowMiiWads](http://code.google.com/p/showmiiwads) or [nandextract](http://github.com/Plombo/showmiiwads)
* Additional requirements applies for some Neo Geo games, see [neogeo_reame.txt](neogeo_readme.txt)

Usage
-----
The program is run by executing wiimetadata.py:  

    python wiimetadata.py nand_directory

Known Issues/Caveats
--------------------
* ALL SYSTEMS: A lot of games have been modified for VC for various reasons. Same games may
  simply just behave differently from the original games, some games may not work properly
  in accurate emulators or on real hardware due. Very often checksums will not be accurate.
  Known instances:
  * Removal of flashing graphics:
    * In Magical Drop 3, Tower character's flashing animation has been removed.
  * FDS games have been customized to let the VC emulator automatically switch disk
    side. You might get strange behaviour when the game normally would ask you to change the
    disk. Depending on emulator, just changing disk may work as usual.
    * Bio Miracle Bokutte Upa: Flashing "wait" screen
    * Zelda no Densetsu: "Press start" is shown, nothing happens if you do
  * Shadow of the Ninja (NES) - 2 bytes are different, causing the intro to
      glitch and freeze in accurate emulators.
  * Content changes:
    * "Ogra Battle 64": "JIHAD" was renamed "LASER" for obvious reasons
* TURBOGRAFX CD: CD audio is extracted in the wrong speed, because the quality is
  higher than required (48 kZz in 44.1kHz). Music in all games will play too slow in Mednafen,
  and a few games (like Super Air Zonk) are completely broken.
  Manually reencodeing the OGG files to 44.1kHz WAVE with e.g. Audacity everything play correctly.
* COMMODORE 64 games and most ARCADE games cannot be extracted at this time.
* NEO GEO: Because of the way Neo Geo ROMs are made, part of the extraction
  process has to be hardcoded separately for each game. If your game is not
  supported, it might be trivial to expand neogeo_convert.py to include support
  for your game.
* NEO GEO: Many Neo Geo games are encrypted on VC. These can be decrypted, but requires
  a lot of advanced extra manual steps. See [neogeo_reame.txt](neogeo_readme.txt)
* NEO GEO: Games that had encryption on the original hardware, like Metal Slug 3 and
  Metal Slug 4, cannot currently be exported correctly. This is because MAME expects
  the original, encrypted ROMs while the VC ROMs come decrypted. (Not the same encryption
  as the previous point.) To solve we must apply encryption to the extracted ROMs.
* NEO GEO:
  NG games play differently depending on if they are ran on an MVS (arcade machine)
  or an AES (home console.) They also change content depending on the region of the
  hardware.
  This is all determined by the emulator (e.g. MAME) and the system ROM.
  The Wii NG games comes bundled with the main system ROM. Some games comes with an
  AES system ROM, other comes with an MVS system ROM.
  All games comes with a japanese system ROM.
  The ROM is patched to make the game think it's an american or european system,
  and the MVS ROM is patched so that the game thinks it is an AES system.

  * If you want the game to run in English and have the same experience as on a US/EU Wii, use "XXX-patched-to-us-XXX" or "XXX-patched-to-eu-XXX".
  * If you want the game to give an arcade experience ("insert coin" etc) use "jp-mvs" or "XXX-patched-to-XX-mvs" ROMs.
  * If you want the game to give a home console experience (insert coin etc) use "jp-aes" or "XXX-patched-to-XX-aes" ROMs.
  * If you want to be able to set DIP switches, or to be able to access the sytem menu, use "jp-mvs" or "jp-mvs-patched-to-XX-mvs" ROMs.
  * If you want to have an experience as accurate as possible, use the "jp-mvs" or "jp-aes".
  * As of now, there are audio issues, and the system menu is completely black (because SFIX is empty), if using an "XX-mvs", "XX-mvs-patched-to-XXX" or "XXX-patched-to-XX-mvs".
  * The system ROMs are not bound to a game, so you can use system ROMs exported from one game to any other NG game.

Credits
-------
* [Bryan Cain](https://github.com/Plombo) - author of vcromclaim
* [JanErikGunnar](https://github.com/JanErikGunnar) - added extraction of Famicom FDS,
  TurboGrafx CD, Neo Geo and Space Harrier.
* [Euan Forrester](https://github.com/euan-forrester) - TurboGrafx save file exporting
* [hcs](http://hcs64.com) - author of C decompression code for Huf8, LZH8, and 
  romchu, all of which I (Bryan) ported to Python for vcromextract.
* [Hector Martin (marcan)](http://marcansoft.com/blog) - original author of the 
  Python LZ77 decompression code, which I (Plombo) heavily modified and expanded for 
  vcromextract.
* [sepalani](https://github.com/sepalani/librso/blob/master/rvl/rso.py) - author of librso, 
  with some reverse engineering done for RSO file format
* [Bregalad](http://www.romhacking.net/community/1067) - author of BRRTools, 
  a Java program on which the BRR encoder in vcromclaim was based.
* qwikrazor87 - author of PCE CD Tools, of which the TG CD data decompression
  was based.
* [blastar](http://www.yaronet.com/topics/185388-ngfx-neogeoneogeocd-graphicseditor) - author of NGFX,
  a very good Neo Geo graphics editor that was useful in creating the open SFIX substitute.
* [ZOINKITY](https://pastebin.com/hcRjjTWg) - author of N64.py, containing the cart CRC code
* [The Neo Geo Development Wiki](https://wiki.neogeodev.org) - very useful for extracting Neo Geo roms
* [MAME](https://www.mamedev.org/) - the source code was very useful in extracting
  arcade and Neo Geo roms
* [HxD](https://mh-nexus.de/en/hxd/) - great, free hex editor
* [WiiBrew](https://wiibrew.org) - invaluable for any Wii development

