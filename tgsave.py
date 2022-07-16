from io import BytesIO
import os

# Wii/TurboGrafx save format reverse engineered by Euan Forrester ( https://github.com/euan-forrester/ ) and JanErikGunnar

# Also with help from:
# https://blackfalcongames.net/?p=190
# http://blockos.github.io/HuDK/doc/files/include/bram-s.html
# https://www.lorenzomoretti.com/wp-content/files/chapter_0.txt
# https://github.com/asterick/TurboSharp/blob/master/Text/pcetech.txt

def bitwise_xor_bytes(a, b):
    result_int = int.from_bytes(a, byteorder="big", signed = True) ^ int.from_bytes(b, byteorder="big", signed = True)
    return result_int.to_bytes(max(len(a), len(b)), byteorder="big", signed = True)

def bitwise_not_bytes(a):
    result_int = ~int.from_bytes(a, byteorder="big", signed = True)
    return result_int.to_bytes(len(a), byteorder="big", signed = True)

def unmangle_tgsave(inputMangledFilePath, outputPlainFileFolder):

    # mangled format:
    # 4 bytes magic word "$PCE"
    # 4 bytes IV (random bytes, different for each game or save?)
    # 4 bytes purpose unknown (unused IV?)
    # 4 bytes padding, always 0
    # the rest of the file is the content of an 8 KiB BRAM, each block of 4 bytes is xored with the NOT previous unmangled (the first block being xored with the IV)
        # After demangling the 8 KiB:
        # 4 bytes magic word "HUBM"
        # 2 bytes "Pointer to the first byte after BRAM."
        #   BRAM starts at 0x8000
        #   Wii emulates an 8 KiB BRAM 0 0x2000
        #   That + endiannes = these two bytes are 0x00A0
        # ... the rest of the bram content
    # 16 unknown bytes (checksums?)

    # We need to unmangle this (remove the Wii header/footer, undo the xoring) to get a file usable in emulators.
    # It's uncertain how emulators will handle the 8 KiB BRAM.
    # All official hardware only had 2 KiB.
    # We export both the original, and a copy converted to 2 KiB.

    inputFile = open(inputMangledFilePath, 'rb')
    plain8kMemcard = BytesIO()

    magicWord = inputFile.read(4)
    assert magicWord == b'$PCE'

    # special case for first iteration
    previousMangledBlock = bitwise_not_bytes(inputFile.read(4))

    inputFile.read(4)
    padding = inputFile.read(4)
    assert padding == b'\x00\x00\x00\x00'

    plain8kMemcard = BytesIO()

    for i in range(0x0, 0x2000, 4):
        mangledBlock = inputFile.read(4)
        assert len(mangledBlock) == 4

        plainBlock = bitwise_xor_bytes(mangledBlock, bitwise_not_bytes(previousMangledBlock))

        if i == 0:
            assert plainBlock == b'HUBM'
        elif i == 4:
            assert plainBlock[0] == 0x00 and plainBlock[1] == 0xa0

        plain8kMemcard.write(plainBlock)

        previousMangledBlock = mangledBlock

    inputFile.read(16) # unknown (checksum?)
    beyondEof = inputFile.read(1)
    assert len(beyondEof) == 0

    output = open(os.path.join(outputPlainFileFolder, "8k.sav"), 'wb')
    output.write(plain8kMemcard.getvalue())
    output.close()



    # convert the 8k memcard to a 2k memcard by truncating it, and changing byte 2 and 3 from $A000 to $8800
    # the bytes are pointers to the byte after the memory card. The memory card starts at 0x8000.
    # 8800-8000 = 0800 (2 KiB)
    # A000-8000 = 2000 (8 KiB)


    plain2kMemcard = BytesIO()
    plain8kMemcard.seek(0)


    for i in range(0x0, 0x800, 2):
        block = plain8kMemcard.read(2)
        assert len(block) == 2

        if i == 4:
            assert block == b'\x00\xa0'
            plain2kMemcard.write(b'\x00\x88')
        else:
            plain2kMemcard.write(block)

    #make sure the rest of the 8 KiB memory card is empty
    for i in range(0x800, 0x2000, 4):
        emptyBlock = plain8kMemcard.read(4)
        assert emptyBlock == b'\x00\x00\x00\x00'
        

    output = open(os.path.join(outputPlainFileFolder, "2k.sav"), 'wb')
    output.write(plain2kMemcard.getvalue())
    output.close()

    print("Extracted BRAM to 2k.sav and 8k.sav")
