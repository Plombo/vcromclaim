#!/usr/bin/env python
# Author: Bryan Cain (Plombo)
# Date: August 2010
# Updated: December 28, 2010
# Extracts an NES ROM from a 00000001.app file from an NES Virtual Console game.

import sys
from cStringIO import StringIO

# returns a file-like object
def extract_nes_rom(app1):
	romoffset = 0
	while True:
		buf = app1.read(8192)
		if buf.find('NES\x1a') >= 0: # Found NES ROM
			romoffset += buf.find('NES\x1a')
			break
		elif len(buf) != 8192: # End of file, and no NES rom found
			app1.close()
			return None
		else: romoffset += 8192
	
	# NES ROM found; calculate size and extract it (FIXME: size calculation doesn't work)
	app1.seek(romoffset)
	#size = 16 + 128 # 16-byte header, 128-byte title data (footer)
	#size += 16 * 1024 * ord(app1.read(1)) # next byte: number of PRG banks, 16KB each
	#size += 8 * 1024 * ord(app1.read(1)) # next byte: number of CHR banks, 8KB each
	app1.seek(romoffset)
	rom = StringIO(app1.read())
	return rom

if __name__ == '__main__':
	if len(sys.argv) != 3:
		sys.exit('Usage: %s input.app output.nes' % sys.argv[0])
	f = open(sys.argv[1], 'rb')
	rom = extract_nes_rom(f)
	f.close()
	f2 = open(sys.argv[2], 'wb')
	f2.write(rom.read())
	f2.close()
	print 'Done!'
	
