#!/usr/bin/env python3

#Metal Slug 4 has some weird byteswapping not seen elsewhere, maybe related to SMC encryption or something.


def swap_8_byte_pairs(input_rom):
    value = 8

    output_rom = input_rom

    size = len(input_rom)

    buffer = bytearray(value)

    for h in range(0, int(size), int(value)):

        buffer[0:value] = output_rom[h:h+value]

        for i in range(0, int(value), int(value/2)):

            swapInputOffset = i ^ int(value/2)

            for j in range(0, int(value/2)):
                output_rom[h + i + j] = buffer[swapInputOffset + j]

    return output_rom
