#!/usr/bin/env python
# Author: Bryan Cain (Plombo)
# Extracts an NES ROM or FDS image from a 00000001.app file from an NES Virtual Console game.

import sys, struct, hashlib
import copy
from array import array
from cStringIO import StringIO
import lz77


NES_HEADER_MAGIC_WORD = 'NES\x1a'

#VCI file format used by Virtual console
VCI_DISK_SIDE_LENGTH = 0x10000

#.fds file format used by common emulators
#OUTPUT FORMAT: (fds format as described here: https://wiki.nesdev.com/w/index.php/Family_Computer_Disk_System)
#Byte 00-03 = FDS\x1a
FDS_MAGIC_WORD = bytearray(['F','D','S',0x1a])
FDS_MAGIC_WORD_LENGTH = 0x4
#Byte 04 = number of sides (0x01, 0x02)
FDS_SIDE_COUNT_POSITION = 0x04
FDS_SIDE_SIZE = 0x01
#Byte 05-0F = 0x00
FDS_HEADER_LENGTH = 0x10
#DISK SIDE BLOCK (one for each side in byte 04)
#0000-FFDC = image of one disk side, should start with \x00*NINTENDO-HVC. Disk gaps between files excluded. The end of the image is padded with zeroes.
FDS_DISK_SIDE_LENGTH = 0x0FFDC

#original data on disks/ROMs
FDS_SIDE_HEADER_MAGIC_WORD = '\x01*NINTENDO-HVC*'
FDS_BIOS_HEADER_MAGIC_WORD = '\x00\x38\x4C\xC6\xC6\xC6\x64\x38\x00\x18\x38\x18\x18\x18\x18\x7E'


def extract_fds_bios_from_app(app1, tryLZ77 = True):
	fdsBiosOffset = find_fds_bios_in_app(app1)
	if fdsBiosOffset >= 0:
		app1.seek(fdsBiosOffset)
		fileData = app1.read(0x2000) # = 8 KiB
		fileHash = hashlib.md5(fileData)
		print "Found FDS BIOS ROM with hash: " + fileHash.hexdigest()

		return StringIO(fileData)
	
	if tryLZ77:
		try:
			return extract_fds_bios_from_app(StringIO(lz77.decompress_lz77_11(app1, 4, 5 * 1024 * 1024)), False)
		except IndexError:
			return None

	else:
		return None


# return:
# 	result = 0 (neither cartridge or FDS), 1 (cartridge), or 2 (FDS)
#	output = the rom/disk image data as StringIO with iNES or FDS header 
def extract_nes_file_from_app(app1, tryLZ77 = True):
	
	cartridgeRomOffset = find_cartridge_header_in_app(app1)
	if cartridgeRomOffset >= 0:
		return (1, get_cartridge_in_app(app1, cartridgeRomOffset))

	fdsImageOffset = find_fds_header_in_app(app1)
	if fdsImageOffset >= 0:
		return (2, StringIO(get_vci_image_as_fds_image(get_vci_body_in_app(app1, fdsImageOffset))))

	# some app files are compressed. decompress the entire file.
	# it seems the ROMs are decompressed properly even if we do not start the decompression at the ROM's start position.
	if tryLZ77:
		#f = open('compressed-NES', 'wb')
		#app1.seek(0)
		#f.write(app1.read())
		#app1.seek(0)
		#f.close()
		
		try:
			#try to autodetect format
			(result, output) = extract_nes_file_from_app(StringIO(lz77.decompress_nonN64(app1)), False)
			return (result, output)
		except ValueError:
			try:
				#try brutally decompressing the entire file
				(result, output) = extract_nes_file_from_app(StringIO(lz77.decompress_lz77_11(app1, 4, 5 * 1024 * 1024)), False)
				return (result, output)
			except IndexError:
				return (0,None)
			
	else:
		return (0,None)
	

def find_cartridge_header_in_app(inputFile):
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


def find_fds_header_in_app(inputFile):
	inputFile.seek(0)
	return inputFile.read().find(FDS_SIDE_HEADER_MAGIC_WORD)

def get_cartridge_in_app(inputFile, start):
	# NES ROM found; calculate size and extract it
	inputFile.seek(start+4)
	# This assumes the ROMs doesn't have any of the optional stuff (trainer, file name, etc)

	size = 16 # 16-byte header, 128-byte title data (optional footer)
	size += 16 * 1024 * struct.unpack(">B", inputFile.read(1))[0] # next byte: number of PRG banks, 16KB each
	size += 8 * 1024 * struct.unpack(">B", inputFile.read(1))[0] # next byte: number of CHR banks, 8KB each
	inputFile.seek(start)
	return StringIO(inputFile.read(size))

# Returns the body as an array - all sides of the game, but with no header, in the Wii format (VCI)
def get_vci_body_in_app(inputFile, start):
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
	
	outputArray = array('B', [])
	sideCounter = 0
	while True:
		vciSideStart = start + sideCounter*VCI_DISK_SIDE_LENGTH

		inputFile.seek(vciSideStart)
		if inputFile.read(len(FDS_SIDE_HEADER_MAGIC_WORD)) == FDS_SIDE_HEADER_MAGIC_WORD:
			inputFile.seek(vciSideStart)
			outputArray.extend(array('B', inputFile.read(VCI_DISK_SIDE_LENGTH)))
			sideCounter += 1
		else:
			break

	return outputArray


def get_vci_image_as_fds_image(vciImage):
	#convert the VCI image to the FDS file format.

	numberOfSides = len(vciImage) / VCI_DISK_SIDE_LENGTH

	outputArray = array('B', FDS_MAGIC_WORD)
	outputArray.extend([numberOfSides])
	outputArray.extend(array('B', '\0' * (FDS_HEADER_LENGTH - FDS_MAGIC_WORD_LENGTH - FDS_SIDE_SIZE)) )

	for sideIndex in xrange(0, numberOfSides):
		outputArray.extend(get_vci_side_as_fds_side(vciImage, sideIndex*VCI_DISK_SIDE_LENGTH))

	return outputArray


def get_vci_side_as_fds_side(vciImage, vciSideStart):
	#Within the disk sides, there is one difference between the VC format and the FDS format:
	#The VC format includes a 2 byte checksum (or at least padding where the checksum used to be) after each block
	#We need to parse the side, block by block, and skip the checksums.

	#checksum is NOT included in these lengths.
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
	side = get_fds_block_from_vci_image(vciImage, inputPosition, BLOCK_1_LENGTH, BLOCK_1_HEADER)
	inputPosition += BLOCK_1_LENGTH + CHECKSUM_LENGTH

	side.extend(get_fds_block_from_vci_image(vciImage, inputPosition, BLOCK_2_LENGTH, BLOCK_2_HEADER))
	inputPosition += BLOCK_2_LENGTH + CHECKSUM_LENGTH

	while is_fds_block_in_vci_image(vciImage, inputPosition, BLOCK_3_HEADER):
		block3 = get_fds_block_from_vci_image(vciImage, inputPosition, BLOCK_3_LENGTH, BLOCK_3_HEADER)
		block4length = BLOCK_4_HEADER_LENGTH + struct.unpack('<H', block3[BLOCK_3_SIZE_OF_BLOCK_4_POSITION : BLOCK_3_SIZE_OF_BLOCK_4_POSITION+BLOCK_3_SIZE_OF_BLOCK_4_SIZE])[0]
		side.extend(block3)
		inputPosition += BLOCK_3_LENGTH + CHECKSUM_LENGTH

		side.extend(get_fds_block_from_vci_image(vciImage, inputPosition, block4length, BLOCK_4_HEADER))
		inputPosition += block4length + CHECKSUM_LENGTH

	side.extend(array('B', '\0' * (FDS_DISK_SIDE_LENGTH - len(side))))
	return side

# returns True if the block at inputStart matches the header.
# returns False if the block at inputStart is empty 0x00 (i.e. no more files)
# throws error if there is a header or unexpected data
def is_fds_block_in_vci_image(vciImage, inputStart, header):
	if vciImage[inputStart : inputStart+len(header)] == array('B',header):
		return True
	
	if vciImage[inputStart] == 0:
		return False

	raise ValueError


# Gets the next block. Throws error if the block is not the expected type.
def get_fds_block_from_vci_image(vciImage, inputStart, length, header):
	assert vciImage[inputStart : inputStart + len(header)] == array('B',header)
	return vciImage[inputStart : inputStart + length]


def convert_nes_save_data(originalFilePath, outputPathWithoutExtension, appFile):

	# Both VC NES and FDS have a 64-bit header. For a few random games it had these values:
	# EBDM
	# 0x00000000
	# 4 bytes; always different (checksum)
	# 4 bytes; alphanumerical code of game (e.g. FAKJ for japanese Zelda, FC6E for US StarTropics)
	# 0x200611040000  (always the same?)
	# 0x00 for Zelda, 0x02 for StarTropics (save type? region?)
	# 0x00
	# 0x60, 0x80 or 0xA0 for Zelda, depending on the number of saves in the save file. 0x20 for StarTropics.
	# 0x00000002
	# EBDM
	# 0x000000
	# 0x04 for Zelda, 0x02 for StarTropics. Region? Save data type?
	# 4 bytes for the save payload size - 0x00001E for 30 bytes of data, 002000 for 8192 bytes of data
	# 0x00 for the rest of the 64 bytes



	if (find_cartridge_header_in_app(appFile) > 0):
		# The actual data payload is the rest of the file. This is the same format as FCEUX etc use.
		# Perhaps the file is padded just like FDS saves are, but the current solutions seems to be working OK.
		infile = open(originalFilePath, 'rb')
		outfile = open(outputPathWithoutExtension + '.sav', 'wb')
		infile.seek(64)
		outfile.write(infile.read())
		outfile.close()
		infile.close()
		return True
	else: #fds
		# The body is a format very similar to a IPS patch:
		# 3 bytes of offset (I), referring to a position in the VCI image file (excluding VCI header).
		# 2 bytes of data length (N)
		# The N bytes to apply at offset (I).
		# (Repeated)
		# 0xFF indicates end of file.
		# padded with 0x00 up to 128KB. (so total file size is 128KB + 64 byte for the header)
		# the above should be the same as the payload size in the header.

		# NOTE: additionally, the savefile can simply be 128KB + 64 bytes but have nothing but 0s, if nothing has been saved in the game.

		#Since VCI is a format that is not used by common emulators, we are not exporting the disk images in that format.
		#We could either export an IPS file with the offsets adjusted to the converted FDS file, or we can just apply this savefile on the
		# VCI file and convert the patched VCI file to .FDS format as a savefile.

		infile = open(originalFilePath, 'rb')
		
		firstFourBytes = infile.read(4)
		if firstFourBytes == '\x00\x00\x00\x00':
			print 'Save file was found, but it was empty. This is normal if nothing has been saved in the game.'
			return False
		elif firstFourBytes == 'EBDM':
			infile.seek(40)
			savePayloadSize = struct.unpack('>I', infile.read(4))[0]
			assert savePayloadSize >= 1

			infile.seek(64)	
			patch = array('B', infile.read(savePayloadSize))
		
			patchedFdsImage = get_vci_image_as_fds_image(apply_patch(get_vci_body_in_app(appFile, find_fds_header_in_app(appFile)), patch))
			outfile = open(outputPathWithoutExtension + '.withsavedata.fds', 'wb') # if we name it .fds, it will overwrite the pristine file
			outfile.write(patchedFdsImage)
		else:
			raise ValueError

#passes arrays, returns arrays
def apply_patch(originalFile, patch):

	patchedFile = copy.deepcopy(originalFile)

	i = 0
	while True:
		#end of patch data - should not happen without seeing the terminator first
		assert i < len(patch)
		
		if patch[i] == 0xFF:
			#terminator - check that we are also at the end of the patch data
			assert i == len(patch)-1
			break
		else:
			#get patch offset
			byteArray = array('B', '\x00')
			byteArray.extend(patch[i:i+3])
			offset = struct.unpack('>I', array('B', byteArray))[0]
			assert offset >= 0
			
			length = struct.unpack('>H', patch[i+3 : i+5])[0]
			assert length > 0

			assert offset+length <= len(patchedFile)

			data = patch[i+5 : i+5+length]
			
			patchedFile[offset:offset+length] = data

			i += 3 + 2 + length
	
	return patchedFile


def find_fds_bios_in_app(inputFile):
	inputFile.seek(0)
	return inputFile.read().find(FDS_BIOS_HEADER_MAGIC_WORD)

if __name__ == '__main__':
	if len(sys.argv) != 3:
		sys.exit('Usage: %s input.app output' % sys.argv[0])
	f = open(sys.argv[1], 'rb')
	result, output = extract_nes_file_from_app(f)
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
	
