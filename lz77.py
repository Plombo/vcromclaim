#!/usr/bin/env python
# Author: Bryan Cain (Plombo)
# Original WiiLZ77 class by Hector Martin (marcan)
# Date: December 30, 2010
# Description: Decompresses LZ77-encoded files and compressed N64 ROMs.

import sys, os, struct
from array import array
from cStringIO import StringIO

class BaseLZ77(object):
	TYPE_LZ77_10 = 0x10
	TYPE_LZ77_11 = 0x11
	
	def uncompress(self):
		if self.compression_type == self.TYPE_LZ77_11: return self.uncompress_11()
		elif self.compression_type == self.TYPE_LZ77_10: return self.uncompress_10()
		else: raise ValueError("Unsupported compression method %d"%self.compression_type)
	
	def uncompress_10(self):
		dout = array('c', '\0' * self.uncompressed_length)
		offset = 0
 
		self.file.seek(self.offset + 0x4)
 
		while offset < self.uncompressed_length:
			flags = ord(self.file.read(1))
 
			for i in xrange(8):
				if flags & 0x80:
					info = struct.unpack(">H", self.file.read(2))[0]
					num = 3 + (info>>12)
					disp = info & 0xFFF
					ptr = offset - disp - 1
					for i in xrange(num):
						dout[offset] = dout[ptr]
						ptr += 1
						offset += 1
						if offset >= self.uncompressed_length:
							break
				else:
					dout[offset] = self.file.read(1)
					offset += 1
				flags <<= 1
				if offset >= self.uncompressed_length:
					break
 
		self.data = dout
		return self.data
	
	def uncompress_11(self):
		dout = array('c', '\0'*self.uncompressed_length)
		offset = 0
		
		self.file.seek(self.offset + 0x4)
		
		if not self.uncompressed_length:
			self.uncompressed_length = struct.unpack("<I", self.file.read(4))[0]
		
		while offset < self.uncompressed_length:
			flags = ord(self.file.read(1))
			
			for i in xrange(7, -1, -1):
				if (flags & (1<<i)) > 0:
					info = struct.unpack(">H", self.file.read(2))[0]
					ptr, num = 0, 0
					if info < 0x2000:
						if info >= 0x1000:
							info2 = struct.unpack(">H", self.file.read(2))[0]
							ptr = offset - (info2 & 0xFFF) - 1
							num = (((info & 0xFFF) << 4) | (info2 >> 12)) + 273
						else:
							info2 = ord(self.file.read(1))
							ptr = offset - (((info & 0xF) << 8) | info2) - 1
							num = ((info&0xFF0)>>4) + 17
					else:
						ptr = offset - (info & 0xFFF) - 1
						num = (info>>12) + 1
					for i in xrange(num):
						dout[offset] = dout[ptr]
						offset += 1
						ptr += 1
						if offset >= self.uncompressed_length:
							break
				else:
					dout[offset] = self.file.read(1)
					offset += 1
				
				if offset >= self.uncompressed_length:
					break
		
		self.data = dout
		return dout

class WiiLZ77(BaseLZ77):
	def __init__(self, file):
		self.file = file
		hdr = self.file.read(4)
		if hdr != "LZ77":
			self.file.seek(0)
		self.offset = self.file.tell()
		
		self.file.seek(0, os.SEEK_END)
		self.compressed_length = self.file.tell()
		self.file.seek(0, os.SEEK_SET)
		
		hdr = struct.unpack("<I", self.file.read(4))[0]
		self.uncompressed_length = hdr>>8
		self.compression_type = hdr & 0xFF
		
		#print "Compression type: 0x%02x" % self.compression_type
		#print "Decompressed size: %d" % self.uncompressed_length

def decompress(infile):
	lz77obj = WiiLZ77(infile)
	return StringIO(lz77obj.uncompress())

def romc_decode(infile):
	dec = RomcLZ77()
	return dec.uncompress()

if __name__ == '__main__':
	import time
	f = open(sys.argv[1])
	
	start = time.clock()
	unc = WiiLZ77(f)
	try:
		du = unc.uncompress_11()
	except IndexError:
		du = unc.data
	
	end = time.clock()
	print 'Time: %.2f seconds' % (end - start)
		
	#du = romc_decode(f)
	 
	f2 = open(sys.argv[2],"w")
	f2.write(''.join(du))
	f2.close()
	f.close()

