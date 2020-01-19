#!/usr/bin/env python
# Author: Bryan Cain (Plombo)
# Date: December 27, 2010
# Description: Reads Wii U8 archives.

import os, struct, posixpath
from cStringIO import StringIO
import lz77, huf8, lzh8
import re

class U8Archive(object):
	# archive can be a string (filesystem path) or file-like object
	def __init__(self, archive):
		if type(archive) == str:
			#print archive
			self.file = open(archive, 'rb')
		else:
			self.file = archive
		assert self.file
		self.files = []
		self.readheader()
	
	def readheader(self):
		magic, rootnode_offset, header_size, data_offset = tuple(struct.unpack('>IIII', self.file.read(16)))
		assert magic == 0x55aa382d
		assert rootnode_offset == 0x20
		assert self.file.read(16) == 16 * '\0'
		
		root = Node(self.file, rootnode_offset)
		root.path = '<root>'
		path = ''
		curdirs = [root.size]
		dirnames = ['<root>']
		filenum = 1
		while curdirs:
			node = Node(self.file, rootnode_offset + 12 * root.size)
			node.path = posixpath.join(path, node.name)
			filenum += 1
			if node.type == 0x100:
				# change current path if this is a directory
				path = node.path
				#print node.name, node.path
				curdirs.append(node.size)
				dirnames.append(node.name)
			else: self.files.append(node)
			
			indices = range(len(curdirs))
			indices.reverse()
			while curdirs and filenum >= curdirs[len(curdirs)-1]:
				#print 'done with ' + dirnames.pop() + ' at %d' % filenum
				path = posixpath.dirname(path)
				curdirs.pop()
	
	# closes the physical file associated with this archive
	def close(self):
		self.file.close()
	
	# returns True if this archive has a file with the given path
	def hasfile(self, path):
		f = self.getfile(path)
		if f:
			f.close()
			return True
		else:
			return False
	
	# returns a file-like object (actually a cStringIO object) for the specified
	# file; detects and decompresses compressed files (LZ77/Huf8/LZH8) automatically!
	# path: file name (string) or actual file node, but NOT node path :D
	def getfile(self, path):
		for node in self.files:
			#print "testing one..."
			#print node
			#print node.name
			if node == path or (type(path) == str and node.name.endswith(path)):
				if node == path:
					path = node.name
				self.file.seek(node.data_offset)
				file = StringIO(self.file.read(node.size))
				if path.startswith("LZ77"):
					try:
						decompressed_file = lz77.decompress(file)
						file.close()
						return decompressed_file
					except ValueError, IndexError:
						print "LZ77 decompression of '%s' failed" % path
						print 'Dumping compressed file to %s' % path
						f2 = open(path, "wb")
						f2.write(file.read())
						f2.close()
						file.close()
						return None
				elif path.startswith("Huf8"):
					try:
						decompressed_file = StringIO()
						huf8.decompress(file, decompressed_file)
						file.close()
						decompressed_file.seek(0)
						return decompressed_file
					except Exception:
						print "Huf8 decompression of '%s' failed" % path
						print "Dumping compressed file to %s" % path
						f2 = open(path, "wb")
						f2.write(file.read())
						f2.close()
						file.close()
					return decompressed_file
				elif path.startswith("LZH8"):
					try:
						decompressed_file = StringIO()
						decompressed_file.write(lzh8.decompress(file))
						decompressed_file.seek(0)
						file.close()
						return decompressed_file
					except Exception:
						print "LZH8 decompression of '%s' failed" % path
						print "Dumping compressed file to %s" % path
						f2 = open(path, "wb")
						f2.write(file.read())
						f2.close()
						file.close()
						return None
				else:
					return file
		return None
	
	# finds a file with the given name, accounting for compression prefixes like "LZ77", "Huf8", etc.
	def findfile(self, name):
		for f in self.files:
			names = (name, "LZ77"+name, "LZ77_"+name, "Huf8"+name, "Huf8_"+name, "LZH8"+name, "LZH8_"+name)
			if f.name in names: return f.name
		return None

	def findfilebyregex(self, reExpression):
		for f in self.files:
			if re.match(reExpression, f.name): return f.name
		return None

	def extract(self, dest):
		if not os.path.lexists(dest): os.makedirs(dest)
		for node in self.files:
			if node.name in ('<root>', '.'): continue
			if node.type == 0x100:
				os.makedirs(os.path.join(dest, node.path))
				#print 'created dir %s' % os.path.join(dest, node.path)
			else:
				#print node.path
				path = os.path.join(dest, node.path)
				if not os.path.lexists(os.path.dirname(path)): os.makedirs(os.path.dirname(path))
				f = open(path, 'wb')
				contents = self.getfile(node)
				contents.seek(0)
				f.write(contents.read())
				f.close()
				#print 'extracted file %s' % os.path.join(dest, node.path)

# file node object
class Node(object):
	def __init__(self, arcfile, stringoffset):
		self.rawdata = arcfile.read(12)
		arcpos = arcfile.tell()
		chunk1, self.data_offset, self.size = tuple(struct.unpack('>III', self.rawdata))
		self.type = chunk1 >> 16
		self.name_offset = chunk1 & 0xffffff
		
		# the root node has a name_offset of 0
		if not self.name_offset: return
		
		# no sane file name should be more than 64 bytes; if one is, string.index() will throw an exception
		arcfile.seek(stringoffset + self.name_offset)
		self.name = arcfile.read(64)
		self.name = self.name[0:self.name.index('\0')]
		#print self.name
		arcfile.seek(arcpos)

if __name__ == '__main__':
	# Quick functionality test and sanity check; will only work on my (Plombo's) computer without a path change
	import os, os.path
	arc = U8Archive(os.path.join(os.getenv('HOME'), 'wii/ssb/00000005.app'))
	print arc.hasfile('romc')
	print len(arc.getfile('romc').read())

