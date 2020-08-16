#!/usr/bin/env python3
# Author: Bryan Cain
# Original software (lzh8_dec 0.8) written in C by hcs
# Date: January 17, 2011
# Description: Decompresses Nintendo's N64 romc compression, type 2 (LZ77+Huffman)

'''
   LZH8 decompressor

   An implementation of LZSS, with symbols stored via two Huffman codes:
   - one for backreference lengths and literal bytes (8 bits each)
   - one for backreference displacement lengths (bits - 1)

   Layout of the compression:

   0x00:		0x40 (LZH8 identifier)
   0x01-0x03:   uncompressed size (little endian)
   0x04-0x07:   optional 32-bit size if 0x01-0x03 is 0
   followed by:

   9-bit prefix coding tree table (for literal bytes and backreference lengths)
   0x00-0x01:   Tree table size in 32-bit words, -1
   0x02-:	   Bit packed 9-bit inner nodes and leaves, stored as in Huff8
   Total size:  2 ^ (leaf count + 1)

   5-bit prefix coding tree table (for backreference displacement lengths)
   0x00:		Tree table size in 32-bit words, -1
   0x01-:	   Bit packed 5-bit inner nodes and leaves, stored as in Huff8
   Total size:  2 ^ (leaf count + 1)

   Followed by compressed data bitstream:
   1) Get a symbol from the 9-bit tree, if < 0x100 is a literal byte, repeat 1.
   2) If 1 wasn't a literal byte, symbol - 0x100 + 3 is the backreference length
   3) Get a symbol from the 5-bit tree, this is the length of the backreference
	  displacement.
   3a) If displacement length is zero, displacement is zero
   3b) If displacement length is one, displacement is one
   3c) If displacement length is > 1, displacement is next displen-1 bits,
	   with an extra 1 on the front (normalized).

   Reverse engineered by hcs.
'''

import sys, os, struct
from array import array

VERSION = "0.8"

# debug output options
SHOW_SYMBOLS	   =  0
SHOW_FREQUENCIES   =  0
SHOW_TREE		  =  0
SHOW_TABLE		 =  0

# constants
LENBITS = 9
DISPBITS = 5
LENCNT = (1 << LENBITS)
DISPCNT = (1 << DISPBITS)

# globals
input_offset = 0
bit_pool = 0 # uint8_t
bits_left = 0

# read MSB->LSB order
'''static inline uint16_t get_next_bits(
		FILE *infile,
		long * const offset_p,
		uint8_t * const bit_pool_p,
		int * const bits_left_p,
		const int bit_count)'''
def get_next_bits(infile, bit_count):
	global input_offset, bit_pool, bits_left
	
	offset_p = input_offset
	bit_pool_p = bit_pool
	bits_left_p = bits_left
	
	out_bits = 0
	num_bits_produced = 0
	while num_bits_produced < bit_count:
		if bits_left_p == 0:
			infile.seek(offset_p)
			bit_pool_p = struct.unpack("<B", infile.read(1))[0]
			bits_left_p = 8
			offset_p += 1
		
		bits_this_round = 0
		if bits_left_p > (bit_count - num_bits_produced):
			bits_this_round = bit_count - num_bits_produced
		else:
			bits_this_round = bits_left_p

		out_bits <<= bits_this_round
		out_bits |= (bit_pool_p >> (bits_left_p - bits_this_round)) & ((1 << bits_this_round) - 1)

		bits_left_p -= bits_this_round
		num_bits_produced += bits_this_round
	
	input_offset = offset_p
	bit_pool = bit_pool_p
	bits_left = bits_left_p
	
	return out_bits

# void analyze_LZH8(FILE *infile, FILE *outfile, long file_length)
def decompress(infile):
	global input_offset, bit_pool, bits_left
	input_offset = 0
	bit_pool = 0
	bits_left = 0
	
	# determine input file size
	infile.seek(0, os.SEEK_END)
	file_length = infile.tell()
	
	# read header
	infile.seek(input_offset)
	header = struct.unpack("<I", infile.read(4))[0]
	if (header & 0xFF) != 0x40: raise ValueError("not LZH8")
	uncompressed_length = header >> 8
	#if uncompressed_length == 0:
	#	uncompressed_length = struct.unpack("<I", f.read(4))[0]

	# allocate output buffer
	outbuf = array('B', b'\0' * uncompressed_length) # uint8_t*

	# allocate backreference length decode table
	length_table_bytes = (struct.unpack("<H", infile.read(2))[0] + 1) * 4 # const uint32_t
	length_decode_table_size = LENCNT * 2 # const long
	length_decode_table = array('H', b'\0' * length_decode_table_size * 2) # uint16_t* const 
	
	input_offset = infile.tell()

	# read backreference length decode table
	#if SHOW_TABLE: print("backreference length table")
	start_input_offset = input_offset-2
	i = 1
	bits_left = 0
	while (input_offset - start_input_offset) < length_table_bytes:
		if i >= length_decode_table_size:
			break
		length_decode_table[i] = get_next_bits(infile, LENBITS)
		i += 1
		#if SHOW_TABLE: print("%ld: %d" % (i-1, length_decode_table[i-1]))
	input_offset = start_input_offset + length_table_bytes
	bits_left = 0
	#if SHOW_TABLE: print("done at 0x%lx" % input_offset)

	# allocate backreference displacement length decode table
	infile.seek(input_offset)
	displen_table_bytes = (struct.unpack("<B", infile.read(1))[0] + 1) * 4 # const uint32_t
	input_offset += 1
	displen_decode_table = array('B', b'\0' * (DISPCNT * 2)) # uint8_t* const

	# read backreference displacement length decode table
	#if SHOW_TABLE: print("backreference displacement length table")
	start_input_offset = input_offset-1
	i = 1
	bits_left = 0
	while (input_offset - start_input_offset < displen_table_bytes):
		if i >= length_decode_table_size:
			break
		displen_decode_table[i] = get_next_bits(infile, DISPBITS)
		i += 1
		#if SHOW_TABLE: print("%ld: %d" % (i-1, displen_decode_table[bit_pool = 0 # uint8_ti-1]))
	input_offset = start_input_offset + displen_table_bytes
	bits_left = 0
	
	#if SHOW_TABLE: print("done at 0x%lx" % input_offset)

	bytes_decoded = 0

	# main decode loop
	while bytes_decoded < uncompressed_length:
		length_table_offset = 1

		# get next backreference length or literal byte
		while True:
			next_length_child = get_next_bits(infile, 1)
			length_node_payload = length_decode_table[length_table_offset] & 0x7F
			next_length_table_offset =  (int(length_table_offset / 2) * 2) + (length_node_payload + 1) * 2 + bool(next_length_child)
			next_length_child_isleaf = length_decode_table[length_table_offset] & (0x100 >> next_length_child)

			if next_length_child_isleaf:
				length = length_decode_table[next_length_table_offset]

				if 0x100 > length:
					# literal byte
					outbuf[bytes_decoded] = length
					bytes_decoded += 1
				else:
					# backreference
					length = (length & 0xFF) + 3
					displen_table_offset = 1
					
					# get backreference displacement length
					while True:
						next_displen_child = get_next_bits(infile, 1)
						displen_node_payload = displen_decode_table[displen_table_offset] & 0x7
						next_displen_table_offset = (int(displen_table_offset / 2) * 2) + (displen_node_payload + 1) * 2 + bool(next_displen_child)
						next_displen_child_isleaf = displen_decode_table[displen_table_offset] & (0x10 >> next_displen_child)

						if next_displen_child_isleaf:
							displen = displen_decode_table[next_displen_table_offset]
							displacement = 0

							if displen != 0:
								displacement = 1   # normalized

								# collect the bits
								#for (uint16_t i = displen-1; i > 0; i--)
								for i in range(displen-1, 0, -1):
									displacement *= 2
									next_bit = get_next_bits(infile, 1)
									
									displacement |= next_bit

							# apply backreference
							#for (long i = 0; i < length && bytes_decoded < uncompressed_length; bytes_decoded ++, i ++)
							for i in range(length):
								outbuf[bytes_decoded] = outbuf[bytes_decoded - displacement - 1]
								bytes_decoded += 1
								if bytes_decoded >= uncompressed_length: break

							break # break out of displen tree traversal loop
						else:
							assert next_displen_table_offset != displen_table_offset # stuck in a loop somehow
							displen_table_offset = next_displen_table_offset
					# end of displen tree traversal loop
				# end of if backreference !(0x100 > length)*/
				break # break out of length tree traversal loop
			else:
				assert next_length_table_offset != length_table_offset # "stuck in a loop somehow"
				length_table_offset = next_length_table_offset
		# end of length tree traversal
	# end of main decode loop
	
	return outbuf.tostring()


if __name__ == "__main__":
	if len(sys.argv) != 3:
		print("lzh8_dec %s\n" % VERSION)
		print("Usage: %s infile outfile" % sys.argv[0])
		sys.exit(1)

	# open file
	infile = open(sys.argv[1], "rb")
	outfile = open(sys.argv[2], "wb")
	
	# decompress
	print("Decompressing")
	infile.seek(0, os.SEEK_SET)
	output = decompress(infile)
	
	print("Writing to file")
	outfile.write(output)
	
	outfile.close()
	infile.close()

	sys.exit(0)


