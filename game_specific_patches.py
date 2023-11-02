#!/usr/bin/env python3

import hashlib

# Dirty hacks to fix specific games

# WARNING: For legal reasons, we cannot ADD any hardcoded data that is not alreday in the ROM. That would be piracy.
# We can only delete, move, copy, convert etc data already in the ROM.
# Likewise should we not document any actual data as found in any ROM. 



def patch_mario_tennis(romByteArray):
    print('Patching Mario Tennis')

    # Game contains an extra instruction in the code with an invalid opcode.
    # The instruction causes hardware and accurate emulators to crash. 
    # This fixes that.

    romByteArray[(0x1070):(0x1070 + 0xC)] = romByteArray[(0x1070 + 0x04):(0x1070 + 0x04 + 0xC)]
    return romByteArray

def patch_specific_games(romByteArray):
    hexDigest = hashlib.sha1(romByteArray).hexdigest()
    #print(hexDigest)

    funcs = {
        '36bcbb5b9b5592d05482ac677a0c54df51b122a1': patch_mario_tennis
    }
    if hexDigest in funcs.keys():
        return funcs[hexDigest](romByteArray)
    else:
        return romByteArray
