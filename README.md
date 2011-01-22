vcromclaim
==========

Intro
-----
vcromclaim is a program to extract game ROMs from Wii Virtual Console games. 
It does this by analyzing an extracted Wii NAND filesystem, locating the ROMs, 
and extracting them.  It automatically detects and decompresses compressed ROMs.
It also extracts the game manual for each Virtual Console game it encounters.

Features
--------
* Extracts virtually all NES, SNES, TurboGrafx16 (PC-Engine), Genesis, Master 
  System, and Nintendo 64 games without fail!
* Supports all known forms of decompression used in Virtual Console games.
* Can recreate a playable replica of the original ROM for SNES games where the 
  original sound data has been removed from the ROM, by re-encoding the PCM 
  sound data to BRR and restoring the BRR data to its original place in the ROM.
* Displays useful information in the extraction process.
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

    python wiimetadata.py nand

Known Issues
------------
* Extraction of Super Mario Bros.: The Lost Levels for NES (US version at least) results in an unplayable file less than 1 KB in size.
* Neo Geo, Commodore 64, and VC Arcade games cannot be extracted at this time.

Credits
-------
* [Bryan Cain](https://github.com/Plombo) - author of vcromclaim
* [hcs](http://hcs64.com) - author of C decompression code for Huf8, LZH8, and 
  romchu; ported to Python by Bryan Cain
* [Hector Martin (marcan)](http://marcansoft.com/blog) - original author of the 
  Python LZ77 decompression code, which was heavily modified and expanded for 
  vcromextract by Bryan Cain.
* [Bregalad](http://www.romhacking.net/community/1067) - author of BRRTools, 
  a Java program on which the BRR encoder in vcromclaim was based


