#!/usr/bin/env python
# Author: Bryan Cain
# Date: January 17, 2011
# Description: Decompresses Nintendo's romc compression used in N64 VC games.

import lz77, romchu, struct

class RomcLZ77(lz77.BaseLZ77):
	FOURMBYTE = 4194304 # 4MB rom size
	
	def __init__(self, file):
		self.file = file
		self.offset = 0
		self.uncompressed_length = self.FOURMBYTE * struct.unpack(">BBBB", self.file.read(4))[0]
		self.compression_type = self.TYPE_LZ77_10

def decompress(infile):
	# read compression type
	infile.seek(0)
	compression_type = struct.unpack(">BBBB", infile.read(4))[3] & 0x3
	
	# decompress
	infile.seek(0)
	if compression_type == 0x01: # LZ77/LZSS
		dec = RomcLZ77(infile)
		return dec.uncompress()
	elif compression_type == 0x02: # LZ77+Huffman (romchu)
		return romchu.decompress(infile)
	else:
		raise ValueError("unknown romc compression type %d" % compression_type)

if __name__ == '__main__':
	import sys, time
	
	if len(sys.argv) != 3:
		print 'Usage: %s infile outfile' % sys.argv[0]
		sys.exit(1)
	
	infile = open(sys.argv[1], 'rb')
	start = time.clock()
	output = decompress(infile)
	end = time.clock()
	print 'Time: %.2f seconds' % (end - start)
	
	outfile = open(sys.argv[2], 'wb')
	outfile.write(output)
	outfile.close()
	infile.close()

