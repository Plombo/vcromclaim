#!/usr/bin/env python3
# Author: Bryan Cain (Plombo)
# Original WiiLZ77 class by Hector Martin (marcan)
# Date: December 30, 2010
# Description: Decompresses LZ77-encoded files and compressed N64 ROMs.

import sys, os, struct
from array import array
from io import BytesIO
import romchu

def decompress_lz77_lzss(file, inputOffset, outputLength):

	#print("Decompressing LZ77/LZSS")

	dout = array('B', b'\0' * outputLength)
	file.seek(inputOffset)
	outputOffset = 0

	while outputOffset < outputLength:
		flags = file.read(1)[0]

		for i in range(8):
			if flags & 0x80:
				info = struct.unpack(">H", file.read(2))[0]
				num = 3 + (info>>12)
				disp = info & 0xFFF
				ptr = outputOffset - disp - 1
				for i in range(num):
					dout[outputOffset] = dout[ptr]
					ptr += 1
					outputOffset += 1
					if outputOffset >= outputLength:
						break
			else:
				dout[outputOffset] = file.read(1)[0]
				outputOffset += 1
			flags <<= 1
			if outputOffset >= outputLength:
				break

	return dout

def decompress_lz77_11(file, inputOffset, outputLength):
	#print("Decompressing LZ77 mode 11"()

	dout = array('B', b'\0'*outputLength)

	file.seek(inputOffset)
	outputOffset = 0


	while outputOffset < outputLength:
	
		flags = file.read(1)[0]

		for i in range(7, -1, -1):
			if (flags & (1<<i)) > 0:
				info = struct.unpack(">H", file.read(2))[0]
				ptr, num = 0, 0
				if info < 0x2000:
					if info >= 0x1000:
						info2 = struct.unpack(">H", file.read(2))[0]
						ptr = outputOffset - (info2 & 0xFFF) - 1
						num = (((info & 0xFFF) << 4) | (info2 >> 12)) + 273
					else:
						info2 = file.read(1)[0]
						ptr = outputOffset - (((info & 0xF) << 8) | info2) - 1
						num = ((info&0xFF0)>>4) + 17
				else:
					ptr = outputOffset - (info & 0xFFF) - 1
					num = (info>>12) + 1
				for i in range(num):
					dout[outputOffset] = dout[ptr]
					outputOffset += 1
					ptr += 1
					if outputOffset >= outputLength:
						break
			else:
				dout[outputOffset] = file.read(1)[0]
				outputOffset += 1
			
			if outputOffset >= outputLength:
				break
	
	return dout

def decompress_romchu(file, inputOffset, outputLength):
	# LZ77+Huffman (romchu)
	return romchu.decompress(file, inputOffset, outputLength)

def decompress_n64(file):	

	file.seek(0)

	# This header has a 30 bit size of the uncompressed file, and 2 bit flag (0x1 and 0x2 being known)
	# It has reversed byte order compared to the non-n64 header.
	inputOffset = 4
	hdr = struct.unpack(">I", file.read(4))[0]
	uncompressed_length = hdr>>2
	compression_type = hdr & 0x3

	if compression_type == 0x1: return decompress_lz77_lzss(file, inputOffset, uncompressed_length)
	elif compression_type == 0x2: return decompress_romchu(file, inputOffset, uncompressed_length)
	else: raise ValueError("Unsupported compression method %d"%compression_type)

def decompress_nonN64(file):
	# This header MAY have magic word "LZ77"
	# Then it has a 24 bit size of the uncompressed file, and 8 bits fla (0x10 and 0x11 being known)
	# It has reversed byte order compared to the n64 header.

	hdr = file.read(4)
	if hdr != "LZ77":
		file.seek(0)
	lz77offset = file.tell()
	inputOffset = lz77offset + 4

	file.seek(lz77offset)

	hdr = struct.unpack("<I", file.read(4))[0]
	uncompressed_length = hdr>>8
	compression_type = hdr & 0xFF

	if compression_type == 0x11: return decompress_lz77_11(file, inputOffset, uncompressed_length)
	elif compression_type == 0x10: return decompress_lz77_lzss(file, inputOffset, uncompressed_length)
	else: raise ValueError("Unsupported compression method %d"%compression_type)


if __name__ == '__main__':
	import time
	f = open(sys.argv[1], 'rb')
	
	start = time.clock()
	if (sys.argv[2] == 'True'):
		du = decompress_n64(f)
	else:
		du = decompress_nonN64(f)
	
	end = time.clock()
	print('Time: %.2f seconds' % (end - start))
		
	f2 = open(sys.argv[2], 'wb')
	f2.write(''.join(du))
	f2.close()
	f.close()

