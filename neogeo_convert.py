#!/usr/bin/env python3

import struct, os, hashlib

import neogeo_acm
import neogeo_cmc_gfx, neogeo_cmc_m1, neogeo_sma, neogeo_smc
from arcade_utilities import getAsymmetricPart, getPart, getPartByDivision, getStripes, pad

HEADER_LENGTH = 64
KILOBYTE = 1024


#invaluable source: https://github.com/mamedev/mame/blob/master/src/mame/neogeo/neogeo.cpp

# To run Neo Geo games in mame, place the two folders (the game folder and the aes/neogeo bios-folder)
# to the "roms" in the mame folder.
# You can move the folders from the BIOS folder to the game folder if you want.
# You can also run an MVS game with AES rom or vice versa. Sometimes this will change the game.
# To run a game such as magdrop3 with an AES rom:
#       .\mame64 aes -cart magdrop3 -bios japan
# To run a game such as kotm with an MVS (neogeo) rom:
#       .\mame64 kotm -bios japan-mv1b



# inputFile must be a game.bin file, which is NOT compressed or encrypted.
# outputFolder should exist and be empty.
# returns True if the file was understood.
def convert_neogeo(inputFile, outputFolder):

    inputProcessor = input_processor(inputFile)
    ngh = inputProcessor.getNgh()

    supportedGames = {
        '001': (convert_nam1975, "nam1975"),
        '005': (convert_maglordh, "maglordh"),
        '016': (convert_kotm, "kotm"),
        '062': (convert_spinmast, "spinmast"),
        '200': (convert_turfmast, "turfmast"),
        '201': (convert_mslug, "mslug"),
        '223': (convert_rbffspec, "rbffspec"),
        '233': (convert_magdrop3, "magdrop3"),
        '238': (convert_shocktro, 'shocktro'),
        '241': (convert_mslug2, "mslug2"),
        '242': (convert_kof98h, "kof98h"),
        '243': (convert_lastbld2, "lastbld2"),
        '246': (convert_shocktr2, "shocktr2"),
        '250': (convert_mslugx, "mslugx"),
        '256': (convert_mslug3, "mslug3"),
        '263': (convert_mslug4, "mslug4")
    }

    if supportedGames.__contains__(ngh):
        mameShortName = supportedGames[ngh][1]
        func = supportedGames[ngh][0]
    else:
        print("Game is unknown. You will have to rename the folder and probably have to split, merge and/or byteswap the ROM files.")
        mameShortName = "NGM-" + ngh
        func = convert_generic_guess

    outputProcessor = output_processor(outputFolder, mameShortName, ngh)
    func(inputProcessor, outputProcessor)
    convert_common(inputProcessor, outputProcessor)




# Game specific conversion functions below.

# Perhaps, if we can get the region size and some game ID from the VC files somehow, we can automatically
# parse this https://github.com/mamedev/mame/blob/master/hash/neogeo.xml to retrieve the appropriate filenames?

#MVS or AES?
#At least one game is definitly the AES version (Magician Lord)
#The rest have the same ROMs for AES/MVS, or has different ROMs but neither match the ones from VC.
#On the Wii, the games run in AES mode.

# C = Characters = most of the sprites. If graphic is completely garbled, one or more of these files are not correctly exported.
# P = Program = If you get grid covering the screen, instead of Neo Geo intro, this one is probably incorrect
# S = Sprites = The smaller static sprites, such as overlay texts
# V = Audio data
# M = Music program
# BIOS = System Program = Probably an AES BIOS, since games run in home console mode on VC. Haven't gotten this to run in MAME yet.




def convert_nam1975(input, output):
    
    # same for both MVS and AES
    # All ROMs have correct CRC according to mame.

    output.createFile("p1.p1", input.regions['P'].data)
    output.createFile("m1.m1", input.regions['M'].data + input.regions['M'].data + input.regions['M'].data + input.regions['M'].data)

    split_region(input, output, 'V1', ['v11.v11'])
    split_region(input, output, 'V2', ['v21.v21', 'v22.v22', 'v23.v23'])

    output.createFile("s1.s1", pad(input.regions['S'].data, 128*KILOBYTE))

    convert_common_c(input, output, 3)


def convert_maglordh(input, output):
    
    # maglordh: CRC of all files match
    # maglord: CRC of all files match except p1
    # shipped with MVS BIOS

    output.createFile("p1.p1", input.regions['P'].data)
    
    m = input.regions['M'].data
    output.createFile("m1.m1", getPart(m, 0,64*KILOBYTE) + getPart(m, 2, 64*KILOBYTE) + getPart(m, 1, 64*KILOBYTE) + getPart(m, 2, 64*KILOBYTE))

    split_region(input, output, 'V1', ['v11.v11'])
    split_region(input, output, 'V2', ['v21.v21', 'v22.v22'])

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 3)


   

def convert_kotm(input, output):

    #Not 100% sure this is the MVS version (kotm) or AES version (kotmh).
    #P1 ROM has wrong checksom for both kotm (p1.p1) and kotmh (hp1.p1). All other files have correct checksum for both.
    #Shipped with MVS BIOS, so assuming it is the MVS version.

    output.createFile("p1.p1", getAsymmetricPart(input.regions['P'].data, 0*KILOBYTE, 512*KILOBYTE))
    output.createFile("p2.p2", pad(getAsymmetricPart(input.regions['P'].data, 512*KILOBYTE, 64*KILOBYTE), 128*KILOBYTE))

    output.createFile("m1.m1", input.regions['M'].data)

    split_region(input, output, 'V1', ['v1.v1', 'v2.v2'])

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 2)

def convert_spinmast(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for p*, otherwise all CRCs match
    # Shipped with AES BIOS

    output.createFile("p1.p1", getPart(input.regions['P'].data, 0, 1024*KILOBYTE))
    output.createFile("p2.sp2", getPart(input.regions['P'].data, 1, 1024*KILOBYTE))

    output.createFile("m1.m1", input.regions['M'].data)

    split_region(input, output, 'V1', ['v1.v1'])

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 4)

def convert_turfmast(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for v4, otherwise all CRCs match
    # Shipped with MVS BIOS

    # banks are in reverse order
    output.createFile("p1.p1", 
        getPart(input.regions['P'].data, 1, 1024*KILOBYTE)
        + getPart(input.regions['P'].data, 0, 1024*KILOBYTE))
    
    output.createFile("m1.m1", input.regions['M'].data)

    split_region(input, output, 'V1', ['v1.v1', 'v2.v2', 'v3.v3', 'v4.v4'])

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 1)



def convert_mslug(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for p1, otherwise all CRCs match
    # Shipped with MVS BIOS

    output.createFile("p1.p1", 
        getPart(input.regions['P'].data, 1, 1024*KILOBYTE)
        + getPart(input.regions['P'].data, 0, 1024*KILOBYTE))

    output.createFile("m1.m1", input.regions['M'].data)

    split_region(input, output, 'V1', ['v1.v1', 'v2.v2'])

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 2)

def convert_rbffspec(input, output):

    # Same ROM for MVS/AES
    # p1 rom has wrong checksum, all others have correct checksum

    output.createFile("p1.p1", getAsymmetricPart(input.regions['P'].data, 0*KILOBYTE, 1024*KILOBYTE))
    output.createFile("p2.sp2", getAsymmetricPart(input.regions['P'].data, 1024*KILOBYTE, 4*1024*KILOBYTE))

    output.createFile("m1.m1", input.regions['M'].data)

    split_region(input, output, 'V1', ['v1.v1', 'v2.v2', 'v3.v3'])

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 4)

def convert_magdrop3(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for p1 and v2, otherwise all CRCs match.
    # In p1, there are only a few bytes changed. The differences are around 0x71120.
    # For the VC version, some of the frames of the Tower character's flashing
    # lightning strike animation has been removed.
    # Shipped with AES BIOS

    output.createFile("p1.p1", input.regions['P'].data)

    output.createFile("m1.m1", input.regions['M'].data)

    output.createFile("v1.v1", getPart(input.regions['V1'].data, 0, 4*1024*KILOBYTE))
    output.createFile("v2.v2", getPart(input.regions['V1'].data, 1, 1*512*KILOBYTE))

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 2)

def convert_shocktro(input, output):

    # Shipped with AES BIOS
    # All file except pg1.p1 has correct CRC.
    # The AES and MVS original has different P1s, the VC version matches none of them,
    # so not sure if the VC version is based of the MVS or AES version.

    output.createFile("pg1.p1", getAsymmetricPart(input.regions['P'].data, 0, 1*1024*KILOBYTE))
    
    output.createFile("p2.sp2", getAsymmetricPart(input.regions['P'].data, 1024*KILOBYTE, 4*1024*KILOBYTE))

    output.createFile("m1.m1", input.regions['M'].data)

    output.createFile("v1.v1", getAsymmetricPart(input.regions['V1'].data, 0*KILOBYTE, 4*1024*KILOBYTE))
    output.createFile("v2.v2", getAsymmetricPart(input.regions['V1'].data, 4*1024*KILOBYTE, 2*1024*KILOBYTE))

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 4)

def convert_mslug2(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for p*, otherwise all CRCs match
    # Shipped with MVS BIOS

    output.createFile("p1.p1", getAsymmetricPart(input.regions['P'].data, 0*KILOBYTE, 1024*KILOBYTE))
    output.createFile("p2.sp2", getAsymmetricPart(input.regions['P'].data, 1024*KILOBYTE, 2*1024*KILOBYTE))

    output.createFile("m1.m1", input.regions['M'].data)

    split_region(input, output, 'V1', ['v1.v1', 'v2.v2'])

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 2)

def convert_kof98h(input, output):

    # wrong CRC for kof98h (MVS/AES), but works
    # kof98 (MVS) has encrypted code
    # to be able to play this as "kof98" in mame, we would need to encrypt this ROM, reversing: https://github.com/ColumPaget/gngeo-cjp/blob/master/src/neocrypt.c
    output.createFile("pn1.p1", getAsymmetricPart(input.regions['P'].data, 0*KILOBYTE, 1024*KILOBYTE))

    output.createFile("p2.sp2", getAsymmetricPart(input.regions['P'].data, 1024*KILOBYTE, 4*1024*KILOBYTE))

    # used for kof98 (MVS), correct CRC!
    # output.createFile("m1.m1", input.regions['M'].data)

    # used for kof98h (MVS/AES). wrong CRC!
    output.createFile("mg1.m1", input.regions['M'].data)

    split_region(input, output, 'V1', ['v1.v1', 'v2.v2', 'v3.v3', 'v4.v4'])

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 4)

def convert_lastbld2(input, output):

    # Same ROM for MVS/AES
    # Shipped with AES BIOS

    # All roms except PG1 have correct checksums

    output.createFile("pg1.p1", getAsymmetricPart(input.regions['P'].data, 0*KILOBYTE, 1024*KILOBYTE))
    output.createFile("pg2.sp2", getAsymmetricPart(input.regions['P'].data, 1024*KILOBYTE, 4*1024*KILOBYTE))

    output.createFile("m1.m1", input.regions['M'].data)

    split_region(input, output, 'V1', ['v1.v1', 'v2.v2', 'v3.v3', 'v4.v4'])

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 3)
    
def convert_shocktr2(input, output):

    # Same ROM for MVS/AES
    # Shipped with AES roms
    # All roms except P2 has correct checksum

    output.createFile("p1.p1", getAsymmetricPart(input.regions['P'].data, 0*KILOBYTE, 1024*KILOBYTE))
    output.createFile("p2.sp2", getAsymmetricPart(input.regions['P'].data, 1024*KILOBYTE, 4*1024*KILOBYTE))

    output.createFile("m1.m1", input.regions['M'].data)

    output.createFile("v1.v1", getAsymmetricPart(input.regions['V1'].data, 0*1024*KILOBYTE, 4*1024*KILOBYTE))
    output.createFile("v2.v2", getAsymmetricPart(input.regions['V1'].data, 4*1024*KILOBYTE, 4*1024*KILOBYTE))
    output.createFile("v3.v3", getAsymmetricPart(input.regions['V1'].data, 8*1024*KILOBYTE, 2*1024*KILOBYTE))

    output.createFile("s1.s1", input.regions['S'].data)

    convert_common_c(input, output, 3)

def convert_mslugx(input, output):

    # Same ROMs for MVS/AES

    # wrong CRC
    output.createFile("p1.p1", getAsymmetricPart(input.regions['P'].data, 0*KILOBYTE, 1024*KILOBYTE))

    # correct CRC
    output.createFile("p2.ep1", getAsymmetricPart(input.regions['P'].data, 1024*KILOBYTE, 4*1024*KILOBYTE))
    output.createFile("m1.m1", input.regions['M'].data)
    output.createFile("v1.v1", getAsymmetricPart(input.regions['V1'].data, 0*1024*KILOBYTE, 4*1024*KILOBYTE))
    output.createFile("v2.v2", getAsymmetricPart(input.regions['V1'].data, 4*1024*KILOBYTE, 4*1024*KILOBYTE))
    output.createFile("v3.v3", getAsymmetricPart(input.regions['V1'].data, 8*1024*KILOBYTE, 2*1024*KILOBYTE))
    output.createFile("s1.s1", input.regions['S'].data)
    convert_common_c(input, output, 3)

def convert_mslug3(input, output):

    # Comes with AES bios

    #v1 and m1 hash matches mslug3, mslug3a, mslug3h.
    output.createFile("m1.m1", input.regions['M'].data)
    split_region(input, output, 'V1', ['v1.v1', 'v2.v2', 'v3.v3', 'v4.v4'])

    encypted_pdata = neogeo_sma.mslug3_encrypt_68k(bytearray(input.regions['P'].data))

    # the first 3*256KB of the encrypted data is garbage: real ROMs are only 256KB + 8MB,
    # when decrypting it grows to 9 MB, when encryptng it shrinks again)

    # correct checksum for a rom only found in "mslug3", not mslug3a or mslug3h
    # the "green" rom is untouched by encryption, can also be retrieved from original region on same address
    output.createFile("green.neo-sma", getAsymmetricPart(encypted_pdata, 3*256*KILOBYTE, 256*KILOBYTE), None, False)

    # CRC incorrect for both, but only minor binary differences. maybe anti-flashing?
    output.createFile("pg1.p1", getAsymmetricPart(encypted_pdata, 1*1024*KILOBYTE, 4*1024*KILOBYTE))
    output.createFile("pg2.p2", getAsymmetricPart(encypted_pdata, 5*1024*KILOBYTE, 4*1024*KILOBYTE))

    # C ROM (includes S ROM)
    # key found in https://github.com/mamedev/mame/blob/master/src/devices/bus/neogeo/prot_cmc.h
    convert_c(neogeo_cmc_gfx.encrypt_cmc42_gfx(get_decompressed_c(input), 0xAD), output, 4, [[0,2],[1,3]])


def convert_mslug4(input, output):

    # wrong checksum for both MVS and AES, but seems to work
    output.createFile("p1.p1", getAsymmetricPart(input.regions['P'].data, 0*KILOBYTE, 1024*KILOBYTE))

    # correct CRC for MVS version, not for AES version
    output.createFile("p2.sp2", getAsymmetricPart(input.regions['P'].data, 1024*KILOBYTE, 4*1024*KILOBYTE))

    # V1: checsum OK    
    split_region_by_data(neogeo_smc.swap_8_byte_pairs(bytearray(input.regions['V1'].data)), output, ['v1.v1', 'v2.v2'])

    # Original hardware has decryption hardware for S, M and C, which MAME emulates.
    # Hence MAME and original hardware expects encrypted ROMs.
    # Wii comes with decrypted ROMs.
    # We need to encrypt them to make them playable with MAME.

    # C ROM (includes S ROM)
    # key found in https://github.com/mamedev/mame/blob/master/src/devices/bus/neogeo/prot_cmc.h
    convert_c(neogeo_cmc_gfx.encrypt_cmc50_gfx(get_decompressed_c(input), 0x31), output, 3, [[0,2],[1,3]])

    # Note: MAME does additional unscrambling of the S part at the end of the C ROM.
    # We do not have to scramble it, because the decrypted Wii C ROM version already contains the
    # scrambled S portion. (The Wii version ALSO contains this as an separate unscrambled S ROM, which
    # we ignore)

    # M1: checksum OK
    output.createFile("m1.m1", neogeo_cmc_m1.encrypt_cmc50_m1(input.regions['M'].data))


def convert_generic_guess(input, output):
    output.createFile("p1.p1", input.regions['P'].data)
    output.createFile("m1.m1", input.regions['M'].data)
    
    if len(input.regions['V2'].data) == 0:
        split_region(input, output, 'V1', ['v1.v1'])
    else:
        split_region(input, output, 'V1', ['v11.v11'])
        split_region(input, output, 'V2', ['v21.v21'])

    convert_common_c(input, output, 2)










# end of game specific code



def split_region(input, output, regionName, outputNameList):
    split_region_by_data(input.regions[regionName].data, output, outputNameList)

def split_region_by_data(regionData, output, outputNameList):
    sizePerPart = int(len(regionData) / len(outputNameList))
    i = 0
    for outputName in outputNameList:
        output.createFile(outputName, getPart(regionData, i, sizePerPart))
        i = i+1



# converts the C data region to several NNN-cN.cN-files. length varies between games.
# length = the number of striped blocks (must be 1 or more - 1,2,3,4 are common).
# number of roms will be length*2
# size per rom will be size of C region / (length*2)
def get_decompressed_c(input):
    if input.regions['C'].data[0:3] == b'ACM':
        return neogeo_acm.decompressAcm(input.regions['C'].data)
    else:
        return input.regions['C'].data

# converts the C data region to several NNN-cN.cN-files. length varies between games.
# length = the number of striped blocks (must be 1 or more - 1,2,3,4 are common).
# number of roms will be length*2
# size per rom will be size of C region / (length*2)
def convert_common_c(input, output, length):
    if input.regions['C'].data[0:3] == b'ACM':
        convert_c(get_decompressed_c(input), output, length, [[0,1],[2,3]])
    else:
        convert_c(input.regions['C'].data, output, length, [[0,2],[1,3]])




# converts the C data to several NNN-cN.cN-files. length varies between games.
# length = the number of striped blocks (must be 1 or more - 1,2,3,4 are common).
# stripeMap - An array with two items. Each item must be an array of two items. The four items must be 0,1,2,3.
#   The stripes in the first array will placed in the odd C-roms, the second array in even C-roms.
# number of roms will be length*2
# size per rom will be size of C region / (length*2)
def convert_c(data, output, length, stripeMap):

    assert length > 0
    width = 2

    for i in range(0, length):
        
        fileIndex = i*width + 1
        dataPart =  getPartByDivision(data, i, length)

        # In original ROMs, bitplane 0 and 1 is in odd roms, and 1 and 2 is in even roms.
        # In the VC large C data area, they are stored as bitplane 0, bitplane 2, bitplane 1, bitplane 4.

        for j in range(0,width):
            output.createFile(
                "c" + str(fileIndex + j) + ".c" + str(fileIndex + j),
                getStripes(dataPart, stripeMap[j])
            )


def convert_common(input, output):

    #BIOS - all games so far comes with either an MVS or an AES BIOS.
    # use SHA1 to identify it

    # These are the same hashes as on: https://github.com/mamedev/mame/blob/master/src/mame/drivers/neogeo.cpp
    biosList = {
        "e92910e20092577a4523a6b39d578a71d4de7085": "mvs", #"japan-j3.bin"], #Japan MVS (J3)
        "4e4a440cae46f3889d20234aebd7f8d5f522e22c": "aes", #"neo-po.bin"] #Japan AES
    }

    hexDigest = input.regions['BIOS'].getSha1HexDigest()
    if biosList.__contains__(hexDigest) and (biosList[hexDigest] == "mvs"):
        convert_bios_files(input, output, 'mvs-jp',                   True,  True, 0x00)
        convert_bios_files(input, output, 'mvs-jp-patched-to-mvs-us', True,  True, 0x01)
        convert_bios_files(input, output, 'mvs-jp-patched-to-mvs-eu', True,  True, 0x02)
        convert_bios_files(input, output, 'mvs-jp-patched-to-aes-jp', False, True, 0x00)
        convert_bios_files(input, output, 'mvs-jp-patched-to-aes-us', False, True, 0x01)
        convert_bios_files(input, output, 'mvs-jp-patched-to-aes-eu', False, True, 0x02)

        #It's an MVS ROM. Some support roms are missing, they are not required for the game to run but mame wont run if at least the files doesn't exist.
        print("This game includes MVS (arcade) BIOS ROMs.")
        print("Pick the original or one of the patched sets, and play the game in MAME using:")
        print("   .\\mame64 " + output.mameShortName + " -bios japan-mv1b")
    elif biosList.__contains__(hexDigest) and (biosList[hexDigest] == "aes"):
        convert_bios_files(input, output, 'aes-jp',                   False, False, 0x00)
        convert_bios_files(input, output, 'aes-jp-patched-to-aes-us', False, False, 0x01)
        convert_bios_files(input, output, 'aes-jp-patched-to-aes-eu', False, False, 0x02)
        convert_bios_files(input, output, 'aes-jp-patched-to-mvs-jp', True,  False, 0x00)
        convert_bios_files(input, output, 'aes-jp-patched-to-mvs-us', True,  False, 0x01)
        convert_bios_files(input, output, 'aes-jp-patched-to-mvs-eu', True,  False, 0x02)

        # The only support rom is l0 which is created below
        print("This game includes AES (home) BIOS ROMs.")
        print("Pick the original or one of the patched sets, and play the game in MAME using:")
        print("   .\\mame64 aes -cart " + output.mameShortName + " -bios japan")
    else:
        print("Warning: The included BIOS is not recognized. SHA1 hash: " + hexDigest)
        output.createFile('unknown-bios', input.regions['BIOS'].data)
    

    #UNKNOWN DATA. should be zero but we might be missing something
    for i in range(1,8):
        regionKey = 'X' + str(i)
        regionData = input.regions[regionKey].data
        if len(regionData) > 0:
            print("WARNING: Game contains data which belongs to unknown ROM. Maybe additional system ROMs?")
            print("SHA1:" + input.regions[regionKey].getSha1HexDigest())
            output.createFile(regionKey + "." + regionKey, regionData)


def convert_bios_files(input, output, biosOutputFolder, mvsFlag, actuallyMvs, regionByte):
    fileName = 'japan-j3.bin' if actuallyMvs else 'neo-po.bin'
    folderName = 'neogeo' if actuallyMvs else 'aes'
    folderPath = os.path.join(biosOutputFolder, folderName)
    
    data = bytearray(input.regions['BIOS'].data)

    # this tells games which region the game is in (00 = jap, 01 = us, 02 = eur)
    # Wii usually patch this to 0x01
    originalRegionByte = data[0x400]
    data[0x400] = regionByte

    # this tells games whether it is an mvs or aes console.
    # Wii usually patch this to 0x00
    originalMvsFlagValue = data[0x401]
    newMvsFlagValue = 0x80 if mvsFlag else 0x00
    data[0x401] = 0x80 if mvsFlag else 0x00
    
    if actuallyMvs and (originalMvsFlagValue != newMvsFlagValue or originalRegionByte != regionByte):

        # The above patches cause an internal checksum test to fail on MVS system roms.
        # The Wii emulator does a similar patch.

        for address in range(0x10C62, 0x10D44, 2):
            # NOP instruction
            data[address:address+2] = b'\x71\x4E'

        for address in range(0x10D86, 0x10D8A, 2):
            # NOP instruction
            data[address:address+2] = b'\x71\x4E'


    output.createFile(fileName, data, subFolder = folderPath)

    # 000-lo.lo is required for all games.
    # On VC, the data exists in RAM, not sure if it is generated or decompressed from somewhere.
    output.createFile('000-lo.lo', get_l0(), subFolder = folderPath)

    if (actuallyMvs):
        # SFIX is only used on arcade machines, contains graphics to use when no cartridge is inserted
        # A file filled with 0s is interpreted as transparent graphics
        output.createFile('sfix.sfix', bytearray(b'\x00' * 0x20000), subFolder = folderPath)

        # output.createFile('sfix.sfix', bytearray('\x11\x00\x10\x01\x01\x10\x00\x11\x11\x11\x10\x10\x10\x10\x11\x11\x11\x11\x01\x01\x01\x01\x11\x11\x11\x00\x01\x10\x10\x01\x00\x11' * (0x20000 / 32)), subFolder = subFolder)
        # SM1 is only used on arcade machines, contains music program to use when no cartridge is inserted
        output.createFile('sm1.sm1', bytearray(b'\x00' * 0x20000), subFolder = folderPath)





def get_l0():
    # The data is 64 KiB mirrored to 128 KiB
    l0_half = get_l0_half()
    return l0_half + l0_half


def get_l0_half():
    # The L0 is a list of FF entries used when horizontally scaling sprites.
    # The first entry has 1 byte, second has 2, last has FF bytes.
    # All entries are padded by FFs to total FF bytes length.
    # Each entry describes which of the FF lines of a sprite to include at a certain scaling point.

    # The L0 table exists in RAM when Mame emulator is running, but I can't find it in files.
    # I'm guessing it is being generated so we do the same.

    nibbles = [0x08, 0x00, 0x0C, 0x04, 0x0A, 0x02, 0x0E, 0x06, 0x09, 0x01, 0x0D, 0x05, 0x0B, 0x03, 0x0F, 0x07]
    row = []
    output = bytearray(b"")
    for second_nibble in nibbles:
        for first_nibble in nibbles:
            byte = first_nibble*0x10 + second_nibble
            row.append(byte)
            row.sort()
            output = output + bytearray(row) + (b'\xFF' * (0x100 - len(row)))
    
    return output


## input/output processors

#ABOUT GAME.BIN
#After decompression, the file can have two different formats.
#Both formats contain all of the ROMs, prepended by a 40-byte header.

# ROM0-header:
# If the first four bytes of the header is "ROM0",
# The game.bin header contains up to 15 values, each representing the size of a ROM in bytes, as a four byte little-endian integer.

# The 15 vales define the size of the ROMs in this order:
# (HEADER) X X S C V X BIOS P M X X X X X X
# X is unused or unknown (maybe som ROM type unused in some game?)
# The game.bin contains the ROMs in the same order as they are listed above. (S C V BIOS P M)

# If the first four bytes are NOT 'ROM0',
# The game.bin header contains 8 pairs of 2 values, where each value is a four byte little-endian integer.
# The first value of each pair is the position of the ROM type (including the header, i.e. the first ROM within game.bin is at position 40).
# The second value of each pair is the size of the ROM in bytes.

# The pairs denote the position and size of the ROMs in this order.
# P M V1 V2 X S C BIOS
# X is unknown and 0 for both position and length - maybe some ROM type only used in some games?







class region(object):
    #indexInOldHeader: The index of the position-length pair in the old style header.
    #indexInRom0Header: The index of the length value in the new style header.
    def __init__(self, parentInputProcessor, indexInOldHeader, indexInRom0Header, byteSwappedRegion = False):
        
        def byteSwap(fileData):
            intdata = struct.unpack('>' + str(int(len(fileData)/2)) + 'H', fileData)
            return struct.pack('<' + str(int(len(fileData)/2)) + 'H', *intdata)
        
        self.indexInOldHeader = indexInOldHeader
        self.indexInRom0Header = indexInRom0Header
        (position, length) = parentInputProcessor.getRegionPositionAndLength(indexInOldHeader,indexInRom0Header)
        
        data = parentInputProcessor.getRegionData(position, length)
        
        if byteSwappedRegion:
            data = byteSwap(data)
        
        self.data = data


    def getSha1HexDigest(self):
        return hashlib.sha1(self.data).hexdigest()
        





class input_processor(object):


    def __init__(self, inputFile):
        self.inputFile = inputFile

        self.regions = {
            'S': region(self, 5, 2),
            'C': region(self, 6, 3),

            # V1 becomes v1.v1, v2.v2, etc OR v11.v11, v12.v12, etc
            'V1': region(self, 2, 4),
            # V2 becomes v21.v21, v22.v22, etc.
            'V2': region(self, 3, 5),

            'BIOS': region(self, 7, 6, True),
            'P': region(self, 0, 7, True),
            'M': region(self, 1, 8),

            # unknown or unused should always be 0 or we are missing something
            'X1': region(self, 4, -1),
            'X2': region(self, -1, 9),
            'X3': region(self, -1, 10),
            'X4': region(self, -1, 11),
            'X5': region(self, -1, 12),
            'X6': region(self, -1, 13),
            'X7': region(self, -1, 14)
        }


    # returns the start position of the region (in bytes, including header offset) and the length of it, according to the header.
    def getRegionPositionAndLength(self, indexInOldHeader, indexInRom0Header):

        self.inputFile.seek(0)
        firstBytesOfHeader = self.inputFile.read(4)
        if (firstBytesOfHeader == b'ROM0') and (indexInRom0Header >= 0):
            position = HEADER_LENGTH
            for i in range(0, indexInRom0Header):
                position += struct.unpack('>I', self.inputFile.read(4)) [0]
            length = struct.unpack('>I', self.inputFile.read(4)) [0]
            return (position, length)
        elif (firstBytesOfHeader != b'ROM0') and indexInOldHeader >= 0:
            self.inputFile.seek(indexInOldHeader * 8)
            pair = struct.unpack('>2I', self.inputFile.read(8))
            position = pair[0]
            length = pair[1]
            return (position, length)
        else:
            return (0,0)

        

    def getRegionData(self, actualStartPosition, actualLength):
        self.inputFile.seek(actualStartPosition)
        regionData = self.inputFile.read(actualLength)
        assert len(regionData) == actualLength
        return regionData



    # Returns the three character code unique to each game, used in ROM file names
    def getNgh(self):
        # PROM: 0x108 = 0x62, 0x109 = 0x00 --> return value = "062", which is the NGH code that uniquely identify each game.
        # Official games does not seem to use A-F or the most significant digit.
    
        data = self.regions['P'].data[0x108:0x10A] # = str of length 2
        assert len(data) == 2
        intData = struct.unpack('<H', data)[0] # = integer representing the value
        hexString = "00" + str(hex(intData))[2:] # string. Values: "000"-00FFFF"
        return hexString[-3:] # string. Values: "0"-"FFF" (most significant digit is cut)




class output_processor(object):
    def __init__(self, outputFolder, mameShortName, ngh):
        self.outputFolder = outputFolder
        self.mameShortName = mameShortName
        self.ngh = ngh

    def createFile(self, fileName, fileData, subFolder = None, usePrefix = True):
        if subFolder == None:
            subFolder = self.mameShortName
            if usePrefix:
                filePrefix = self.ngh + "-"
            else:
                filePrefix = ''
        else:    
            # keep subFolder
            filePrefix = ''

        folderPath = os.path.join(self.outputFolder, subFolder)
        filePath = os.path.join(self.outputFolder, subFolder, filePrefix + fileName)

        if not os.path.lexists(folderPath):
            os.makedirs(folderPath)


        outputFile = open(filePath, 'wb')
        
        outputFile.write(fileData)

        outputFile.close()



