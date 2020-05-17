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
  playable in MAME:
  * NAM-1975
  * Magician Lord
  * King of the Monsters
  * Spinmaster
  * Neo Turf Master
  * Metal Slug
  * Real Bout Fatal Fury Special
  * Magical Drop 3
  * Shock Troopers
  * Metal Slug 2
  * The Last Blade 2
  * Shock Troopers 2
  * Metal Slug X
  * Support for many other Neo Geo games can be added easily. Encrypted games
  can be extracted, although extra steps are required, see [neogeo_reame.txt](neogeo_readme.txt)
* Can recreate a playable replica of the original ROM for SNES games where the 
  original sound data has been removed from the ROM, by re-encoding the PCM 
  sound data to BRR and restoring the BRR data to its original place in the ROM.
* Can extract most, but not all, of Space Harrier (Arcade).
* Automatically extracts the built-in manuals in VC games.
* Automatically extracts saves for all formats, except PC Engine / TurboGrafx16
  / TurboGrafx CD.
* Displays useful debugging information in the extraction process.
* Cross-platform - compatible with Linux, Windows, Mac OS X, and any other 
  platform supported by Python.

Requirements
------------
* [Python](http://python.org) 2.6 or 2.7 (or higher, but not Python 3.x)
* A NAND dump dumped by [BootMii](http://bootmii.org) and extracted by 
  [ShowMiiWads](http://code.google.com/p/showmiiwads) or [nandextract](http://github.com/Plombo/showmiiwads)

Usage
-----
The program is run by executing wiimetadata.py:  

    python wiimetadata.py nand_directory

Known Issues
------------
* NEO GEO: Because of the way Neo Geo games are made, part of the extraction
  process has to be hardcoded separately for each game. If your game is not
  supported, it might be trivial to expand neogeo_convert.py to include support
  for your game.
* NEO GEO: Many Neo Geo games are encrypted. These can be decrypted, but requires
  a lot of extra manual steps. See [neogeo_reame.txt](neogeo_readme.txt)
* NEO GEO: A few Neo geo games are compressed using LZMA. At this time, these
  cannot be decompressed.
* NEO GEO:
  NG games play differently depending on if they are ran on an MVS (arcade machine) or an AES (home console.)
  They also change content depending on the region of the hardware.
  This is all determined by the emulator (e.g. MAME) and the system ROM.
  The Wii NG games comes bundled with the main system ROM. Some games comes with an AES system ROM, other comes with an MVS system ROM.
  All games comes with a japanese system ROM.
  The ROM is patched to make the game think it's an american or european system, and the MVS ROM is patched so that the game thinks it is an AES system.

  * If you want the game to run in English and have the same experience as on a US/EU Wii, use "XXX-patched-to-us-XXX" or "XXX-patched-to-eu-XXX".
  * If you want the game to give an arcade experience ("insert coin" etc) use "jp-mvs" or "XXX-patched-to-XX-mvs" ROMs.
  * If you want the game to give a home console experience (insert coin etc) use "jp-aes" or "XXX-patched-to-XX-aes" ROMs.
  * If you want to be able to set DIP switches, or to be able to access the sytem menu, use "jp-mvs" or "jp-mvs-patched-to-XX-mvs" ROMs.
  * If you want to have an experience as accurate as possible, use the "jp-mvs" or "jp-aes".
  * As of now, there are audio issues, and the system menu is completley black (because SFIX is empty), if using an "XX-mvs", "XX-mvs-patched-to-XXX" or "XXX-patched-to-XX-mvs".
  * The system ROMs are not bound to a game, so you can use system ROMs exported from one game to any other NG game.

* A lot of games have simply been modified for VC.
  * For some games, the changes are minimal, for example the removal of flashing
    graphics. Known examples:
    * In Magical Drop 3, Tower character's flashing animation has been removed.
  * FDS games have been customized to let the emulator automatically switch disk
    side, which regular emulators does not support. You might get strange
    behaviour when it's time to switch disk. Just switching disk let's you bypass
    it in these known examples:
    * Bio Miracle Bokutte Upa: Flashing "wait" screen
    * Zelda no Densetsu: "Press start" is shown, nothing happens if you do
  * Some games are completely broken when played in regular emulators, known
    cases:
    * Mario Tennis (N64) - 8 bytes are different in the middle of the file,
      (as well as the CRC checksum in the header) making it crash on boot.
    * Shadow of the Ninja (NES) - 2 bytes are different, causing the intro to
      glitch and freeze.
* TURBOGRAFX CD: CD audio will play too slow in Mednafen. Reencodeing the OGG
  files makes them run correctly.
* TURBOGRAFX CD: Super Air Zonk does not play.
* TURBOGRAFX 16/CD: Save games are not extracted at this time.
* COMMODORE 64 and ARCADE: games cannot be extracted at this time.

Credits
-------
* [Bryan Cain](https://github.com/Plombo) - author of vcromclaim
* [JanErikGunnar](https://github.com/JanErikGunnar) - fixed a number of bugs and
  added compatibility with Famicom FDS, TurboGrafx CD, and some Neo Geo games.
* [hcs](http://hcs64.com) - author of C decompression code for Huf8, LZH8, and 
  romchu, all of which I (Bryan) ported to Python for vcromextract.
* [Hector Martin (marcan)](http://marcansoft.com/blog) - original author of the 
  Python LZ77 decompression code, which I heavily modified and expanded for 
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


