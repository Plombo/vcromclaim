#!/usr/bin/env python3


import arcade_utilities

# decryption converted from: https://github.com/mamedev/mame/blob/519cd8b99af8264e4117e3061b0e2391902cfc02/src/devices/bus/neogeo/prot_sma.cpp
# added reversed code for encryption

#void sma_prot_device::mslug3_decrypt_68k(uint8_t* base){
def mslug3_decrypt_68k(encrypted_rom_including_green):

    #MAP OF INPUT:
    #      0 -  c0000 = EMPTY
    #  c0000 - 100000 = "green" SMA ROM
    # 100000 - 900000 = encrypted P ROMs
    # this is how the roms are initially loaded in mame

    #MAP OF OUTPUT:
    #      0 - 900000 = the unencrypted code, in a way that can be executed.

    print("Decrypting P ROM with SMA encryption...")

    #uint16_t *rom = (uint16_t *)(base + 0x100000);
    output_everything = bytearray(encrypted_rom_including_green)
    rom = output_everything[0x100000:]

	# swap data lines on the whole ROMs
	#for (int i = 0; i < 0x800000/2; i++)
    for i in range(0, int(0x800000), 2):
        #rom[i] = bitswap<16>(rom[i],4,11,14,3,1,13,0,7,2,8,12,15,10,9,5,6);
        two_bytes_int = int.from_bytes(rom[i : i+2],'little')
        two_bytes_int = arcade_utilities.bitswap(two_bytes_int,[4,11,14,3,1,13,0,7,2,8,12,15,10,9,5,6])
        rom[i : i+2] = two_bytes_int.to_bytes(2, 'little')
		
    output_everything[0x100000:0x100000+len(rom)] = rom # 0x800000 * b'\xFF
	


	# swap address lines & relocate fixed part
	#rom = (uint16_t *)base;
    rom = output_everything

	#for (int i = 0; i < 0x0c0000/2; i++)
    for i in range (0, int(0x0c0000/2)):
        #rom[i] = rom[0x5d0000/2 + bitswap<19>(i,18,15,2,1,13,3,0,9,6,16,4,11,5,7,12,17,14,10,8)];
        swapped_address = int(0x5d0000) + arcade_utilities.bitswap(i,[18,15,2,1,13,3,0,9,6,16,4,11,5,7,12,17,14,10,8]) * 2
        rom[i*2+0] = rom[swapped_address + 0]
        rom[i*2+1] = rom[swapped_address + 1]

    # swap address lines for the banked part
	#rom = (uint16_t *)(base + 0x100000);
    output_everything = rom
    rom = output_everything[0x100000 :]

	#for (int i = 0; i < 0x800000/2; i += 0x10000/2) {
    for i in range(0, int(0x800000), int(0x10000)):
	
		#uint16_t buffer[0x10000/2];
		#memcpy(buffer, &rom[i], 0x10000);
        buffer = rom[i : i + 0x10000]

        #for (int j = 0; j < 0x10000/2; j++)
        for j in range(0, int(0x10000/2)):
            #rom[i+j] = buffer[bitswap<15>(j,2,11,0,14,6,4,13,8,9,3,10,7,5,12,1)];
            swapped_address = arcade_utilities.bitswap(j,[2,11,0,14,6,4,13,8,9,3,10,7,5,12,1]) * 2
            rom[i + j*2 : i + j*2 + 2] = buffer[swapped_address : swapped_address + 2]
	#}

    output_everything[0x100000 :] = rom
    return output_everything
#}


#void sma_prot_device::mslug3_decrypt_68k(uint8_t* base){
def mslug3_encrypt_68k(decrypted_rom_including_green):

    #MAP OF INPUT:
    #      0 - 900000 = the unencrypted code, in a way that can be executed. this is the output of mslug3_decrypt_68k and also how it was delivered as a P ROM on Wii.

    #MAP OF OUTPUT:
    #      0 -  c0000 = UNDEFINED - should be same as input, which means it is decrypted garbage and should be ignored.
    #  c0000 - 100000 = "green" SMA ROM, untouched, same input as output
    # 100000 - 900000 = encrypted actual P ROMs
    # this is how the roms are initially loaded in mame

    print("Encrypting P ROM with SMA encryption...")

    output_everything = bytearray(decrypted_rom_including_green)

    rom = output_everything[0x100000:]

    for i in range(0, int(0x800000), int(0x10000)):
        buffer = rom[i : i + 0x10000]

        for j in range(0, int(0x10000/2)):
            swapped_address = arcade_utilities.bitswap(j,[2,11,0,14,6,4,13,8,9,3,10,7,5,12,1]) * 2
            rom[i + swapped_address : i + swapped_address + 2] = buffer[j*2 : j*2 + 2]
		
    output_everything[0x100000:] = rom
	
	# swap address lines & relocate fixed part
    rom = output_everything

    for i in range (0, int(0x0c0000/2)):
        swapped_address = int(0x5d0000) + arcade_utilities.bitswap(i,[18,15,2,1,13,3,0,9,6,16,4,11,5,7,12,17,14,10,8])*2
        rom[swapped_address : swapped_address + 1] = rom[i*2 : i*2 + 1]

    output_everything = rom
    rom = output_everything[0x100000 :]


	# swap data lines on the whole ROMs
    for i in range(0, int(0x800000), 2):
        two_bytes_int = int.from_bytes(rom[i : i+2],'little')
        two_bytes_int = arcade_utilities.bitswap(two_bytes_int,[4,13,10,5,14,3,2,6,8,0,1,15,12,7,11,9])
        rom[i : i+2] = two_bytes_int.to_bytes(2, 'little')

    output_everything[0x100000:] = rom
    return output_everything
#}

