#FACTS about Ghosts n Goblins on Wii Virtual Console:
# - When played on Wii, it looks like the English verison of the game.
# - The Wii emulator also skips the glitching boot up screens and the RAM/ROM self-tests that are normal on real hardware.
#       Not sure how it is done, possibly the emulator has a built-in save-state that is always loaded.

# - The ROMs stored in the Wii version is identical to "makaimurg" in MAME (Makai-Mura, Japanese revision G). It is NOT a clean match of any other MAME sets. 
# - 2 tiny roms at 256 bytes each are completely missing, but all other files have correct checksums.
# - The missing files are not used by MAME, according to MAME's source code, so the game should be as accurate as it gets despite the checksum warning on startup.
# - The rom set is the JAPANESE version of the game!

# - The differences between Japanese and English versions of the game are very small, most notably the title screen is different.
# - The Japanese ROMs even have the English title screen included in the ROM, probably there is just some flags in the P ROM deciding region.
# - It seems the Wii emulator is patching the P ROMs. 2 of the 3 PROMs have a total of 10-20 changed bytes scattered throughout,
#        which probably change the title screen to English, possibly other things like reduce flickering.
# - Applying the patches to the PROMs mentioned above will cause the self-test to fail ("ROM BAD"). Probably the P ROMs have a checksum that is not patched on Wii

# - So, to get the English version as played on Wii would probably require us to
#    (1) Repeat the patches that are applied by Wii emulator
#    (2) Further patch the ROMs with correct checksum


# ABOUT SAVE DATA:
#   Wii stores the high scores as part of save data.
#   MAME does NOT load or save high scores in this game. 
#   Not sure if the real hardware keeps high score when power is off.
#   Since MAME does not read the save data, I don't know what format it should be exported to, so I don't export it.
#   But if needed, it should be very easy to export it. It is not compressed or anything. It might need to be truncated though, most of the file is blank.



# ROM hashes taken from:
# https://github.com/mamedev/mame/blob/master/src/mame/capcom/gng.cpp




import os, hashlib, sys
import lz77




def create_rom_folder(parentFolder, romFolderName):
    newFolder = os.path.join(parentFolder, romFolderName)
    if not os.path.lexists(newFolder):
        os.makedirs(newFolder)
    return newFolder


def export_rom(output_folder, file_name, dol_bytearray, index, length):
    outputfile = open(os.path.join(output_folder, file_name), 'wb')
    outputfile.write(dol_bytearray[index : index+length])
    outputfile.close()


def export_roms_from_dol(dol_bytearray, output_parent_folder):

    output_folder = create_rom_folder(output_parent_folder, 'makaimurg')

    # these two files does not exist in Wii, and according to mame source code, mame does not use them, but wont start without them
    dummy_files = bytearray(0x100)
    export_rom(output_folder, 'tbp24s10.14k', dummy_files, 0, 0x100)
    export_rom(output_folder, '63s141.2e', dummy_files, 0, 0x100)

    print("Scanning file for ROMs...")

    # This method is obviously terribly slow, but should be more reliable if there are different version of the game (different regions?)
    # and should be easier to adapt to other games

    for i in range(0, len(dol_bytearray)):
        
        digest = hashlib.sha1(dol_bytearray[i:i+0x8000]).hexdigest()
        if digest == '23a0a17d0abc4b084ffeba90266ef455361771cc':
            export_rom(output_folder, 'mj03g.bin', dol_bytearray, i, 0x8000)
        elif digest == '7694a981a6196d77fd2279fc34042b4cfb40c054':
            export_rom(output_folder, 'mj05g.bin', dol_bytearray, i, 0x8000)
        elif digest == '7ef9ec5c2072e21c787a6bbf700033f50c759c1d':
            export_rom(output_folder, 'gg2.bin', dol_bytearray, i, 0x8000)


        digest = hashlib.sha1(dol_bytearray[i:i+0x4000]).hexdigest()

        if digest == '07f7cf788810a1425016e016ce3579adb3253ac7':
            export_rom(output_folder, 'mj04g.bin', dol_bytearray, i, 0x4000)
        elif digest == '0a1518e19a2e0a4cc3dde4b9568202ea911b5ece':
            export_rom(output_folder, 'gg1.bin', dol_bytearray, i, 0x4000)
        elif digest == 'f9d77eee5e2738b7e83ba02fcc55dd480391479f':
            export_rom(output_folder, 'gg11.bin', dol_bytearray, i, 0x4000)
        elif digest == '8434c994cc55d2586641f3b90b6b15fd65dfb67c':
            export_rom(output_folder, 'gg10.bin', dol_bytearray, i, 0x4000)
        elif digest == 'bbb1fba0eb19471f66d29526fa8423ccb047bd63':
            export_rom(output_folder, 'gg9.bin', dol_bytearray, i, 0x4000)
        elif digest == '1c42fa02cb27b35d10c3f7f036005e747f9f6b79':
            export_rom(output_folder, 'gg8.bin', dol_bytearray, i, 0x4000)
        elif digest == '1947f159189b3a53f1251d8653b6e7c65c91fc3c':
            export_rom(output_folder, 'gg7.bin', dol_bytearray, i, 0x4000)
        elif digest == '944da1ce29a18bf0fc8deff78bceacba0bf23a07':
            export_rom(output_folder, 'gg6.bin', dol_bytearray, i, 0x4000)
        elif digest == '13e5a38a134bd7cfa16c63a18fa332c6d66b9345':
            export_rom(output_folder, 'gng13.n4', dol_bytearray, i, 0x4000)
        elif digest == '9e06012bcd82f98fad43de666ef9a75979d940ab':
            export_rom(output_folder, 'gg16.bin', dol_bytearray, i, 0x4000)
        elif digest == 'e3a1421d465b87148ffa94f5673b2307f0246afe':
            export_rom(output_folder, 'gg15.bin', dol_bytearray, i, 0x4000)
        elif digest == 'af207f9ee2f93a0cf9cf25cfe72b0fdfe55481b8':
            export_rom(output_folder, 'gng16.l4', dol_bytearray, i, 0x4000)
        elif digest == 'cb641c25bb04b970b2cbeca41adb792bbe142fb5':
            export_rom(output_folder, 'gg13.bin', dol_bytearray, i, 0x4000)
        elif digest == '3f129ca6d695548b659955fe538584bd9ac2ff17':
            export_rom(output_folder, 'gg12.bin', dol_bytearray, i, 0x4000)

        # these files don't seem to exist, and mame does not use them 
        #digest = hashlib.sha1(dol_bytearray[i:i+0x100]).hexdigest()
        #if digest == 'bafd4108708f66cd7b280e47152b108f3e254fc9':
        #    export_rom(output_folder, 'tbp24s10.14k', dol_bytearray, i, 0x100)
        #elif digest == '5018c3950b675af58db499e2883ecbc55419b491':
        #    export_rom(output_folder, '63s141.2e', dol_bytearray, i, 0x100)
        
        if (i % 10240 == 0):
            sys.stdout.write("\r  %5.2f%%" % ((100 * i) / (len(dol_bytearray)+1)))
            sys.stdout.flush()

    print() # start a new line after the progress counter


def export_roms_from_lzh_compressed_dol(lzh_dol_file, output_parent_folder):
    print("Warning: Save data (highscores) are not exported because MAME does not persist them.")
    
    data = lz77.decompress_nonN64(lzh_dol_file)
    export_roms_from_dol(bytearray(data), output_parent_folder)
