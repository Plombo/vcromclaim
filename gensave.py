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
	assert infile.read(4) == 'VCSD'
	size1 = struct.unpack('<I', infile.read(4))[0] # size of expanded file + size of SRAM block (0x8)
	infile.read(4) # not sure what these 4 bytes do
	assert infile.read(4) == 'SRAM'
	size = struct.unpack('<I', infile.read(4))[0] # size of expanded file; equal to (size1 - 0x8)
	assert size == size1 - 0x8
	
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

