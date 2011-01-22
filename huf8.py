#!/usr/bin/env python
# Author: Bryan Cain (translated to Python from the "puff8" program by hcs, written in C)
# Date: January 17, 2011
# Description: Decompresses Nintendo's Huf8 compression used in Virtual Console games.

import os, struct
from array import array

def decompress(infile, outfile):
	infile.seek(0, os.SEEK_END)
	file_length = infile.tell()
	infile.seek(0, os.SEEK_SET)

	# read header
	magic_declength, symbol_count = struct.unpack('<IB', infile.read(5))
	if (magic_declength & 0xFF) != 0x28:
		raise ValueError("not 8-bit Huffman")
	decoded_length = magic_declength >> 8
	symbol_count += 1

	# read decode table
	decode_table_size = symbol_count * 2 - 1
	decode_table = array('B', infile.read(decode_table_size))
	
	'''
	print "encoded size = %ld bytes (%d header + %ld body)" % (
			file_length, 5 + decode_table_size,
			file_length - (5 + decode_table_size))
	print "decoded size = %ld bytes" % decoded_length
	'''

	# decode
	bits = 0
	bits_left = 0
	table_offset = 0
	bytes_decoded = 0

	while bytes_decoded < decoded_length:
		if bits_left == 0:
			bits = struct.unpack("<I", infile.read(4))[0]
			bits_left = 32

		current_bit = ((bits & 0x80000000) != 0)
		next_offset = (((table_offset + 1) / 2 * 2) + 1 +
			(decode_table[table_offset] & 0x3f) * 2 +
			current_bit)

		if next_offset >= decode_table_size:
			raise ValueError("reading past end of decode table")

		if ((not current_bit and (decode_table[table_offset] & 0x80)) or
			(    current_bit and (decode_table[table_offset] & 0x40))):
			outfile.write(chr(decode_table[next_offset]))
			bytes_decoded += 1
			# print "%02x" % decode_table[next_offset]
			next_offset = 0
		
		if next_offset == table_offset:
			raise ValueError("infinite loop in Huf8 decompression")
		table_offset = next_offset
		bits_left -= 1
		bits <<= 1

if __name__ == "__main__":
	import sys
	if len(sys.argv) != 3:
		sys.stderr.write("Usage: %s infile outfile\n" % sys.argv[0])
	
	infile = open(sys.argv[1], "rb")
	outfile = open(sys.argv[2], "wb")
	
	decompress(infile, outfile)
	outfile.close()

