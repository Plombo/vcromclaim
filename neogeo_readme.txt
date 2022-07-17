The following are instructions that are necessary to be able to extract encrypted Neo Geo games.
Roughly half of the Neo Geo virtual console games are encrypted.
Vcromclaim will tell you if a game is encrypted, and refer to this file.

Note that "encryption" in this file refers to the Wii specific encrption.
If does NOT refer to the original encryption that some games originally had, like Metal Slug 3 and Metal Slug 4.

The steps are, roughly:
1. Run ShowMiiWads to pack the game as a Wad
2. Run the Wad in Dolphin
3. Use Dolphin's debugging tools to get the key from the emulated RAM (it is different for each game)
4. Add the key to neogeo_key.py
5. Install PyCryptodome
6. Run vcromclaim as for any other games.

These instructions are not very user friendly - FEEL FREE TO IMPROVE THEM AND SUBMIT PR!


See further below for technical details about the encryption.


DETAILED INSTRUCTIONS



Install and run ShowMiiWads- https://wiibrew.org/wiki/ShowMiiWads
Options --> Change NAND backup path --> Select the location of your Wii NAND files (the same as you specify as source for vcromclaim)
You should see all of the games in the NAND backup
Find the game you need the encryption key for
In the left most column, there is 'xxxxxxxx.tik'. Add the 8 characters xxxxxxxx to a new line in neogeo_keys.py.
Right click and select Pack Wad. Save this file somewhere convenient.



Install and run Dolphin - http://www.dolphin-emulator.com/
Make sure the views "Code", "Registers" and "Memory" are open.
Load the wad file (drag & drop or File -> Open) for the wad you packed.
When the game says "Now loading...", hit the pause button in Dolphin.
(Note: the timing kind of matters. You may have to start over from here trying hitting pause at various times).


In the Memory view, there are two text boxes at the top, the second one is "Value".
In this box, type: 812b0000
Make sure "Hex" is selected in the radio button.
Make sure "U32" is selected as data type.
Click Find next and/or Find previous. There should be exactly two matches: One on a 80xxxxxx address and one on a c0xxxxxx address.
Click Find next and/or Find previous so that the 80xxxxxx match is highlighted.
Right click on the highlighted address 80xxxxxx (the leftmost column) and select copy address.
In Code, in the textbox Search address, paste the address you copied and hit Enter.
The highlighted line in the Code view should be:

80xxxxxx lwz r9, 0 (r11)
followed by:
80xxxxyy rlwinm r12, r10, 16, 0, 15 (0000ffff)

This is one of the instructions that read part of the encryption key from RAM during decryption.

Right click the "80xxxxxx lwz" line and pick "Run to here".
Click Play to resume execution.
It will pause again once the execution is at this line which will be very quick).
If the game starts (beyond Now loading), it's too late, the decryption has already been done, if so, stop emulation completely and start over Try hitting pause earlier.

Now, look at the Registers view.
Look for r11. This is the CPU register that holds the address to RAM where the key is stored.
There will be *another* 80xxxxxx address. Double click it, select it and copy it.
(Note - you might get the wrong key, this code is run with a few different keys, only one of the keys is correct.
You may want to experiment pausing emulation earlier and repeatedly pressing play until the value in r11 changes.)

Back to the Memory view. In the top text box (Search Address), paste the last address.
The address will be highlighted.
The 4 blocks of characters next to the address is the encryption key!

Open the neogeo_keys.py file and add the encryption key (whithout spaces) to it.

NOTE: that the memory view will move around if you try to click on the data,
so the easiest way to copy the entire value is to manually copy it.

NOTE: Since neogeo_keys.py is Python, be careful to use the correct whitespace on each line.

Finally, install PyCryptodome by typing in terminal:
pip install pycryptodome
Read more about it here if necessary: https://pypi.org/project/pycryptodome/
PyCrypto should also work.

NOTE: If game extraction crash with an unclear error message, you probably got the wrong key. Make sure you copied the key correctly or look for another key as described above.


TECHNICAL DETAILS ABOUT THE KEYS AND NEO GEO VIRTUAL CONSOLE ENCRYPTION


The encrypted games are packed similarly to non-encrypted games:
There is one DOL file (the emulator), and one U8 archive.
The U8 archive contains several files, one of them contains all of the ROMs, the other are config files etc.
The ROMs file can either be plain, compressed or compressed and then encrypted.
For the encrypted files, the first 20 bytes is a header, the rest is the encrypted data.
It is encrypted using 128-bit (16 byte blocks) AES in CBC mode.
The IV is just zeroes.

The key is the problem... It is constructed using the following:
- The 20 first bytes of the encrypted file (different for each game)
- A 128byte block of random data in the DOL file (probably same for every game)
- 16 bytes of data constructed by some code (probably same for each game)
- ?????? (there is more, which is different for each game, but I've given up digging deeper,
    I can imagine it is the checksum of the DOL file or something like that)

Between each merging of the above data, A TON of bitshifting, byteswapping, xoring etc etc is done.

So it's definitly POSSIBLE to automatically rebuild the encryption keys from a NAND backup.
However, I can't justify spending the time reverse-engineering this.
