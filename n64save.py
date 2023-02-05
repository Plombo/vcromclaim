#!/usr/bin/env python3
# Author: Bryan Cain
# Date: January 22, 2011
# Description: Converts Virtual Console N64 saves to Mupen64Plus N64 saves.
# The save formats used by N64 Virtual Console games were reverse engineered by Bryan Cain.



# EXAMPLES:
# Mario Golf (North America) = 4e415545 = NMFE
# Save file created in Project64: ".sra", >= 27 KiB (seems to cut after the last written byte)
# Save file created in Wii: "RAM_MMFE", 48KiB (where the P64 file ends, the Wii file is padded with 0xAA)
# Project64 is fine with using the 48 KiB Wii file as it is, so that is how we export it
# Actual hardware: 32KiB battery-backed SRAM




import os, shutil, struct

# Converts (byte-swaps) Nintendo N64 SRAM and/or Flash RAM saves to little endian
# SRAM and/or Flash RAM saves that can be used by Mupen64Plus and other emulators.
def convert_sram(src, name, size):
	# determine output extensions
	if size == 32*1024:
		ext = '.sra'
	if size == 48*1024:
		ext = '.sra'
	elif size == 128*1024:
		ext = '.fla'
	elif size == 256*1024:
		ext = '.fla' # this might be the wrong extension, fix if needed
	
	# copy original file as a big-endian save file
	shutil.copy2(src, name+'.be'+ext)
	
	# open files
	infile = open(src, 'rb')
	outfile = open(name+'.le'+ext, 'wb')
	
	# byte-swap file
	while True:
		data = infile.read(8192)
		if len(data) != 8192:
			if len(data) != 0: raise ValueError('SRAM save file size should be a multiple of 8 KB')
			break
		
		intdata = struct.unpack('>2048I', data)
		outfile.write(struct.pack('<2048I', *intdata))
	
	outfile.close()
	infile.close()

# Converts (truncates) Nintendo N64 EEPROM saves to the appropriate size so they 
# can be used with Mupen64Plus and other N64 emulators.
def convert_eeprom(src, name):
	infile = open(src, 'rb')
	outfile = open(name + '.eep', 'wb')
	
	data = infile.read(2048)
	if len(data) != 2048: raise ValueError('EEPROM save file size should be at least 2 KB')
	outfile.write(data)
	
	outfile.close()
	infile.close()

def convert(src, name):
	f = open(src, 'rb')
	f.seek(0, os.SEEK_END)
	size = f.tell()
	f.close()
	
	if size in (4*1024, 16*1024): convert_eeprom(src, name)
	elif size in (32*1024, 48*1024, 128*1024, 256*1024): convert_sram(src, name, size)
	else: raise ValueError('unknown save type (size=%d bytes)' % size)

if __name__ == '__main__':
	import sys
	if len(sys.argv) != 3:
		sys.stderr.write('Usage: %s infile outfile\n' % sys.argv[0])
		sys.exit(1)
	convert(sys.argv[1], sys.argv[2])
	print('Done')

