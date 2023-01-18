#!/usr/bin/env python3
# Author: Bryan Cain (Plombo)
# Date: December 27, 2010
# Description: Reads Wii title metadata from an extracted NAND dump.
# Thanks to Leathl for writing Wii.cs in ShowMiiWads, which was an important 
# reference in writing this program.

import os, os.path, struct, shutil, re, zlib, lzma
from io import BytesIO
import gensave, n64save
from u8archive import U8Archive
from ccfarchive import CCFArchive
import lz77
from nes_extract import extract_nes_file_from_app, extract_fds_bios_from_app, convert_nes_save_data
from snesrestore import restore_brr_samples
from neogeo_decrypt import decrypt_neogeo
from neogeo_convert import convert_neogeo
from arcade_extract import extract_arcade
from tgcd_extract import extract_tgcd
from tgsave import unmangle_tgsave
from configurationfile import getConfiguration 
from n64crc import updateN64Crc
import game_specific_patches

# rom: file-like object
# path: string (filesystem path)
def writerom(rom, path):
	f = open(path, 'wb')
	rom.seek(0)
	f.write(rom.read())
	f.close()
	rom.seek(0)

class RomExtractor(object):
	# file extensions for ROMs (not applicable for all formats)
	extensions = {
		'Nintendo 64': '.z64',
		'Genesis': '.gen',
		'Master System': '.sms',
		'SNES': '.smc',
		'TurboGrafx16': '.pce'
	}
	
	def __init__(self, id, name, channeltype, nand):
		self.id = id
		self.name = name
		self.channeltype = channeltype
		self.nand = nand

	def ensure_folder_exists(self, outputFolderName):
		if not os.path.lexists(outputFolderName):
			os.makedirs(outputFolderName)

	def extract(self):
		content = os.path.join(self.nand.path, 'title', '00010001', self.id, 'content')
		rom_extracted = False
		manual_extracted = False

		for app in os.listdir(content):
			if not app.endswith('.app'): continue
			app = os.path.join(content, app)
			if self.extractrom(app, os.path.join(self.channeltype, self.name), app[-10:], self.id): rom_extracted = True
			if self.extractmanual(app, os.path.join(self.channeltype, self.name, 'manual')): manual_extracted = True
		
		if rom_extracted and manual_extracted: return
		elif rom_extracted: print('Unable to extract manual.')
		elif manual_extracted: print('Unable to extract ROM.')
		else: print('Unable to extract ROM and manual.')
	
	# Actually extract the ROM
	# Currently works for almost all NES, SNES, N64, TG16, Master System, and Genesis ROMs.
	def extractrom(self, u8path, gameOutputPath, name, id):
		funcs = {
			'Nintendo 64': self.extractrom_n64,
			'Genesis': self.extractrom_sega,
			'Master System': self.extractrom_sega,
			'NES': self.extractrom_nes,
			'SNES': self.extractrom_snes,
			'TurboGrafx16': self.extractrom_tg16,
			'TurboGrafxCD': self.extractrom_tgcd,
			'Neo Geo': self.extractrom_neogeo,
			'Arcade': self.extractrom_arcade
		}
		
		if self.channeltype == 'NES':
			#NES roms are NOT packages in U8 archives.
			u8arc = self.tryGetU8Archive(u8path)
			if u8arc:
				return False
			else:
				u8arc = u8path
		elif self.channeltype == 'Arcade':
			#SOME arcade games are packed in U8 archives
			u8arc = u8path
		else:
			u8arc = self.tryGetU8Archive(u8path)

			#x = open(u8path, 'rb')
			#self.ensure_folder_exists(gameOutputPath)
			#f = open(os.path.join(gameOutputPath, 'file_' + name),'wb')
			#f.write(x.read())
			#f.close()

			if not u8arc:
				return False
		
		self.ensure_folder_exists(gameOutputPath)

		if self.channeltype in funcs.keys():
			return funcs[self.channeltype](u8arc, gameOutputPath, self.name, id)
		else:
			return False
	
	def extractrom_nes(self, u8path, outputPath, filenameWithoutExtension, id):
		if not os.path.exists(u8path): return False
		
		f = open(u8path, 'rb')
		result, output = extract_nes_file_from_app(f)

		hasExportedSaveData = False
		if result == 1 or result == 2:
			saveFilePath = self.getsavefile('savedata.bin')
			if saveFilePath != None:
				try:
					hasExportedSaveData = convert_nes_save_data(saveFilePath, os.path.join(outputPath, self.name), f)
				except:
					print('Failed to extract save file(s)')
					pass


#		fdsBios = extract_fds_bios_from_app(f)

		f.close()

		if result == 1:
			# nes rom

			# make sure save/SRAM flag is set if the game has save data - not sure which games this is used for?
			# Original behaviour in vcromclaim was to force the flag IF there was save data, otherwise leave it.
			# That is not complete because user maybe never saved anything.
			# Have extended to include a check for some games known to have SRAM.

			sramFlagAlreadySet = output.getvalue()[6] & 2

			if sramFlagAlreadySet:
				# WORST CASE: some games incorrectly indicate to emulator that they use SRAM.
				# If it causes problems - extend logic to clear flags of games known NOT to have SRAM?
				print('Leaving SRAM flag ON.')
			else:
				# Incomplete list of games known to have SRAM: Kirby's Adventure, Zelda 1 and 2, Star Tropics 1 and 2, Final Fantasy, Wario's Woods, NES Open Tournament Golf
				# All of those except Kirby's Adventure has been seen to have the SRAM flag set though.
				knownToHaveSram = id in ['46413845', '46414b45', '46413945', '46433645', '46455245', '46464145', '46414d45', '46415045']

				# Flag NOT set correctly! Not sure if this causes any problems, not sure if emulators actually care about this flag.
				if knownToHaveSram or hasExportedSaveData:
					print('Changing SRAM flag from OFF to ON! It is OFF in extracted ROM header, but we found saved data, or the game is known to have SRAM.')
					output.seek(6)
					output.write((output.getvalue()[6] | 2).to_bytes(1, 'little'))
				else:
					print('Leaving SRAM flag OFF, because nothing suggest it is wrong.')

			filename = os.path.join(outputPath, filenameWithoutExtension + ".nes")

			print('Got ROM: %s' % filename)

		elif result == 2:
			# FDS
			
			filename = os.path.join(outputPath, filenameWithoutExtension + ".fds")

			print('Got FDS image: %s' % filename)

		else:
			return False

		writerom(output, filename)

#		if fdsBios != None:
#			print('Extracted FDS BIOS')
#			writerom(fdsBios, os.path.join(outputPath, "DISKSYS.ROM"))
#
		if hasExportedSaveData:
			print('Extracted save data')

		return True
	
	def extractrom_n64(self, arc, outputPath, filenameWithoutExtension, id):
		filename = os.path.join(outputPath, filenameWithoutExtension + self.extensions[self.channeltype])
		if arc.hasfile('rom'):
			rom = arc.getfile('rom')
			outfile = open(filename, 'wb')
			outfile.write(updateN64Crc(game_specific_patches.patch_specific_games(rom.read())))
			outfile.close()
			print('Got ROM: %s' % filename)
		elif arc.hasfile('romc'):
			rom = arc.getfile('romc')
			print('Decompressing ROM: %s (this could take a minute or two)' % filename)
			try:
				outfile = open(filename, 'wb')
				outfile.write(updateN64Crc(game_specific_patches.patch_specific_games(lz77.decompress_n64(rom))))
				outfile.close()
				print('Got ROM: %s' % filename)
			except IndexError: # unknown compression - something besides LZSS and romchu?
				print('Decompression failed: unknown compression type')
				outfile.close()
				os.remove(filename)
				return False
		else: return False
		
		# extract save file
		savepath = self.extractsave(outputPath)
		if savepath: print('Extracted save file(s)')
		else: print('Failed to extract save file(s)')
		
		return True
	
	def extractrom_sega(self, arc, outputPath, filenameWithoutExtension, id):
		filename =  os.path.join(outputPath, filenameWithoutExtension + self.extensions[self.channeltype])
		if arc.hasfile('data.ccf'):
			ccf = CCFArchive(arc.getfile('data.ccf'))
		
			if ccf.hasfile('config'):
				romfilename = getConfiguration(ccf.getfile('config'), 'romfile')
			else:
				return False
					
			if romfilename:
				rom = ccf.find(romfilename)
				writerom(rom, filename)
				print('Got ROM: %s' % filename)
				
				if self.extractsave(outputPath):
					print('Extracted save to %s.srm' % self.name)
				else:
					print('No save file found')
				
				return True
			else:
				print('ROM filename not specified in config')
				return False
	
	def extractrom_tg16(self, arc, outputPath, filenameWithoutExtension, id):
		#for node in arc.files:
		#	print(node.name)
		config = arc.getfile('config.ini')
		#writerom(config, os.path.join(outputPath, "config.ini"))
		#savetemplate = arc.getfile('savedata.tpl')
		#writerom(savetemplate, os.path.join(outputPath, "savedata.tpl"))

		if not config:
			print('config.ini not found')
			return False

		path = getConfiguration(config, "ROM")
		
		if not path:
			print('ROM filename not specified in config.ini')
			return False

		rom = arc.getfile(path)

		if rom:
			filename =  os.path.join(outputPath, filenameWithoutExtension + self.extensions[self.channeltype])
			writerom(rom, filename)
			print('Got ROM: %s' % filename)
			self.extractsave(outputPath)
			return True

		return False

	def extractrom_tgcd(self, arc, outputPath, filenameWithoutExtension, id):
		if (arc.hasfile("config.ini")):
			extract_tgcd(arc, outputPath)
			print("Extracted TurboGrafx CD image")
			self.extractsave(outputPath)
			return True
		else:
			return False
	
	def extractrom_snes(self, arc, outputPath, filenameWithoutExtension, id):
		filename = os.path.join(outputPath, filenameWithoutExtension + self.extensions[self.channeltype])
		extracted = False
		
		# try to find the original ROM first
		for f in arc.files:
			path = f.path.split('.')
			if len(path) == 2 and path[0].startswith('SN') and path[1].isdigit():
				print('Found original ROM: %s' % f.path)
				rom = arc.getfile(f.path)
				writerom(rom, filename)
				print('Got ROM: %s' % filename)
				
				extracted = True
	
		# if original ROM not present, try to create a playable ROM by recreating and injecting the original sounds
		if not extracted:
			for f in arc.files:
				path = f.path.split('.')
				if len(path) == 2 and path[1] == 'rom':
					print("Recreating original ROM from %s" % f.path)
					vcrom = arc.getfile(f.path)
					if not vcrom: print("Error in reading ROM file %s" % f.path); return False
			
					# find raw PCM data
					pcm = None
					for f2 in arc.files:
						path2 = f2.path.split('.')
						if len(path2) == 2 and path2[1] == 'pcm':
							pcm = arc.getfile(f2.path)
					if not pcm: print('Error: PCM audio data not found'); return False
			
					'''# encode raw PCM in SNES BRR format
					print('Encoding audio as BRR')
					brr = BytesIO()
					enc = BRREncoder(pcm, brr)
					enc.encode()
					pcm.close()'''
			
					# inject BRR audio into the ROM
					print('Encoding and restoring BRR audio data to ROM')
					romdata = restore_brr_samples(vcrom, pcm)
					vcrom.close()
					pcm.close()
			
					# write the recreated ROM to disk
					f = open(filename, 'wb')
					f.write(romdata)
					f.close()
					print('Got ROM: %s' % filename)
					extracted = True
		
		# extract save data (but don't overwrite existing save data)
		if extracted:
			srm = filename[0:filename.rfind('.smc')] + '.srm'
			if os.path.lexists(srm): print('Not overwriting existing save data')
			elif self.extractsave(outputPath): print('Extracted save data to %s' % srm)
			else: print('Could not extract save data')
		
		return extracted


	def extractrom_neogeo(self, arc, outputPath, filenameWithoutExtension, id):
		foundRom = False
		for file in arc.files:
			#print(file.name)

			#arcFile = arc.getfile(file.path)
			#f = open(os.path.join(outputPath, 'arc_' + file.name),'wb')
			#f.write(arcFile.read())
			#f.close()

			#PROBABLY. game.bin = not compressed, .z = zlib compressed, .xz = LZMA/XZ compressed
			#encryption may be applied on any file, and is applied after compression (decrypt before decompressing)
			
			if file.name == "game.bin" or file.name == "game.bin.z" or file.name == "game.bin.xz":

				rom = arc.getfile(file.path)
				rom.seek(0)
				entireFile = rom.read()

				giveUp = False

				if (entireFile[0:4] == b'CR00'):
					#f = open(os.path.join(outputPath, 'encrypted_' + file.name),'wb')
					#f.write(entireFile)
					#f.close()

					(success, output) = decrypt_neogeo(self.id, entireFile)
					entireFile = output

					if not success:
						outputFileName = "game.bin.encrypted"
						print("Exporting encrypted ROMs without decrypting them")
						giveUp = True

				if not giveUp:
					if file.name == "game.bin.xz":
						assert entireFile[0:4] == b'\x5D\x00\x00\x80'
						print("Decompressing LZMA (XZ) file")
						decomp = lzma.LZMADecompressor(lzma.FORMAT_AUTO, None, None)
						entireFile = decomp.decompress(entireFile)

					elif file.name == "game.bin.z":
						assert entireFile[0] == 0x78
						print("Decompressing using zlib")
						entireFile = zlib.decompress(entireFile)

					elif file.name != "game.bin":
						#game.bin = unencrypted, uncompress game
						#any other file name: do nothing
						outputFileName = file.name
						giveUp = True

					convert_neogeo(BytesIO(entireFile), outputPath)
					print("Extracted ROM files (some BIOS files may be missing)")
				else:
					writerom(BytesIO(entireFile), os.path.join(outputPath, outputFileName))
					print("Files extracted but further processing is required.")

				if self.extractsave(outputPath):
					print("Exported memory card with save file")
				else:
					print("No save data found")

				foundRom = True

			# This is just the contents of a formatted 2KB memory card without any saves on it. Probably useless to everyone.
			#elif file.name == "memcard.dat":
			#	rom = arc.getfile(file.path)
			#	print('Got default (empty) save data')
			#	writerom(rom, os.path.join(outputFolderName, "memcard.empty.dat"))

			#This probably contains the DIP switch settings of the game, or maybe flags for the emulator
			#elif file.name == "config.dat":
			#	rom = arc.getfile(file.path)
			#	writerom(rom, os.path.join(outputFolderName, "config.dat"))

			#else: other files are probably useless
			#	rom = arc.getfile(file.path)
			#	writerom(rom, os.path.join(outputFolderName, file.name))
	

		return foundRom

	def extractrom_arcade(self, appFilePath, outputPath, filenameWithoutExtension, id):
		foundRom = False

		#print("file in app:" + appFilePath)

		u8arc = self.tryGetU8Archive(appFilePath)
		if not u8arc:
			#print("It is NOT a U8 archive! First bytes:")
			inFile = open(appFilePath, 'rb')

			inFile.seek(0)
			if (inFile.read(1))[0] == 0x11:
				#print("The first byte is 11 so it is probably compressed LZ77")
				data = lz77.decompress_nonN64(inFile)
				inFile.close()
			
				#!!! NOTE !!! This will be done multiple time for each game, overwriting the previous one
				# For ghosts n goblins, this is the only file that might contain the roms!
				outFile = open(os.path.join(outputPath, "TODO_DECOMPRESSED.BIN"), 'wb')
				outFile.write(data)
				outFile.close()
			#else:
				#print("The first byte is unknown, don't know what to do with this file, dumping it as DERP")
				#inFile.seek(0)
				#outFile = open(os.path.join(outputPath, "DERP_output" + appFilePath[(len(appFilePath)-7):]), 'wb')
				#outFile.write(inFile.read())
				#outFile.close()

		else:
			#print("It IS a U8 archive! Content:")

			#for file in u8arc.files:
			#	print(file.path)

			if u8arc.hasfile('data.ccf'):
				ccf = CCFArchive(u8arc.getfile('data.ccf'))
				if ccf.hasfile('config'):
					foundRom = extract_arcade(ccf, outputPath)

		if foundRom:
			print("Got ROMs")

		return foundRom

	def tryGetU8Archive(self, path):
		try:
			u8arc = U8Archive(path)
			if not u8arc:
				return None
			else:
				return u8arc
		except AssertionError:
			return None

	def getsavefile(self, expectedFileName):
		datadir = os.path.join(self.nand.path, 'title', '00010001', self.id, 'data')
		datafiles = os.listdir(datadir)
		for filename in datafiles:
			path = os.path.join(datadir, filename)
			if filename == expectedFileName:
				return path

		return None

	# copy save file, doing any necessary conversions to common emulator formats
	def extractsave(self, outputPath):
		datadir = os.path.join(self.nand.path, 'title', '00010001', self.id, 'data')
		datafiles = os.listdir(datadir)
		
		for filename in datafiles:
			path = os.path.join(datadir, filename)
			if (self.channeltype == 'TurboGrafxCD' or self.channeltype == 'TurboGrafx16') and filename == 'pcengine.bup':
				unmangle_tgsave(path, outputPath)
				return True
			elif filename == 'savedata.bin':
				if self.channeltype == 'SNES':
					# VC SNES saves are standard SRM files
					outpath = os.path.join(outputPath, self.name + '.srm')
					shutil.copy2(path, outpath)
					return True
				#elif self.channeltype == 'NES': #not used because FDS games requires the app file
				#return convert_nes_save_data(path, self.name)
				elif self.channeltype == 'Genesis':
					# VC Genesis saves use a slightly different format from 
					# the one used by Gens/GS and other emulators
					outpath = os.path.join(outputPath, self.name + '.srm')
					gensave.convert(path, outpath, True)
					return True
				elif self.channeltype == 'Master System':
					# VC Genesis saves use a slightly different format from 
					# the one used by Gens/GS and other emulators
					outpath = os.path.join(outputPath, self.name + '.ssm')
					gensave.convert(path, outpath, False)
					return True
			elif filename == 'savefile.dat' and self.channeltype == 'Neo Geo':
				# VC Neo Geo saves are memory card images, can be opened as is by mame
				shutil.copy2(path, os.path.join(outputPath, "memorycard.bin"))
				return True
			elif filename.startswith('EEP_') or filename.startswith('RAM_'):
				assert self.channeltype == 'Nintendo 64'
				n64save.convert(path, os.path.join(outputPath, self.name))
				return True
		
		return False
	
	def extractmanual(self, u8path, manualOutputPath):
		try:
			u8arc = U8Archive(u8path)
			if not u8arc: return False
		except AssertionError: 
			return False
	
		man = None
		try:
			if u8arc.findfile('emanual.arc'):
				man = U8Archive(u8arc.getfile(u8arc.findfile('emanual.arc')))
			elif u8arc.findfile('html.arc'):
				man = U8Archive(u8arc.getfile(u8arc.findfile('html.arc')))
			elif u8arc.findfile('man.arc'):
				man = U8Archive(u8arc.getfile(u8arc.findfile('man.arc')))
			elif u8arc.findfile('data.ccf'):
				ccf = CCFArchive(u8arc.getfile(u8arc.findfile('data.ccf')))
				man = U8Archive(ccf.getfile('man.arc'))
			elif u8arc.findfile('htmlc.arc'):
				manc = u8arc.getfile(u8arc.findfile('htmlc.arc'))
				print('Decompressing manual: htmlc.arc')
				man = U8Archive(BytesIO(lz77.decompress_n64(manc)))
			elif u8arc.findfilebyregex('.+_manual_.+\\.arc\\.lz77$'):
				# E.g. makaimura_manual_usa.arc.lz77 (Arcade Ghosts n Goblins)
				manc = u8arc.getfile(u8arc.findfilebyregex('.+_manual_.+\\.arc\\.lz77$'))
				man = U8Archive(BytesIO(lz77.decompress_nonN64(manc)))
				manc.close()
		except AssertionError: pass
	
		if man:
			self.ensure_folder_exists(manualOutputPath)
			man.extract(manualOutputPath)
			print('Extracted manual to ' + manualOutputPath)
			return True
	
		return False

class NandDump(object):
	# path: path on filesystem to the extracted NAND dump
	def __init__(self, path):
		self.path = path + '/'
	
	def scantickets(self):
		tickets = os.listdir(os.path.join(self.path, 'ticket', '00010001'))
		for ticket in tickets:
			id = ticket.rstrip('.tik')
			content = os.path.join('title', '00010001', id, 'content')
			title = os.path.join(content, 'title.tmd')
			if(os.path.exists(os.path.join(self.path, title))):
				appname = self.getappname(title)
				if not appname: continue
				#print(title, content + appname)
				name = self.gettitle(os.path.join(content, appname), id)
				channeltype = self.channeltype(ticket)
				if name and channeltype:
					print('%s: %s (ID: %s)' % (channeltype, name, id))
					ext = RomExtractor(id, name, channeltype, self)
					ext.extract()
					print()
	
	# Returns a string denoting the channel type.  Returns None if it's not a VC game.
	def channeltype(self, ticket):

		f = open(os.path.join(self.path, 'ticket', '00010001', ticket), 'rb')
		f.seek(0x1dc)
		thistype = struct.unpack('>I', f.read(4))[0]
		if thistype != 0x10001: return None
		f.seek(0x221)
		if struct.unpack('>B', f.read(1))[0] != 1: return None
		f.seek(0x1e0)
		ident = f.read(2)
		
		# TODO: support the commented game types
		# http://wiibrew.org/wiki/Title_database
		
		if ident[0] == ord('F'): return 'NES'
		elif ident[0] == ord('J'): return 'SNES'
		elif ident[0] == ord('L'): return 'Master System'
		elif ident[0] == ord('M'): return 'Genesis'
		elif ident[0] == ord('N'): return 'Nintendo 64'
		elif ident[0] == ord('P'): return 'TurboGrafx16'
		elif ident[0] == ord('E') and ident[1] == ord('A'): return 'Neo Geo' #E.g. Neo Turf Master
		elif ident[0] == ord('E') and ident[1] == ord('B'): return 'Neo Geo' #E.g. Spin Master, RFBB Special
		elif ident[0] == ord('E') and ident[1] == ord('C'): return 'Neo Geo' #E.g. Shock Troopers 2, NAM-1975
		elif ident[0] == ord('E'): return 'Arcade' #E.g. E5 = Ghosts'n' Goblins, E6 = Space Harrier
		elif ident[0] == ord('Q'): return 'TurboGrafxCD'
		#elif ident[0] == 'C': return 'Commodore 64'
		#elif ident[0] == 'X': return 'MSX'
		else: return None
	
	# Returns the path to the 00.app file containing the game's title
	# Precondition: the file denoted by "title" exists on the filesystem
	def getappname(self, title):
		f = open(os.path.join(self.path, title), 'rb')
		f.seek(0x1de)
		count = struct.unpack('>H', f.read(2))[0]
		f.seek(0x1e4)
		appname = None
		for i in range(count):
			info = struct.unpack('>IHHQ', f.read(16))
			f.read(20)
			if info[1] == 0:
				appname = '%08x.app' % info[0]
		return appname
	
	# Gets title (in English) from a 00.app file
	def gettitle(self, path, defaultTitle):
		path = os.path.join(self.path, path)
		if not os.path.exists(path): return None
		f = open(path, 'rb')
		data = f.read()
		f.close()
		index = data.find(b'IMET')
		if index < 0: return None
		engindex = index + 29 + 84
		title = data[engindex:engindex+84]
		
		# Format the title properly
		title = title.strip(b'\0')
		while title.find(b'\0\0\0') >= 0: title = title.replace(b'\0\0\0', b'\0\0')
		title = title.replace(b'\0\0', b' - ')
		title = title.replace(b'\0', b'')
		title = title.replace(b':', b' - ')

		# Replace some characters
		title = re.sub(b'!\x60', b'I', title) # e.g. Ys Book I&II
		title = re.sub(b'!\x61', b'II', title) # e.g. Zelda II 
		title = re.sub(b'!\x62', b'III', title) # e.g. Ninja Gaiden III
		title = re.sub(b' \x19', b'\'', title) # e.g. Indiana Jones' GA

		# Delete any characters that are not known to be safe
		title = re.sub(b'[^A-Za-z0-9\\-\\!\\_\\&\\\'\\. ]', b'', title)

		# more than one consequtive spaces --> one space
		while title.find(b'  ') >= 0: title = title.replace(b'  ', b' ')

		# Delete any mix of "." and space at beginning or end of string - they are valid in filenames, but not always as head or tail
		title = re.sub(b'(^[\\s.]*)|([\\s.]*$)', b'', title)

		# If we stripped everything (maybe can happen on japanese titles?), fall back to using defaultTitle
		if len(title) <= 0:
			title = defaultTitle

		return title.decode('ascii')

if __name__ == '__main__':
	import sys
	nand = NandDump(sys.argv[1])
	nand.scantickets()

