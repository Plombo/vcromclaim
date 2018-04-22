#!/usr/bin/env python

import struct, os

HEADER_LENGTH = 64
KILOBYTE = 1024

#invaluable source: https://github.com/mamedev/mame/blob/master/src/mame/drivers/neogeo.cpp



# inputFile must be a game.bin file, which is NOT compressed or encrypted.
# wiiGameId is the game Id (8 character string). Hopefully once more games have been analyzed this can be replaced by something else - config.bin? using the header?
# outputFolder should exist and be empty.
# returns True if the file was understood.
def convert_neogeo(inputFile, wiiGameId, outputFolder):

    supportedGames = {
        '45414345': (convert_maglordh, "maglordh", "005"),
        '45414f45': (convert_kotmh, "kotmh", "016"),
        '45415245': (convert_turfmast, "turfmast", "200")
    }

    if supportedGames.has_key(wiiGameId):
        func = supportedGames[wiiGameId][0]
        mameShortName = supportedGames[wiiGameId][1]
        ngh = supportedGames[wiiGameId][2]
        func(input_processor(inputFile), output_processor(outputFolder, mameShortName, ngh))
        return True
    else:
        return False


def convert_maglordh(input, output):
    
    # maglordh: CRC of all files match
    # maglord: CRC of all files match except p1

    output.createFile("p1.p1", byteSwap(input.getNextRegion(512)))
    
    output.createFile("m1.m1",
        input.getRegion(512+0*64, 64)
        + input.getRegion(512+2*64, 64) # padding
        + input.getRegion(512+1*64, 64)
        + input.getRegion(512+2*64, 64)) # padding

    output.createFile("v11.v11", input.getNextRegion(512))
    output.createFile("v21.v21", input.getNextRegion(512))
    output.createFile("v22.v22", input.getNextRegion(512))

    output.createFile("s1.s1", input.getNextRegion(128))

    region = input.getNextRegion(1024)
    output.createFile("c1.c1", getStripes(region,[0,2]))
    output.createFile("c2.c2", getStripes(region,[1,3]))

    region = input.getNextRegion(1024)
    output.createFile("c3.c3", getStripes(region,[0,2]))
    output.createFile("c4.c4", getStripes(region,[1,3]))

    region = input.getNextRegion(1024)
    output.createFile("c5.c5", getStripes(region,[0,2]))
    output.createFile("c6.c6", getStripes(region,[1,3]))

    output.createFile("bios.bin", byteSwap(input.getNextRegion(128)), shared = True)
    

def convert_kotmh(input, output):

    #Not sure if this is actually kotm (MVS) or kotmh (AES) version.
    #kotm: CRC of all files except P1 match
    #kotmh: CRC of all files except P1 match

    output.createFile("hp1.p1", byteSwap(input.getNextRegion(512)))
    output.createFile("p2.p2", pad(byteSwap(input.getNextRegion(64)),128))
    
    output.createFile("m1.m1", input.getNextRegion(128))

    output.createFile("v1.v1", input.getNextRegion(1024))
    output.createFile("v2.v2", input.getNextRegion(1024))

    output.createFile("s1.s1", input.getNextRegion(128))

    region = input.getNextRegion(2048)
    output.createFile("c1.c1", getStripes(region,[0,2]))
    output.createFile("c2.c2", getStripes(region,[1,3]))

    region = input.getNextRegion(2048)
    output.createFile("c3.c3", getStripes(region,[0,2]))
    output.createFile("c4.c4", getStripes(region,[1,3]))

    output.createFile("bios.bin", byteSwap(input.getNextRegion(128)), shared = True)

   


def convert_turfmast(input, output):

    # Same ROM for MVS/AES
    # CRC is incorrect for v4, otherwise all CRCs match

    # banks are in reverse order
    output.createFile("p1.p1", byteSwap(
        input.getRegion(1024, 1024)
        + input.getRegion(0, 1024)))
    
    output.createFile("m1.m1", input.getRegion(2*1024, 128))

    output.createFile("v1.v1", input.getNextRegion(2048))
    output.createFile("v2.v2", input.getNextRegion(2048))
    output.createFile("v3.v3", input.getNextRegion(2048))
    output.createFile("v4.v4", input.getNextRegion(2048))

    output.createFile("s1.s1", input.getNextRegion(128))

    region = input.getNextRegion(8*1024)
    output.createFile("c1.c1", getStripes(region,[0,2]))
    output.createFile("c2.c2", getStripes(region,[1,3]))

    output.createFile("bios.bin", byteSwap(input.getNextRegion(128)), shared = True)





## input/output processors

class input_processor(object):
    def __init__(self, inputFile):
        self.inputFile = inputFile
        self.lastPosition = HEADER_LENGTH

    def getActualRegion(self, actualStartPosition, actualLength):
        self.inputFile.seek(actualStartPosition)
        regionData = self.inputFile.read(actualLength)
        assert len(regionData) == actualLength
        self.lastPosition = actualStartPosition + actualLength
        return regionData

    # position should NOT include the header offset (64 byte for all files)
    def getRegion(self, startPositionInKilobytes, lengthInKilobytes):
        return self.getActualRegion(HEADER_LENGTH + startPositionInKilobytes * 1024, lengthInKilobytes * KILOBYTE)

    def getNextRegion(self, lengthInKilobytes):
        return self.getActualRegion(self.lastPosition, lengthInKilobytes * KILOBYTE)


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



#stripes = [0] = get byte 0, 4, 8 etc
#stripes = [0,1] = get byte 0,1,4,5,8,9 etc
#stripes = [0,2] = get byte 0,2,4,6,8,10 etc
#stripes = [1,3] = get byte 1,3,5,7,9,11 etc
def getStripes(fileData, stripes):
    retVal = ''
    for i in xrange(0, len(fileData), 4):
        for j in stripes:
            retVal += fileData[i+j]
    return retVal


def byteSwap(fileData):
    intdata = struct.unpack('>' + str(len(fileData)/2) + 'H', fileData)
    return struct.pack('<' + str(len(fileData)/2) + 'H', *intdata)


def pad(fileData, totalLengthInKilobytes):
    actualTotalLength = totalLengthInKilobytes * KILOBYTE
    assert actualTotalLength >= len(fileData)
    return fileData + '\xFF'*(actualTotalLength-len(fileData))







