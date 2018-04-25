#!/usr/bin/env python

import struct, os, hashlib

HEADER_LENGTH = 64
KILOBYTE = 1024

#invaluable source: https://github.com/mamedev/mame/blob/master/src/mame/drivers/neogeo.cpp



# inputFile must be a game.bin file, which is NOT compressed or encrypted.
# wiiGameId is the game Id (8 character string). Hopefully once more games have been analyzed this can be replaced by something else - config.bin? using the header?
# outputFolder should exist and be empty.
# returns True if the file was understood.
def convert_neogeo(inputFile, outputFolder):

    inputProcessor = input_processor(inputFile)
    ngh = getNgh(inputProcessor)

    supportedGames = {
        '005': (convert_maglordh, "maglordh"),
        '016': (convert_kotm, "kotm"),
        '062': (convert_spinmast, "spinmast"),
        '200': (convert_turfmast, "turfmast"),
        '201': (convert_mslug, "mslug"),
        '233': (convert_magdrop3, "magdrop3"),
        '241': (convert_mslug2, "mslug2")
    }

    if supportedGames.has_key(ngh):
        mameShortName = supportedGames[ngh][1]
        func = supportedGames[ngh][0]
    else:
        print "Game is unknown. You will have to rename the folder and probably have to split or merge the ROM files."
        mameShortName = "NGH-" + ngh
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




def convert_maglordh(input, output):
    
    # maglordh: CRC of all files match
    # maglord: CRC of all files match except p1
    # shipped with MVS BIOS

    output.createFile("p1.p1", input.regions['P'].data)
    
    m = input.regions['M'].data
    output.createFile("m1.m1", getPart(m, 0,64) + getPart(m, 2, 64) + getPart(m, 1, 64) + getPart(m, 2, 64))

    output.createFile("v11.v11", input.regions['V1'].data)
    output.createFile("v21.v21", getPart(input.regions['V2'].data,0,512))
    output.createFile("v22.v22", getPart(input.regions['V2'].data,1,512))

    convert_common_c(input, output, 2, 3)


   

def convert_kotm(input, output):

    #Not sure if this is actually kotm (MVS) or kotmh (AES) version.
    #kotm: CRC of all files except P1 match
    #kotmh: CRC of all files except P1 match
    # shipped with MVS BIOS

    output.createFile("hp1.p1", getAssymetricPart(input.regions['P'].data, 0, 512))
    output.createFile("p2.p2", pad(getAssymetricPart(input.regions['P'].data, 512, 64), 128))

    output.createFile("m1.m1", input.regions['M'].data)

    output.createFile("v1.v1", getPart(input.regions['V1'].data, 0, 1024))
    output.createFile("v2.v2", getPart(input.regions['V1'].data, 1, 1024))

    convert_common_c(input, output, 2, 2)

def convert_spinmast(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for p*, otherwise all CRCs match
    # Shipped with AES BIOS

    output.createFile("p1.p1", getPart(input.regions['P'].data, 0, 1024))
    output.createFile("p2.sp2", getPart(input.regions['P'].data, 1, 1024))

    output.createFile("m1.m1", input.regions['M'].data)

    output.createFile("v1.v1", input.regions['V1'].data)

    convert_common_c(input, output, 2, 4)

def convert_turfmast(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for v4, otherwise all CRCs match
    # Shipped with MVS BIOS

    # banks are in reverse order
    output.createFile("p1.p1", 
        getPart(input.regions['P'].data, 1, 1024)
        + getPart(input.regions['P'].data, 0, 1024))
    
    output.createFile("m1.m1", input.regions['M'].data)

    output.createFile("v1.v1", getPart(input.regions['V1'].data, 0, 2048))
    output.createFile("v2.v2", getPart(input.regions['V1'].data, 1, 2048))
    output.createFile("v3.v3", getPart(input.regions['V1'].data, 2, 2048))
    output.createFile("v4.v4", getPart(input.regions['V1'].data, 3, 2048))

    convert_common_c(input, output, 2, 1)



def convert_mslug(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for p1, otherwise all CRCs match
    # Shipped with MVS BIOS

    output.createFile("p1.p1", 
        getPart(input.regions['P'].data, 1, 1024)
        + getPart(input.regions['P'].data, 0, 1024))

    output.createFile("m1.m1", input.regions['M'].data)

    output.createFile("v1.v1", getPart(input.regions['V1'].data, 0, 4*1024))
    output.createFile("v2.v2", getPart(input.regions['V1'].data, 1, 4*1024))

    convert_common_c(input, output, 2, 2)

def convert_rbffspec(input, output):

    # Same ROM for MVS/AES
    # NOT TESTED, becaues the game.bin is encrypted

    output.createFile("p1.p1", getAssymetricPart(input.regions['P'].data, 0, 1024))
    output.createFile("p2.sp2", getAssymetricPart(input.regions['P'].data, 1024, 4*1024))

    output.createFile("m1.m1", input.regions['M'].data)

    output.createFile("v1.v1", getPart(input.regions['V1'].data, 0, 4*1024))
    output.createFile("v2.v2", getPart(input.regions['V1'].data, 1, 4*1024))
    output.createFile("v3.v3", getPart(input.regions['V1'].data, 1, 4*1024))

    convert_common_c(input, output, 2, 4)

def convert_magdrop3(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for p1 and v2, otherwise all CRCs match.
    # Shipped with AES BIOS

    output.createFile("p1.p1", input.regions['P'].data)

    output.createFile("m1.m1", input.regions['M'].data)

    output.createFile("v1.v1", getPart(input.regions['V1'].data, 0, 4*1024))
    output.createFile("v2.v2", getPart(input.regions['V1'].data, 1, 1*512))

    convert_common_c(input, output, 2, 2)

def convert_mslug2(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for p*, otherwise all CRCs match
    # Shipped with MVS BIOS

    output.createFile("p1.p1", getAssymetricPart(input.regions['P'].data, 0, 1024))
    output.createFile("p2.sp2", getAssymetricPart(input.regions['P'].data, 1024, 2*1024))

    output.createFile("m1.m1", input.regions['M'].data)

    output.createFile("v1.v1", getPart(input.regions['V1'].data, 0, 4*1024))
    output.createFile("v2.v2", getPart(input.regions['V1'].data, 1, 4*1024))

    convert_common_c(input, output, 2, 2)


def convert_generic_guess(input, output):
    output.createFile("p1.p1", input.regions['P'].data)
    output.createFile("m1.m1", input.regions['M'].data)
    
    if len(input.regions['V2'].data) == 0:
        output.createFile("v1.v1", input.regions['V1'].data)
    else:
        output.createFile("v11.v11", input.regions['V1'].data)
        output.createFile("v21.v21", input.regions['V2'].data)

    convert_common_c(input, output, 2, 2)



# converts the C data region to several NNN-cN.cN-files. width and length varies between games.
# width = must be 1, 2 or 4. Number of "stripes" the original data was divided into (and which we need to recreate).
# length = the number of striped blocks (must be 1 or more - 1,2,3,4 are common).
# number of roms will be length*width
# size per rom will be size of C region / (length*width)
def convert_common_c(input, output, width, length):

    assert width == 1 or width == 2 or width == 4
    assert length > 0

    for i in xrange(0, length):
        
        fileIndex = i*width + 1
        dataPart =  getPartByDivision(input.regions['C'].data, i, length)

        for j in xrange(0,width):
            output.createFile(
                "c" + str(fileIndex + j) + ".c" + str(fileIndex + j),
                getStripes(dataPart, range(j, 4, width))
            )


def convert_common(input, output):
    output.createFile("s1.s1", input.regions['S'].data)

    # different games come with different BIOS, for some reason
    # use SHA1 to identify it

    # These are the same hashes as on: https://github.com/mamedev/mame/blob/master/src/mame/drivers/neogeo.cpp
    biosFileNames = {
        "e92910e20092577a4523a6b39d578a71d4de7085": "japan-j3.bin", #Japan MVS (J3)
        "4e4a440cae46f3889d20234aebd7f8d5f522e22c": "neo-po.bin" #Japan AES
    }

    hexDigest = input.regions['BIOS'].getSha1HexDigest()
    if biosFileNames.has_key(hexDigest):
        biosFileName = biosFileNames[hexDigest]
    else:
        print "Warning: The included BIOS is not recognized. SHA1 hash: " + hexDigest
        biosFileName = "unknown-bios-" + hexDigest + ".bin"

    output.createFile(biosFileName, input.regions['BIOS'].data, shared = True)



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
            intdata = struct.unpack('>' + str(len(fileData)/2) + 'H', fileData)
            return struct.pack('<' + str(len(fileData)/2) + 'H', *intdata)
        
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
        if (self.inputFile.read(4) == 'ROM0') and (indexInRom0Header >= 0):
            position = HEADER_LENGTH
            for i in xrange(0, indexInRom0Header):
                position += struct.unpack('>I', self.inputFile.read(4)) [0]
            length = struct.unpack('>I', self.inputFile.read(4)) [0]
            return (position, length)
        elif indexInOldHeader >= 0:
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





class output_processor(object):
    def __init__(self, outputFolder, mameShortName, ngh):
        self.outputFolder = outputFolder
        self.mameShortName = mameShortName
        self.ngh = ngh

    def createFile(self, fileName, fileData, shared = False):
        if shared:
            folderPath = os.path.join(self.outputFolder, "bios")
            filePath = os.path.join(self.outputFolder, "bios", fileName)
        else:
            folderPath = os.path.join(self.outputFolder, self.mameShortName)
            filePath = os.path.join(self.outputFolder, self.mameShortName, self.ngh + "-" + fileName)

        if not os.path.lexists(folderPath):
            os.makedirs(folderPath)


        outputFile = open(filePath, 'wb')
        
        outputFile.write(fileData)

        outputFile.close()




#Utilities

def getAssymetricPart(fileData, startInKb, lengthInKb):
    retVal = fileData[ startInKb*KILOBYTE : (startInKb+lengthInKb)*KILOBYTE ]
    assert len(retVal) == lengthInKb*KILOBYTE
    return retVal


# e.g. if file data is 4 mb, and lengthInKb = 1024, then index 2 would retrieve the third mb of the region
def getPart(fileData, index, lengthInKb):
    retVal = fileData[ index*lengthInKb*KILOBYTE : index*lengthInKb*KILOBYTE + lengthInKb*KILOBYTE ]
    assert len(retVal) == lengthInKb*KILOBYTE
    return retVal

# E.g. to get the first half of a ROM, call with partIndex = 0, partCount = 2. To get second half, call partIndex 1, partCount = 2.
# fileData = the file data of the region.
# partIndex = the part to retrieve. (0-based index)
# partCount = the total number of parts.
# The size of the returned value will be len(fileData) / partCount.
def getPartByDivision(fileData, partIndex, partCount):
    assert partCount > 0
    assert partIndex >= 0
    assert partIndex < partCount

    partSize = len(fileData) / partCount
    
    retVal = fileData[ partIndex*partSize : partIndex*partSize + partSize ]
    assert len(retVal) == partSize
    return retVal


#stripes = [0] = get byte 0, 4, 8 etc
#stripes = [0,1] = get byte 0,1,4,5,8,9 etc
#stripes = [0,2] = get byte 0,2,4,6,8,10 etc
#stripes = [1,3] = get byte 1,3,5,7,9,11 etc
#stripes = [1,2,3,4] = get all bytes
def getStripes(fileData, stripes):
    retVal = ''
    for i in xrange(0, len(fileData), 4):
        for j in stripes:
            retVal += fileData[i+j]
    return retVal





def pad(fileData, totalLengthInKilobytes):
    actualTotalLength = totalLengthInKilobytes * KILOBYTE
    assert actualTotalLength >= len(fileData)
    return fileData + '\xFF'*(actualTotalLength-len(fileData))


# Returns the three character code unique to each game, used in ROM file names
def getNgh(inputProcessor):
    # PROM: 0x108 = 0x62, 0x109 = 0x00 --> return value = "062", which is the NGH code that uniquely identify each game.
    # Official games does not seem to use A-F or the most significant digit.
    
    data = inputProcessor.regions['P'].data[0x108:0x10A] # = str of length 2
    assert len(data) == 2
    intData = struct.unpack('<H', data)[0] # = integer representing the value
    hexString = "00" + str(hex(intData))[2:] # string. Values: "000"-00FFFF"
    return hexString[-3:] # string. Values: "0"-"FFF" (most significant digit is cut)
