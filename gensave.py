#!/usr/bin/env python3
# Author: Bryan Cain
# Date: January 22, 2011
# Description: Converts VC Genesis and VC Master System saves to the .srm/.ssm format used by Gens/GS/Kega Fusion.
# The save format used by Genesis VC games was reverse engineered by Bryan Cain.

import struct

# src, dest: filesystem paths
# genesis:
#  True if the output file is a .srm file for a Genesis game.
#  False if the output file is a .ssm file for a Master System game.
def convert(src, dest, genesis):
	infile = open(src, 'rb')
	outfile = open(dest, 'wb')

	SIZE_SIZE = 4
	COMPOUND_DATA_MAGIC = b'compound data\x00\x00\x00'
	COMPOUND_DATA_MAGIC_SIZE = len(COMPOUND_DATA_MAGIC)
	SRAM_MAGIC = b'SRAM'
	SRAM_MAGIC_SIZE = len(SRAM_MAGIC)

	# MW4 = monster world IV, genesis NTSC
	# PS = phantasy star, sms NTSC
	# Those two games are confirmed working in GENS and Kega Fusion (latest versions as of july 2018).
	# the original reverse engineering was probably of some other games, which seem to have a somewhat different format.
	# i've tried to preserve the original functionality but have not been able to test it so I might have broken it.

	# read "VCSD"
	assert infile.read(4) == b'VCSD'

	# read four bytes = size
	totalSize = struct.unpack('<I', infile.read(SIZE_SIZE))[0]
	assert totalSize > 0

	# read 4 or 5 bytes: 5 bytes 0x12C0A21004 for MW4, 5 bytes 0x0A53124504 for PS, 4 bytes for some games (which?)
	headSize = 4
	infile.seek(4,1)

	# then skip bytes until we get to "SRAM" magic word
	while infile.read(SRAM_MAGIC_SIZE) != SRAM_MAGIC and headSize < totalSize:
		infile.seek(-3,1) #step 3 bytes back and look again
		headSize = headSize + 1
	assert headSize == 4 or headSize == 5

	# read four bytes = size
	innerSize = struct.unpack('<I', infile.read(SIZE_SIZE))[0]
	assert innerSize == totalSize - headSize - SIZE_SIZE

	# is the next bytes a "compound data" block, or the actual SRAM?
	if (infile.read(COMPOUND_DATA_MAGIC_SIZE) == COMPOUND_DATA_MAGIC):
		#it's compound (e.g. MW4 and PS)
		
		# look for next SRAM block (should follow just after)
		assert infile.read(SRAM_MAGIC_SIZE) == SRAM_MAGIC

		# get the size
		innerInnerSize = struct.unpack('<I', infile.read(SIZE_SIZE))[0]
		assert innerInnerSize == innerSize - SIZE_SIZE - COMPOUND_DATA_MAGIC_SIZE - SRAM_MAGIC_SIZE

		# get the even inner inner size (shuld be same as before but -4)
		actualSramSize = struct.unpack('<I', infile.read(SIZE_SIZE))[0]
		assert actualSramSize == innerInnerSize - SIZE_SIZE
	else:
		# else, the last size was refering to the actual sram data.
		# UNTESTED
		infile.seek(-COMPOUND_DATA_MAGIC_SIZE, 1)
		actualSramSize = innerSize

	assert actualSramSize % 512 == 0

	# get the data
	sramData = infile.read(actualSramSize)
	intData = struct.unpack('>' + str(actualSramSize) + 'B', sramData)

	if (genesis):
		outType = 'H'
	else:
		outType = 'B'

	outfile.write(struct.pack('>' + str(actualSramSize) + outType, *intData))
	
	outfile.close()
	infile.close()

if __name__ == '__main__':
	import sys
	if len(sys.argv) != 3:
		sys.stderr.write('Usage: %s infile outfile\n' % sys.argv[0])
		sys.exit(1)
	convert(sys.argv[1], sys.argv[2], True)
	print('Done')

