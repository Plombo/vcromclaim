# Decompress ACM files, used by some Neo Geo games on the Virtual Console.
# Reverse engineered by JanErikGunnar using Dolphin.

# The files are used to compress C ROMs for Neo Geo games.
# The Virtual Console emulator decompress on demand, because the C ROMs are too large to fit in the Wii RAM.
# Hence, the algorithm is very simple.
# This implementation however, is not very optimized :)

# 0x0: magic word ACM, followed by null padding.
# 0x10: Number of blocks in block table, e.g. 0x0000 0400.
#           The output file size will be this value * 0x1 0000.
# 0x14: Always 0001 followed by null padding?
# 0x20: Translation table
#          Fixed length
#          For 0 .. 0xFF:
#           0x00: either 0 or 1
#           0x01:   If value at 0x00 is 0x00, this is the output byte.
#                   if value at 0x00 is 0x01, this is another entry in this table. Recursively replace the byte with values from that entry instead.
#           0x02: similar to 0x00
#           0x03: similar to 0x01
# 0x420: Block table
#          For each block:
#           0x0: (4 bytes) address of block start (4 bytes), from top of file
#           0x4: (2 bytes) length of compressed data in block (from start of block)
#           0x6: (2 bytes) always 0xFFFF
# [number of blocks in block table * 8 + 0x420]: Blocks of data
#          For each block (starting at positions specified in block table):
#           [0 - length of compressed data]: First the compressed data (has the length specified in block table)
#           [length of compressed data - ceil(length of compressed data/8)]: Flags determining whether trans
#               Each byte in the first block has a corresponding bit in the second.
#               If the bit in the second block is 1, the byte in the first block should be replaced with two or more values as defined by the translation table.
#               If the bit is the second block is 0, the byte in the first block should be used as is.


# Once decompressed, the data revealed is still different from the original roms, maybe to reduce the load required of the Wii CPU to read the sprites?
# We have to convert it back to the Neo Geo sprite data structure.

# Very useful:
# https://wiki.neogeodev.org/index.php?title=Sprite_graphics_format



import struct


def decompressAcm(inputAcmStr):

    def translateValue(byteValue):
        translationtableEntryPos = TRANSLATION_TABLE_POS + (byteValue << 2)
        char0 = inputArray[translationtableEntryPos+0]
        char1 = inputArray[translationtableEntryPos+1]
        char2 = inputArray[translationtableEntryPos+2]
        char3 = inputArray[translationtableEntryPos+3]

        if char0 == 0x1:
            retVal = translateValue(char1)
        elif char0 == 0x0:
            retVal = bytearray([char1])
        else:
            raise ValueError(char0)

        if char2 == 0x1:
            retVal.extend(translateValue(char3))
        elif char2 == 0x0:
            retVal.append(char3)
        else:
            raise ValueError(char2)

        return retVal

    print "Decompressing ACM (this will take some time)..."

    #assert(inputAcmStr[0:4] == 'ACM\x00')

    inputArray = bytearray(inputAcmStr)
    outputPosition = 0

    blockCount = struct.unpack('>I', str(inputArray[0x10:0x14]))[0]

    outputArray = bytearray(blockCount * 0x10000)
    TRANSLATION_TABLE_POS = 0x20
    BLOCK_TABLE_POS = 0x420
    BLOCK_TABLE_ENTRY_SIZE = 0x8


    #perform translations all at once for faster processing of the compressed data
    translations = [translateValue(i) for i in xrange(0x00,0x100)]

    for blockIndex in xrange(0, blockCount):
        assert blockIndex < blockCount
        
        blockTableEntryPos = BLOCK_TABLE_POS + BLOCK_TABLE_ENTRY_SIZE*blockIndex
        blockTableEntry = struct.unpack('>IHxx', str(inputArray[blockTableEntryPos:blockTableEntryPos+8]))
        compressedDataStart = blockTableEntry[0]
        compressedDataLength = blockTableEntry[1]
        flagStart = compressedDataStart + compressedDataLength

        for compressedDataIndex in xrange(0, compressedDataLength):
            
            # read the flag after the compressed data
            useTranslation = (
                (
                    (
                        (
                            (
                                inputArray[flagStart + (compressedDataIndex / 8)]
                            ) >> (7- (compressedDataIndex % 8))
                        ) & 0x1
                    )
                )
            ) == 0x1

            if useTranslation:
                translatedBytes = translations[inputArray[compressedDataStart + compressedDataIndex]]
                for translatedByteIndex in xrange(0, len(translatedBytes)):
                    outputArray[outputPosition] = translatedBytes[translatedByteIndex]
                    outputPosition = outputPosition + 1
            else:
                outputArray[outputPosition] = inputArray[compressedDataStart + compressedDataIndex]
                outputPosition = outputPosition + 1
           
            
        #print "Exported block %s" % blockIndex


    assert outputPosition == blockCount * 0x10000

    return convertToRegularSpriteData(outputArray)


        
# Takes the CROM data that was decompressed from "ACM", and gives it in the normal Neo Geo format. (bitplanes 0,1,2,3 in one string, in that order)
def convertToRegularSpriteData(inputByteArray):
    assert (len(inputByteArray) % 0x80) == 0

    outputByteArray = bytearray('\x00' * len(inputByteArray))

    for spritePosition in xrange(0, len(inputByteArray), 0x80):
        # Each sprite is 16x16 = 256 pixels
        # Each sprite is stored as 128 bytes, both in input and output
        # Each pixel is always 4 bits (16 different colours).
        # In input (the decompressed ACM file), each byte represents two pixels.
        # In output (that matches the memory layout of the NG), each byte represents 1 bit = 1/4 of 8 pixels.
        #   Note that the output file then needs to be split into C1,C2,C3... files, as all other VC NG games
        
        # read four bytes from the input file, convert them to four bytes in the output file.

        for inputIndex in xrange (0x00, 0x80, 0x04):

            # Read 8 pixels from 4 bytes. The & operation is not needed, but below we only use the four last bits.
            ip0 = ((inputByteArray[spritePosition + inputIndex + 0]) >> 4) # & 0x0F = 00001111
            ip1 = ((inputByteArray[spritePosition + inputIndex + 0]) >> 0) # & 0x0F
            ip2 = ((inputByteArray[spritePosition + inputIndex + 1]) >> 4) # & 0x0F
            ip3 = ((inputByteArray[spritePosition + inputIndex + 1]) >> 0) # & 0x0F
            ip4 = ((inputByteArray[spritePosition + inputIndex + 2]) >> 4) # & 0x0F
            ip5 = ((inputByteArray[spritePosition + inputIndex + 2]) >> 0) # & 0x0F
            ip6 = ((inputByteArray[spritePosition + inputIndex + 3]) >> 4) # & 0x0F
            ip7 = ((inputByteArray[spritePosition + inputIndex + 3]) >> 0) # & 0x0F


            # Convert the bits to the bytes in the output format.

            # 0 everything except bitplane 0 for all 8 pixels, store in byte 0
            ob0 = (
                ((ip0 & 0x1) << 7) |
                ((ip1 & 0x1) << 6) |
                ((ip2 & 0x1) << 5) |
                ((ip3 & 0x1) << 4) |
                ((ip4 & 0x1) << 3) |
                ((ip5 & 0x1) << 2) |
                ((ip6 & 0x1) << 1) |
                ((ip7 & 0x1)     )
            )

            # 0 everything except bitplane 1 for all 8 pixels, store in byte 1
            ob1 = (
                ((ip0 & 0x2) << 6) |
                ((ip1 & 0x2) << 5) |
                ((ip2 & 0x2) << 4) |
                ((ip3 & 0x2) << 3) |
                ((ip4 & 0x2) << 2) |
                ((ip5 & 0x2) << 1) |
                ((ip6 & 0x2)     ) |
                ((ip7 & 0x2) >> 1)
            )
            
            # 0 everything except bitplane 2 for all 8 pixels, store in byte 2
            ob2 = (
                ((ip0 & 0x4) << 5) |
                ((ip1 & 0x4) << 4) |
                ((ip2 & 0x4) << 3) |
                ((ip3 & 0x4) << 2) |
                ((ip4 & 0x4) << 1) |
                ((ip5 & 0x4)     ) |
                ((ip6 & 0x4) >> 1) |
                ((ip7 & 0x4) >> 2)
            )

            # 0 everything except bitplane 3 for all 8 pixels, store in byte 3
            ob3 = (
                ((ip0 & 0x8) << 4) |
                ((ip1 & 0x8) << 3) |
                ((ip2 & 0x8) << 2) |
                ((ip3 & 0x8) << 1) |
                ((ip4 & 0x8)     ) |
                ((ip5 & 0x8) >> 1) |
                ((ip6 & 0x8) >> 2) |
                ((ip7 & 0x8) >> 3)
            )

            # ACTUAL row within the sprite:
            row = (inputIndex >> 3) # 0-F
            #rowWithinBlock = row % 0x8
            
            #outputIndex = prependrows * 0x4 + rowWithinBlock * 0x4 + 0
            if (inputIndex % 0x8 == 0): # whether the four pixels is in the left half of the sprite or not
                #outputIndex = 2*0x8*0x4 + row * 0x4 + 0
                outputIndex = 0x40 + row * 0x4
            else:
                outputIndex = row * 0x4

            outputByteArray[spritePosition + outputIndex + 0] = ob0
            outputByteArray[spritePosition + outputIndex + 1] = ob1
            outputByteArray[spritePosition + outputIndex + 2] = ob2
            outputByteArray[spritePosition + outputIndex + 3] = ob3

    return str(outputByteArray)