#!/usr/bin/env python

import struct, os

HEADER_LENGTH = 64
MEGABYTE = 1024*1024
KILOBYTE = 1024
NEOGEO_BIOS_LENGTH = 128*KILOBYTE

#invaluable source: https://github.com/mamedev/mame/blob/master/src/mame/drivers/neogeo.cpp



# inputFile must be a game.bin file, which is NOT compressed or encrypted.
# wiiGameId is the game Id (8 character string). Hopefully once more games have been analyzed this can be replaced by something else - config.bin? using the header?
# outputFolder should exist and be empty.
# returns True if the file was understood.
def convert_neogeo(inputFile, wiiGameId, outputFolder):

    supportedGames = {
        '45414f45': convert_kotm,
        '45415245': convert_turfmast
    }

    if supportedGames.has_key(wiiGameId):
        supportedGames[wiiGameId](inputFile, outputFolder)
        return True
    else:
        return False


def convert_kotm(inputFile, outputFolder):
    
    # mame wants 128kb file for p2, but the second half is just 0xFF
    # not sure whether this should be kotm (arcade version) or kotmh (Home version).
    # only diff is in name and content of p1/hp1, but the one from Wii has different CRC than both of them.
    process_file(inputFile, [ \
        header_region(), \
        game_file_region(512*KILOBYTE, True, "p1"), \
        game_file_region(64*KILOBYTE, True, "p2"), \
        game_file_region(128*KILOBYTE, False, "m1"), \
        game_file_region(1*MEGABYTE, False, "v1"), \
        game_file_region(1*MEGABYTE, False, "v2"), \
        game_file_region(128*KILOBYTE, False, "s1"), \
        game_merged_bitplaine_file_region(2*MEGABYTE, ["c1", "c2"]), \
        game_merged_bitplaine_file_region(2*MEGABYTE, ["c3", "c4"]), \
        bios_file_region() \
        ], outputFolder, "kotm", "016")

def convert_turfmast(inputFile, outputFolder):
    process_file(inputFile, [ \
        header_region(), \
        game_reverse_banked_file_region(2*MEGABYTE, 2, True, False, "p1"), \
        game_file_region(128*KILOBYTE, False, "m1"), \
        game_file_region(2*MEGABYTE, False, "v1"), \
        game_file_region(2*MEGABYTE, False, "v2"), \
        game_file_region(2*MEGABYTE, False, "v3"), \
        game_file_region(2*MEGABYTE, False, "v4"), \
        game_file_region(128*KILOBYTE, False, "s1"), \
        game_merged_bitplaine_file_region(8*MEGABYTE, ["c1", "c2"]), \
        bios_file_region() \
        ], outputFolder, "turfmast", "200")


class region(object):
    def __init__(self, length):
        self.length = length


class ignoreable_region(region):
    def __init__(self, length):
        super(ignoreable_region, self).__init__(length)
    def process_region(self, inputFile, position, outputFolder, mameGameShortName, ngh):
        pass


class header_region(ignoreable_region):
    def __init__(self):
        super(ignoreable_region, self).__init__(HEADER_LENGTH)

class file_region(region):

    # length = length of the region in bytes
    # swap = whether the bytes should be swapped (1234--> 2143)
    # sharedFile = if false, output file should be named "<NGH>-<name>.<name>". if true, will be named whatever name is.
    # reversedBankCount: 1 = region is copied as is, 2 or more = the total area is divided into this number of banks, which are then written in reverse order to the output file.
    def __init__(self, length, reversedBankCount, swap, sharedFile, names):
        super(file_region, self).__init__(length)
        self.swap = swap
        self.sharedFile = sharedFile
        self.names = names
        self.reversedBankCount = reversedBankCount
    def process_region(self, inputFile, position, outputFolder, mameGameShortName, ngh):

        outputFiles = [None] * len(self.names)
        i = 0
        for name in self.names:
            if self.sharedFile:
                folderPath = os.path.join(outputFolder, "bios")
                filePath = os.path.join(outputFolder, "bios", name)
            else:
                folderPath = os.path.join(outputFolder, mameGameShortName)
                filePath = os.path.join(outputFolder, mameGameShortName, ngh + "-" + name + "." + name)

            if not os.path.lexists(folderPath):
                os.makedirs(folderPath)

            outputFiles[i] = open(filePath, 'wb')
            i += 1

        if len(self.names) == 4:
            outputFile0 = outputFiles[0]
            outputFile1 = outputFiles[1]
            outputFile2 = outputFiles[2]
            outputFile3 = outputFiles[3]
        elif len(self.names) == 2:
            outputFile0 = outputFiles[0]
            outputFile1 = outputFiles[1]
            outputFile2 = outputFiles[0]
            outputFile3 = outputFiles[1]
        elif len(self.names) == 1:
            outputFile0 = outputFiles[0]
            outputFile1 = outputFiles[0]
            outputFile2 = outputFiles[0]
            outputFile3 = outputFiles[0]
        else:
            raise ValueError



        # for loop to handle bankswapped roms
        # other roms will just do one iteration
        bankLength = self.length / self.reversedBankCount
        for i in xrange(self.reversedBankCount-1, -1, -1):

            inputFile.seek(position + i*bankLength)
            fileData = inputFile.read(bankLength)
            assert len(fileData) == bankLength # make sure not trying to read past the file
            
            #Do byte swapping if needed
            if self.swap:
                # 1234 --> 2143
                intdata = struct.unpack('>' + str(bankLength / 2) + 'H', fileData)
                fileData = struct.pack('<' + str(bankLength / 2) + 'H', *intdata)
            else:
                fileData

            #on real hardware, the CROMs are basically raid striped.
            #4xCROMS (c1-4): byte 0,4,8,... on C1, byte 1,5,9,... on C2, byte 2,6,10,... on C3, byte 3,7,11 on C4...
            #2xCROMS (c1-4): byte 0,1,4,5,8,9... on C1, byte 2,3,6,7,10,11,... on C2
            for j in xrange(0, len(fileData), 4):
                outputFile0.write(fileData[j+0])
                outputFile1.write(fileData[j+1])
                outputFile2.write(fileData[j+2])
                outputFile3.write(fileData[j+3])

        for outputFile in outputFiles:
            outputFile.close()



#Used where the actual ROM file is e.g. 2MB and called P1, but the VC version stores the second half first, then the first half.
#NeoGeo has a max size of P1 of 1024 so this might be the case for all games with P1 of more than 1024MB.
class game_reverse_banked_file_region(file_region):
    def __init__(self, length, reversedBankCount, swap, sharedFile, name):
        super(game_reverse_banked_file_region, self).__init__(length, reversedBankCount, swap, False, [name])
        
#Regular file, such as VROM
class game_file_region(file_region):
    def __init__(self, length, swap, name):
        super(game_file_region, self).__init__(length, 1, swap, False, [name])
    
#BIOS file
class bios_file_region(file_region):
    def __init__(self):
        super(bios_file_region, self).__init__(NEOGEO_BIOS_LENGTH, 1, True, True, ["bios.bin"])



class game_merged_bitplaine_file_region(file_region):
    def __init__(self, length, names):
        super(game_merged_bitplaine_file_region, self).__init__(length, 1, False, False, names)





def process_file(inputFile, regions, outputFolder, mameGameShortName, ngh):

    position = 0

    for region in regions:
        region.process_region(inputFile, position, outputFolder, mameGameShortName, ngh)
        position += region.length

    #should be at end of file, this should return 0-length string
    inputFile.seek(position)
    fileData = inputFile.read(1)
    assert len(fileData) == 0 # make sure no missed data in file


