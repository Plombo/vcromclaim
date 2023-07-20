#!/usr/bin/env python3

#Extracts VC Arcade games from a CCF archive.

import os, os.path

from configurationfile import getConfiguration
from rso import rso
from arcade_utilities import getPart, getStripes, getBitStripe

def extract_arcade_ccf(ccfArchive, outputFolder):
    config = ccfArchive.find('config')

    architecture = getConfiguration(config, "console.machine_arch")

    if architecture == 'sharrier':
        extract_SHARRIER(ccfArchive, create_rom_folder(outputFolder,'sharrier1'))
        #print_metadata(ccfArchive, config)
        return True
    else: 
        print('Found unfamiliar game. Extraction scripts need to be updated to be able to extract this game.')
#       #print_metadata(ccfArchive, config)
        return False

def extract_SHARRIER(ccfArchive, outputFolder):

    # https://github.com/mamedev/mame/blob/master/src/mame/drivers/segahang.cpp

    def convert_roadgfx(roadInput):

        # input = vc version format
        # output = original ROM format

        # this would probably be very similar for Super Hangon which use the same Arcade hardware

        outputHalfLength = int(len(roadInput) / 8)
        outputFullLength = int(outputHalfLength * 2)
        BITS_IN_BYTE = 8

        # real rom has twice as many "rows", but each "row" has 8x bytes as the VC ROM
        returnValue = bytearray(outputFullLength)

        for outputByteOffset in range(0, outputHalfLength):
            inputByteOffset = outputByteOffset * BITS_IN_BYTE
            explodedByte = roadInput[inputByteOffset : inputByteOffset+BITS_IN_BYTE]
            
            returnValue[outputByteOffset] = (
                ((explodedByte[0] & 0x1) << 7) |
                ((explodedByte[1] & 0x1) << 6) |
                ((explodedByte[2] & 0x1) << 5) |
                ((explodedByte[3] & 0x1) << 4) |
                ((explodedByte[4] & 0x1) << 3) |
                ((explodedByte[5] & 0x1) << 2) |
                ((explodedByte[6] & 0x1) << 1) |
                ((explodedByte[7] & 0x1)     )
            )

            returnValue[outputHalfLength + outputByteOffset] = (
                ((explodedByte[0] & 0x2) << 6) |
                ((explodedByte[1] & 0x2) << 5) |
                ((explodedByte[2] & 0x2) << 4) |
                ((explodedByte[3] & 0x2) << 3) |
                ((explodedByte[4] & 0x2) << 2) |
                ((explodedByte[5] & 0x2) << 1) |
                ((explodedByte[6] & 0x2)     ) |
                ((explodedByte[7] & 0x2) >> 1)
            )

        return returnValue

    moduleFile = ccfArchive.find('sharrier.rso')
    module = rso(moduleFile)

    f = open(os.path.join(outputFolder, 'sharrier.rso'), 'wb')
    moduleFile.seek(0)
    f.write(moduleFile.read())
    f.close()
    moduleFile.seek(0)

    #for export in module.getAllExports():
    #    print(" -- Export " + export)

    # The separate ROM files has been merged, we need to splice them so that MAME can load them.
    # Basically this is doing the reverse of what MAME does when loading the ROMs

    #maincpu = 68000 code
    cpu1 = get_rom_file(module, 'sharrier_rom_cpu1', 0x40000)
    save_rom_file(getStripes(getPart(cpu1,0,0x10000),[0,2]), outputFolder, 'epr-7188.ic97')
    save_rom_file(getStripes(getPart(cpu1,0,0x10000),[1,3]), outputFolder, 'epr-7184.ic84')
    save_rom_file(getStripes(getPart(cpu1,1,0x10000),[0,2]), outputFolder, 'epr-7189.ic98')
    save_rom_file(getStripes(getPart(cpu1,1,0x10000),[1,3]), outputFolder, 'epr-7185.ic85')
    save_rom_file(getStripes(getPart(cpu1,2,0x10000),[0,2]), outputFolder, 'epr-7190.ic99')
    save_rom_file(getStripes(getPart(cpu1,2,0x10000),[1,3]), outputFolder, 'epr-7186.ic86')
    save_rom_file(getStripes(getPart(cpu1,3,0x10000),[0,2]), outputFolder, 'epr-7191.ic100')
    save_rom_file(getStripes(getPart(cpu1,3,0x10000),[1,3]), outputFolder, 'epr-7187.ic87')

    #subcpu = second 68000 CPU
    cpu2 = get_rom_file(module, 'sharrier_rom_cpu2', 0x10000)
    save_rom_file(getStripes(cpu2,[0,2]), outputFolder, 'epr-7182.ic54')
    save_rom_file(getStripes(cpu2,[1,3]), outputFolder, 'epr-7183.ic67')

    #gfx1 = tiles
    # These are 3 bits per pixel. one bit is in each rom.
    # Then the hardware or emulator read from the three separate roms to build every pixel.
    # To speed things up on the Wii, the three roms has been merged into one linear rom.
    # We need to split them up again with getBitStripe
    # Lots of help from MAME source code to figure this out
    gfx1 = get_rom_file(module, 'sharrier_rom_grp1', 0x20000)
    save_rom_file(getBitStripe(gfx1, 0), outputFolder, 'epr-7196.ic31')
    save_rom_file(getBitStripe(gfx1, 1), outputFolder, 'epr-7197.ic46')
    save_rom_file(getBitStripe(gfx1, 3), outputFolder, 'epr-7198.ic60')
    #This has data, not sure what it is though
    #save_rom_file(getBitStripe(gfx1, 2), outputFolder, 'should-be-empty-but-is-not')

    #sprites
    sprites = get_rom_file(module, 'sharrier_rom_grp2', 0x100000)
    save_rom_file(getStripes(getPart(sprites,0,0x20000),[3]), outputFolder, 'epr-7230.ic36')
    save_rom_file(getStripes(getPart(sprites,0,0x20000),[2]), outputFolder, 'epr-7222.ic28')
    save_rom_file(getStripes(getPart(sprites,0,0x20000),[1]), outputFolder, 'epr-7214.ic18')
    save_rom_file(getStripes(getPart(sprites,0,0x20000),[0]), outputFolder, 'epr-7206.ic8')
    save_rom_file(getStripes(getPart(sprites,1,0x20000),[3]), outputFolder, 'epr-7229.ic35')
    save_rom_file(getStripes(getPart(sprites,1,0x20000),[2]), outputFolder, 'epr-7221.ic27')
    save_rom_file(getStripes(getPart(sprites,1,0x20000),[1]), outputFolder, 'epr-7213.ic17')
    save_rom_file(getStripes(getPart(sprites,1,0x20000),[0]), outputFolder, 'epr-7205.ic7')
    save_rom_file(getStripes(getPart(sprites,2,0x20000),[3]), outputFolder, 'epr-7228.ic34')
    save_rom_file(getStripes(getPart(sprites,2,0x20000),[2]), outputFolder, 'epr-7220.ic26')
    save_rom_file(getStripes(getPart(sprites,2,0x20000),[1]), outputFolder, 'epr-7212.ic16')
    save_rom_file(getStripes(getPart(sprites,2,0x20000),[0]), outputFolder, 'epr-7204.ic6')
    save_rom_file(getStripes(getPart(sprites,3,0x20000),[3]), outputFolder, 'epr-7227.ic33')
    save_rom_file(getStripes(getPart(sprites,3,0x20000),[2]), outputFolder, 'epr-7219.ic25')
    save_rom_file(getStripes(getPart(sprites,3,0x20000),[1]), outputFolder, 'epr-7211.ic15')
    save_rom_file(getStripes(getPart(sprites,3,0x20000),[0]), outputFolder, 'epr-7203.ic5')
    save_rom_file(getStripes(getPart(sprites,4,0x20000),[3]), outputFolder, 'epr-7226.ic32')
    save_rom_file(getStripes(getPart(sprites,4,0x20000),[2]), outputFolder, 'epr-7218.ic24')
    save_rom_file(getStripes(getPart(sprites,4,0x20000),[1]), outputFolder, 'epr-7210.ic14')
    save_rom_file(getStripes(getPart(sprites,4,0x20000),[0]), outputFolder, 'epr-7202.ic4')
    save_rom_file(getStripes(getPart(sprites,5,0x20000),[3]), outputFolder, 'epr-7225.ic31')
    save_rom_file(getStripes(getPart(sprites,5,0x20000),[2]), outputFolder, 'epr-7217.ic23')
    save_rom_file(getStripes(getPart(sprites,5,0x20000),[1]), outputFolder, 'epr-7209.ic13')
    save_rom_file(getStripes(getPart(sprites,5,0x20000),[0]), outputFolder, 'epr-7201.ic3')
    save_rom_file(getStripes(getPart(sprites,6,0x20000),[3]), outputFolder, 'epr-7224.ic30')
    save_rom_file(getStripes(getPart(sprites,6,0x20000),[2]), outputFolder, 'epr-7216.ic22')
    save_rom_file(getStripes(getPart(sprites,6,0x20000),[1]), outputFolder, 'epr-7208.ic12')
    save_rom_file(getStripes(getPart(sprites,6,0x20000),[0]), outputFolder, 'epr-7200.ic2')
    save_rom_file(getStripes(getPart(sprites,7,0x20000),[3]), outputFolder, 'epr-7223.ic29')
    save_rom_file(getStripes(getPart(sprites,7,0x20000),[2]), outputFolder, 'epr-7215.ic21')
    save_rom_file(getStripes(getPart(sprites,7,0x20000),[1]), outputFolder, 'epr-7207.ic11')
    save_rom_file(getStripes(getPart(sprites,7,0x20000),[0]), outputFolder, 'epr-7199.ic1')

    #gfx3 = road gfx - BROKEN!
    gfx3 = get_rom_file(module, 'sharrier_rom_grp3', 0x20000)
    save_rom_file(convert_roadgfx(gfx3), outputFolder, 'epr-7181.ic2')

    #soundcpu = sound CPU
    soundcpu = get_rom_file(module, 'sharrier_rom_cpu3', 0x008000)
    save_rom_file(getPart(soundcpu,0,0x004000), outputFolder, 'epr-7234.ic73')
    save_rom_file(getPart(soundcpu,1,0x004000), outputFolder, 'epr-7233.ic72')

    #pcm = Sega PCM sound data - NOTE: the two roms are stacked in reverse order vs the actual address range
    pcm = get_rom_file(module, 'sharrier_rom_pcm', 0x10000)
    save_rom_file(getPart(pcm,1,0x008000), outputFolder, 'epr-7231.ic5')
    save_rom_file(getPart(pcm,0,0x008000), outputFolder, 'epr-7232.ic6')

    #sprites:zoom = zoom table - OK
    save_rom_file(get_rom_file(module, 'sharrier_rom_prom', 0x2000), outputFolder, 'epr-6844.ic123')


#TODO: create extract_ARCHITECTURE functions for other games


#def print_metadata(ccfArchive, config):
    
    #Look for the module most specific to the game, and for exports that refers to roms

#    modules = string.split(getConfiguration(config, 'modules'))
#    for module in modules:
#        moduleFilename = module + '.rso'
#        print(' - Module ' + moduleFilename + ':')
#        moduleFile = ccfArchive.find(moduleFilename)
#        module = rso(moduleFile)
#        for export in module.getAllExports():
#            print(" -- Export " + export)

        
def create_rom_folder(parentFolder, romFolderName):
    newFolder = os.path.join(parentFolder, romFolderName)
    if not os.path.lexists(newFolder):
        os.makedirs(newFolder)
    return newFolder


def get_rom_file(inputModule, inputName, size):
    return inputModule.getExport(inputName, size)

def save_rom_file(romData, outputFolder, outputName):
    outputFile = open(os.path.join(outputFolder, outputName), 'wb')
    outputFile.write(romData)
    outputFile.close()

        











