#!/usr/bin/env python
# Author: Bryan Cain
# Date: January 17, 2011
# Description: Decompresses Nintendo's romc compression used in N64 VC games.

import lz77, romchu, struct

class RomcLZ77(lz77.BaseLZ77):

	SIZEBYTE2MULTIPLIER = 64
	SIZEBYTE1MULTIPLIER = SIZEBYTE2MULTIPLIER * 256
	SIZEBYTE0MULTIPLIER = SIZEBYTE1MULTIPLIER * 256
	
	def __init__(self, file):
		self.file = file
		self.offset = 0
		unpacked = struct.unpack(">BBBB", self.file.read(4))
		
		# How these four bytes determine the uncompressed file size is a bit uncertain.
		# The following has been tested with these games (all North American NTSC):

		# Kirby 64 ROM: 8,0,0,1
		# Mario Golf ROM: 8,0,0,1
		# Mario Golf MANUAL: 0, 100, 186, 201
		# Paper Mario ROM: 10,0,0,1

		#  Works for everything above
		self.uncompressed_length = unpacked[0] * self.SIZEBYTE0MULTIPLIER + unpacked[1] * self.SIZEBYTE1MULTIPLIER + unpacked[2] * self.SIZEBYTE2MULTIPLIER

		#  Works for Mario Golf ROM and Kirby 64 ROM
		#  Does NOT work for Mario Golf MANUAL (manual is extracted without error messages, but some of the extracted files are empty)
		#self.uncompressed_length = unpacked[0] * self.SIZEBYTE0MULTIPLIER + unpacked[1] * self.SIZEBYTE1MULTIPLIER

		#  Works for Mario Golf ROM and Kirby 64 ROM
		#  Does NOT work for Mario Golf MANUAL (fails completely to extract manual)
		#self.uncompressed_length = unpacked[0] * self.SIZEBYTE0MULTIPLIER
		
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
	import cProfile
	
	if len(sys.argv) != 3:
		print 'Usage: %s infile outfile' % sys.argv[0]
		sys.exit(1)
	
	infile = open(sys.argv[1], 'rb')
	start = time.clock()
	output = decompress(infile) # cProfile.run('output = decompress(infile)')
	end = time.clock()
	print 'Time: %.2f seconds' % (end - start)
	
	outfile = open(sys.argv[2], 'wb')
	outfile.write(output)
	outfile.close()
	infile.close()

