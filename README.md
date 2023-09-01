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
* Extracts several Neo Geo games, including encrypted games, along with the AES/MVS
  BIOS, so that they are playable in MAME
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
  * Metal Slug 3
  * Metal Slug 4
  * ...and support for many other Neo Geo games can be added relatively easily.
    Lots of caveats though - see below!
* Can extract the arcade games Ghosts'N Goblins and Space Harrier.
* Automatically extracts the built-in manuals in VC games.
* Automatically extracts saves for most formats.
* Cross-platform - compatible with Linux, Windows, Mac OS X, and any other 
  platform supported by Python. Some games may require additional libraries to extract.
* If the game/platform you want to extract is missing - please submit a bug to let me
  know there is demand for it!

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
  in accurate emulators or on real hardware. Very often checksums will not be accurate.
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
    * Ogre Battle 64: "JIHAD" was renamed "LASER" for obvious reasons
* TURBOGRAFX CD: CD audio is extracted in the wrong speed, because the quality is
  higher than required (48 kHz instead of 44.1kHz). Music in all games will play too slow
  in Mednafen, and a few games (like Super Air Zonk) are completely broken.
  Manually reencodeing the OGG files to 44.1kHz WAVE with e.g. Audacity should fix all this.
* COMMODORE 64 games and most ARCADE games cannot be extracted at this time.
* NEO GEO: Because of the way Neo Geo ROMs are made, part of the extraction
  process has to be hardcoded separately for each game. If your game is not
  supported, it might be trivial to expand neogeo_convert.py to include support
  for your game - please create a bug and I can try to implement it.
* NEO GEO: For AES encrypted games, you will need to install PyCryptodome (or PyCrypto).
  Install it by typing in terminal:
  pip install pycryptodome
* NEO GEO: About the system ROMs...
  NEO GEO games always require a set of them. Either the MVS (arcade) or AES (home) ROMs,
  each available in many different versions, and regional variations (jap/us/eu).
  Depending on what ROM is used, the game will automatically display different language,
  and different content. The MVS ROM will enable system menu, some generic "how to play"
  screens, "winners don't do drugs", etc. The AES ROMs are lighter and does not provide any
  of that. Also games ran with MVS ROMs will typically show "insert coin", but not when ran with
  AES ROMs.

  The Wii games comes bundled with weird system ROMs. Some games randomly comes shippd with
  MVS ROMs, others with AES ROMs. All are shipped with the Japanese ROMs.
  The system ROMs contain a few flags that tell the game what region/system it is in.
  Annoyingly, instead of shipping the correct system ROMs, all of them are instead patched
  to tell the game it is e.g. US AES.

  Also the MVS ROM sets are incomplete. They are missing the SFIX ROM, which contains all of the
  graphics used in system menu and how-to-play screens. (To allow the games to run, this tool
  creates a dummy SFIX file, but system menu etc is basically unusable.)

  This tool will extract whatever ROM was included. It will export an original version that
  is as close to original as possible, AND it will also create a number of different patches
  to simulate different Wii behaviours. You may have to experiment and try different ROM
  versions, to get the experience you want. Some combinations of games+system ROM may not work,
  or have audio problems.

  * If you want to have an US/EU Wii-like experience, use "XXX-patched-to-aes-us" or "XXX-patched-to-aes-eu"
  * If you want ARCADE-like experience, use "jp-mvs" or "XXX-patched-to-mvs-XX"
  * If you want the game to give a HOME CONSOLE experience, use "aes-jp" or "XXX-patched-to-aes-XX"
  * If you want to have an experience as ACCURATE as possible, use the "mvs-jp" or "aes-jp"
  * If you want the game to be in ENGLISH, use "XXX-patched-to-XX-us" or "XXX-patched-to-XX-eu"
  * If you want the game to be in JAPANESE, use "mvs-jp", "aes-jp" or "XXX-patched-to-XX-jp"



Credits
-------
* [Bryan Cain](https://github.com/Plombo) - author of vcromclaim
* [JanErikGunnar](https://github.com/JanErikGunnar) - added extraction of Famicom FDS,
  TurboGrafx CD, Neo Geo and arcade games.
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

