#!/usr/bin/env python
# Author: Bryan Cain
# Date: January 22, 2011
# Description: Converts VC Genesis saves to the .srm format used by Gens/GS.
# The save format used by Genesis VC games was reverse engineered by Bryan Cain.

import struct

# src, dest: filesystem paths
def convert(src, dest):
	infile = open(src, 'rb')
	outfile = open(dest, 'wb')
	
	# read VC header

	# first, magic word VCSD
	assert infile.read(4) == 'VCSD'

	# now a header that may be 8-9 bytes, maybe more or less?
	# At least north american Monster World IV has 9 bytes header.
	
	#first four bytes of that header contains an integer which is
	# the size of expanded file + headerSize of this header below
	totalSize = struct.unpack('<I', infile.read(4))[0] 
	headSize = 4
	# remaining bytes of the header is unknown
	
	# search for 'SRAM' magic word.
	while infile.read(4) != 'SRAM' and headSize < totalSize:
		infile.seek(-3,1) #step 3 bytes back and look again
		headSize = headSize + 1

	# sanity check. if this is not true then SRAM was not found in the file.
	assert headSize < totalSize

	size = struct.unpack('<I', infile.read(4))[0] # size of expanded file; equal to (totalSize - headSize)
	assert size == (totalSize - headSize)
	
	while outfile.tell() < size:
		data = infile.read(512)
		intdata = struct.unpack('>512B', data)
		outfile.write(struct.pack('>512H', *intdata))
	
	outfile.close()
	infile.close()

if __name__ == '__main__':
	import sys
	if len(sys.argv) != 3:
		sys.stderr.write('Usage: %s infile outfile\n' % sys.argv[0])
		sys.exit(1)
	convert(sys.argv[1], sys.argv[2])
	print 'Done'

