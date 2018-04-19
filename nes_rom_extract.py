#!/usr/bin/env python
# Author: Bryan Cain (Plombo)
# Extracts an NES ROM or FDS image from a 00000001.app file from an NES Virtual Console game.

import sys, struct, hashlib
from array import array
from cStringIO import StringIO
from lz77 import WiiLZ77


NES_HEADER_MAGIC_WORD = 'NES\x1a'
FDS_SIDE_HEADER_MAGIC_WORD = '\x01*NINTENDO-HVC*'
FDS_BIOS_HEADER_MAGIC_WORD = '\x00\x38\x4C\xC6\xC6\xC6\x64\x38\x00\x18\x38\x18\x18\x18\x18\x7E'


def extract_fds_bios_rom(app1, tryLZ77 = True):
	fdsBiosOffset = scan_for_fds_bios(app1)
	if fdsBiosOffset >= 0:
		app1.seek(fdsBiosOffset)
		fileData = app1.read(0x2000) # = 8 KiB
		fileHash = hashlib.md5(fileData)
		print "Found FDS BIOS ROM with hash: " + fileHash.hexdigest()

		return StringIO(fileData)
	
	if tryLZ77:
		unc = WiiLZ77(app1)
		try:
			return extract_fds_bios_rom(StringIO(unc.uncompress_11()), False)
		except IndexError:
			return None

	else:
		return None


# return:
# 	result = 0 (neither cartridge or FDS), 1 (cartridge), or 2 (FDS)
#	output = the rom/disk image data as StringIO with iNES or FDS header 
def extract_nes_rom(app1, tryLZ77 = True):
	
	cartridgeRomOffset = scan_for_cartridge_header(app1)
	if cartridgeRomOffset >= 0:
		return (1, extract_cartridge_rom(app1, cartridgeRomOffset))

	fdsImageOffset = scan_for_fds_header(app1)
	if fdsImageOffset >= 0:
		return (2, extract_fds_image(app1, fdsImageOffset))

	# some app files are compressed. decompress the entire file.
	# it seems the ROMs are decompressed properly even if we do not start the decompression at the ROM's start position.
	if tryLZ77:
		unc = WiiLZ77(app1)
		try:
			(result, output) = extract_nes_rom(StringIO(unc.uncompress_11()), False)
			return (result, output)
		except IndexError:
			return (0,None)
			
	else:
		return (0,None)
	

def scan_for_cartridge_header(inputFile):
	# The NES header is: (source = http://wiki.nesdev.com/w/index.php/INES )
	# Byte 0-4 = 'NES\x1a'
	# Byte 5-A = header data
	# Byte B-F = 0x00
	
	position = 0
	while True:
		inputFile.seek(position)
		position = inputFile.read().find(NES_HEADER_MAGIC_WORD)
		if position < 0:
			#no header found. return -1.
			return position
		else:
			#check if header byte B-F is zeroes, to skip some false positives
			inputFile.seek(position + 0xB)
			if inputFile.read(5) == '\x00\x00\x00\x00\x00':
				# most likely a NES header
				return position
			else:
				# not a NES header - keep searching
				position += 1


def scan_for_fds_header(inputFile):
	inputFile.seek(0)
	return inputFile.read().find(FDS_SIDE_HEADER_MAGIC_WORD)


def extract_cartridge_rom(inputFile, start):
	# NES ROM found; calculate size and extract it (FIXME: size calculation doesn't work)
	inputFile.seek(start+4)
	# This assumes the ROMs doesn't have any of the optional stuff (trainer, file name, etc)

	size = 16 # 16-byte header, 128-byte title data (optional footer)
	size += 16 * 1024 * struct.unpack(">B", inputFile.read(1))[0] # next byte: number of PRG banks, 16KB each
	size += 8 * 1024 * struct.unpack(">B", inputFile.read(1))[0] # next byte: number of CHR banks, 8KB each
	inputFile.seek(start)
	return StringIO(inputFile.read(size))

def extract_fds_image(inputFile, start):
	#NES VC FDS images are prefixed with VCI header.
	#However, this header is also used on some ROMs, and the header does not indicate whether the data is a cart rom or fds image.
	#So, just ignore the VCI header and look for the headers from the disk images... 

	#For reference, the ignored VCI header is as follows:
	#Byte 00-03 = VCI\x1a (Virtual Console Image?)
	#Byte 04-08 = ?????? (often 0x00 but sometimes different values)
	#Byte 09    = number of disk sides (0x01, 0x02) but is e.g. 0x04 for NES Open Tournament Golf (cart game)
	#Byte 0A-2F = ?????? (often 0x00 but sometimes different values)
	#DISK SIDE BLOCK (repeated for each disk side)
	#0000-FFFF =
	# 	Image of one disk side, should start with \x01*NINTENDO-HVC.
	# 	Disk gaps between files excluded (just like in FDS format).
	# 	The end of the disk is just zeroes, just like with FDS format, however, the VC format has longer padding.
	VCI_DISK_SIDE_LENGTH = 0x10000

	#OUTPUT FORMAT: (fds format as described here: https://wiki.nesdev.com/w/index.php/Family_Computer_Disk_System)
	#Byte 00-03 = FDS\x1a
	FDS_MAGIC_WORD_LENGTH = 0x4
	#Byte 04 = number of sides (0x01, 0x02)
	FDS_SIDE_COUNT_POSITION = 0x04
	#Byte 05-0F = 0x00
	FDS_HEADER_LENGTH = 0x10
	#DISK SIDE BLOCK (one for each side in byte 04)
	#0000-FFDC = image of one disk side, should start with \x00*NINTENDO-HVC. Disk gaps between files excluded. The end of the image is padded with zeroes.
	FDS_DISK_SIDE_LENGTH = 0xFFDC

	#We ignore VC so start should point directly to the first FDS side image

	outputArray = array('B', bytearray(['F','D','S',0x1a]))
	outputArray.extend(array('B', '\0' * (FDS_HEADER_LENGTH-FDS_MAGIC_WORD_LENGTH)) )

	sideCounter = 0
	while True:
		vciSideStart = start + sideCounter*VCI_DISK_SIDE_LENGTH
		inputFile.seek(vciSideStart)
		if inputFile.read(len(FDS_SIDE_HEADER_MAGIC_WORD)) == FDS_SIDE_HEADER_MAGIC_WORD:
			sideData = extract_fds_side(inputFile, vciSideStart)
			outputArray.extend(sideData)
			outputArray.extend(array('B', '\0' * (FDS_DISK_SIDE_LENGTH - len(sideData))))

			sideCounter += 1
		else:
			break

	outputArray[FDS_SIDE_COUNT_POSITION] = sideCounter
	print "Found " + str(sideCounter) + " floppy disk sides"

	return StringIO(outputArray)


def extract_fds_side(inputFile, vciSideStart):
	#Within the disk sides, there is one difference between the VC format and the FDS format:
	#The VC format includes a 2 byte checksum (or at least padding where the checksum used to be) after each block
	#We need to parse the side, block by block, and skip the checksums.

	#checksum is NOT included in these lengths.
	inputFile.seek(vciSideStart)
	BLOCK_1_LENGTH = 0x38 #Side header
	BLOCK_1_HEADER = '\x01'
	
	BLOCK_2_LENGTH = 0x02 #Number of files on the side - though some disks lie to improve load times. have to scan the entire side!
	BLOCK_2_HEADER = '\x02'
	
	BLOCK_3_LENGTH = 0x10 #File header
	BLOCK_3_HEADER = '\x03'
	BLOCK_3_SIZE_OF_BLOCK_4_POSITION = 0xD # Position of little endian 2 byte value that defines the size of the block 4 data (excluding header and checksum)
	BLOCK_3_SIZE_OF_BLOCK_4_SIZE = 0x2

	BLOCK_4_HEADER = '\x04'
	BLOCK_4_HEADER_LENGTH = 0x1
	#Blocks are 1,2,[(3,4),(3,4),(3,4),...]. after the last file is padded with 0 till the end of the side.

	CHECKSUM_LENGTH = 0x02

	inputPosition = vciSideStart
	side = extract_fds_block(inputFile, inputPosition, BLOCK_1_LENGTH, BLOCK_1_HEADER)
	inputPosition += BLOCK_1_LENGTH + CHECKSUM_LENGTH

	side.extend(extract_fds_block(inputFile, inputPosition, BLOCK_2_LENGTH, BLOCK_2_HEADER))
	inputPosition += BLOCK_2_LENGTH + CHECKSUM_LENGTH

	inputFile.seek(inputPosition)
	while is_fds_block(inputFile, inputPosition, BLOCK_3_HEADER):
		block3 = extract_fds_block(inputFile, inputPosition, BLOCK_3_LENGTH, BLOCK_3_HEADER)
		block4length = BLOCK_4_HEADER_LENGTH + struct.unpack('<H', block3[BLOCK_3_SIZE_OF_BLOCK_4_POSITION : BLOCK_3_SIZE_OF_BLOCK_4_POSITION+BLOCK_3_SIZE_OF_BLOCK_4_SIZE])[0]
		side.extend(block3)
		inputPosition += BLOCK_3_LENGTH + CHECKSUM_LENGTH

		side.extend(extract_fds_block(inputFile, inputPosition, block4length, BLOCK_4_HEADER))
		inputPosition += block4length + CHECKSUM_LENGTH

		inputFile.seek(inputPosition)

	return side

# returns True if the block at inputStart matches the header.
# returns False if the block at inputStart is empty 0x00 (i.e. no more files)
# throws error if the header is of not the expected type
def is_fds_block(inputFile, inputStart, header):
	inputFile.seek(inputStart)
	if inputFile.read(len(header)) == header:
		return True
	
	inputFile.seek(inputStart)
	if inputFile.read(1) == '\x00':
		return False

	raise ValueError


# Gets the next block. Throws error if the block is not the expected type.
def extract_fds_block(inputFile, inputStart, length, header):

	inputFile.seek(inputStart)
	assert inputFile.read(len(header)) == header

	inputFile.seek(inputStart)
	return array('B', inputFile.read(length))


def scan_for_fds_bios(inputFile):
	inputFile.seek(0)
	return inputFile.read().find(FDS_BIOS_HEADER_MAGIC_WORD)




if __name__ == '__main__':
	if len(sys.argv) != 3:
		sys.exit('Usage: %s input.app output' % sys.argv[0])
	f = open(sys.argv[1], 'rb')
	result, output = extract_nes_rom(f)
	f.close()
	if result <= 0:
		print "No rom or disk image found in file!"
	else:
		if result == 1:
			filename = sys.argv[2] + ".nes"
		elif result == 2:
			filename = sys.argv[2] + ".fds"

		f2 = open(filename, 'wb')
		f2.write(output.read())
		f2.close()
		print 'Done!'
	
