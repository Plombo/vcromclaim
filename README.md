vcromclaim
==========

Intro
-----
vcromclaim is a program to extract game ROMs from Wii Virtual Console games. 
It does this by analyzing an extracted Wii NAND filesystem, locating the ROMs, 
and extracting them.  It automatically detects and decompresses compressed ROMs.
It also extracts the game manual and save files for each Virtual Console game 
it encounters.

This is a fork of Bryan Cain's original version. This fork fixes a number of
bugs and adds compatibility with Famicom FDS, TurboGrafx CD, and some Neo Geo
games. 

Features
--------
* Extracts virtually all NES/Famicom/Disk System, SNES, PC Engine /
  TurboGrafx16 / TurboGrafx CD, Mega Drive/Genesis, Master System, and
  Nintendo 64 games without fail!
* Extracts several Neo Geo games, along with the AES/MVS BIOS, so that they are
  playable in MAME: Magician Lord, King of the Monsters, Spinmaster, Neo Turf
  Master, Metal Slug, Metal Slug 2, Magical Drop 3. Support for many other Neo
  Geo games can be added easily, as long as the game is not encrypted.
* Can recreate a playable replica of the original ROM for SNES games where the 
  original sound data has been removed from the ROM, by re-encoding the PCM 
  sound data to BRR and restoring the BRR data to its original place in the ROM.
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
* NEO GEO: Many Neo Geo games are encrypted. At this time, there is no way of
  decryptiny these games. (If you are desperate, you can emulate the WAD in
  Dolphin, and use Dolphin's debug mode to create a ram dump. The ram dumps
  should contain the decrypted roms.)
* NEO GEO: The BIOS used for Neo Geo games (MVS or AES depending on game) is
  included with the VC games and is extracted, but some of the support ROMs
  (sfix and m1) are missing because are not needed for normal game play.
  To make the games run in mame, dummy files are created, but some BIOS
  functionality (such as management menu) is broken.
* FDS: Many games spanning multiple disk sides will glitch in common emulators
  when you are supposed to switch side. For example, Bio Miracle Bokutte Upa
  will show a flashing WAIT message and Zelda no Densetsu will show "Press
  Start" (but nothing happens if you do). In both these games, just switching
  disk will resume the game. This is because the games have been customized for
  the Virtual Console emulator to automatically switch sides.
* ALL SYSTEMS: Some VC ROMs are modified from the original ROMs in ways that
  causes them to glitch or not run in common emulators. Known cases:
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
* ZOINKITY - author of N64.py, containing the cart CRC code


