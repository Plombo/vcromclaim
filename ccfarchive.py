#!/usr/bin/env python
# Author: Bryan Cain (Plombo)
# Date: December 27, 2010
# Description: Reads Wii CCF archives, which contain Genesis and Master System ROMs.

import struct
import zlib
from cStringIO import StringIO

class CCFArchive(object):
	# archive: a file-like object containing the CCF archive, OR the path to a CCF archive
	def __init__(self, archive):
		if type(archive) == type(''):
			self.file = open(archive, 'rb')
		else:
			self.file = archive
		self.files = []
		self.readheader()
	
	def readheader(self):
		magic, zeroes1, rootnode_offset, numfiles, zeroes2 = struct.unpack('<4s12sII8s', self.file.read(32))
		assert magic == 'CCF\0'
		assert zeroes1 == 12 * '\0'
		assert rootnode_offset == 0x20
		assert zeroes2 == 8 * '\0'
		for i in range(numfiles):
			fd = FileDescriptor(self.file)
			self.files.append(fd)
	
	def hasfile(self, path):
		for f in self.files:
			if f.name == path: return True
		return False
	
	def getfile(self, path):
		assert self.hasfile(path)
		fd = None
		for f in self.files:
			if f.name == path: fd = f
		return self.getfile2(fd)
	
	def getfile2(self, fd):
		self.file.seek(fd.data_offset * 32)
		string = self.file.read(fd.size)
		if fd.compressed:
			string = zlib.decompress(string)
			assert len(string) == fd.decompressed_size
		return StringIO(string)
	
	# returns the requested file, even if the name is cut off inside the archive
	def find(self, name):
		for fd in self.files:
			if name.startswith(fd.name.rstrip()) or fd.name.startswith(name.rstrip()): return self.getfile2(fd)
		return None

class FileDescriptor(object):
	# f: a file-like object of a CCF file at the position of this file descriptor
	def __init__(self, f):
		self.name, self.data_offset, self.size, self.decompressed_size = struct.unpack('<20sIII', f.read(32))
		self.name = self.name[0:self.name.find('\0')]
		self.compressed = (self.size != self.decompressed_size)

if __name__ == '__main__':
	import os
	arc = CCFArchive(os.getenv('HOME') + '/wii/spinball/data.ccf')
	arc.getfile('SonicSpinball_USA.S')
	

