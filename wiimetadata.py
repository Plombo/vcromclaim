#!/usr/bin/env python
# Author: Bryan Cain (Plombo)
# Date: December 27, 2010
# Description: Reads Wii title metadata from an extracted NAND dump.
# Thanks to Leathl for writing Wii.cs in ShowMiiWads, which was an important 
# reference in writing this program.

import os, os.path, struct, shutil, re
from cStringIO import StringIO
import romc, gensave, n64save
from u8archive import U8Archive
from ccfarchive import CCFArchive
from nes_rom_extract import extract_nes_rom, extract_fds_bios_rom
from snesrestore import restore_brr_samples

# rom: file-like object
# path: string (filesystem path)
def writerom(rom, path):
	f = open(path, 'wb')
	f.write(rom.read())
	f.close()
	rom.seek(0)

class RomExtractor(object):
	# file extensions for ROMs
	extensions = {
		'Nintendo 64': '.z64',
		'Genesis': '.gen',
		'Master System': '.sms',
		'SNES': '.smc',
		'TurboGrafx16': '.pce'
		#NES extension is determined by media type (cart = nes, disk = fds)
	}
	
	def __init__(self, id, name, channeltype, nand):
		self.id = id
		self.name = name
		self.channeltype = channeltype
		self.nand = nand
	
	def extract(self):
		content = os.path.join(self.nand.path, 'title', '00010001', self.id, 'content')
		rom_extracted = False
		manual_extracted = False
		
		for app in os.listdir(content):
			if not app.endswith('.app'): continue
			app = os.path.join(content, app)
			if self.extractrom(app): rom_extracted = True
			if self.extractmanual(app): manual_extracted = True
			if rom_extracted and manual_extracted: return
		
		if rom_extracted: print 'Unable to extract manual.'
		elif manual_extracted: print 'Unable to extract ROM.'
		else: print 'Unable to extract ROM and manual.'
	
	# Actually extract the ROM
	# Currently works for almost all NES, SNES, N64, TG16, Master System, and Genesis ROMs.
	def extractrom(self, u8path):
		funcs = {
			'Nintendo 64': self.extractrom_n64,
			'Genesis': self.extractrom_sega,
			'Master System': self.extractrom_sega,
			'NES': self.extractrom_nes,
			'SNES': self.extractrom_snes,
			'TurboGrafx16': self.extractrom_tg16
		}
		
		if self.channeltype == 'NES':
			arc = u8path
		else:
			try:
				arc = U8Archive(u8path)
				if not arc: return False
			except AssertionError:
				return False
		
		if self.channeltype in funcs.keys():
			return funcs[self.channeltype](arc, self.name)
		else:
			return False
	
	# FIXME: use string instead of StringIO
	def extractrom_nes(self, u8path, filenameWithoutExtension):
		if not os.path.exists(u8path): return False
		
		f = open(u8path, 'rb')
		result, output = extract_nes_rom(f)
		f.close()
		
		if result == 1:
			# nes rom

			# make sure save flag is set if the game has save data
			if self.extractsave():
				if not (ord(output.getvalue()[6]) & 2):
					output = list(output.getvalue())
					output[6] = chr(ord(output[6]) | 2)
					output = StringIO(''.join(output))
					print 'Set the save flag to true'

			filename = filenameWithoutExtension + ".nes"

			print 'Got ROM: %s' % filename

		elif result == 2:
			# FDS
			print "Sorry, no save file support for FDS games yet."

			filename = filenameWithoutExtension + ".fds"

			print 'Got FDS image: %s' % filename

		else:
			return False

		writerom(output, filename)
		return True
	
	def extractrom_n64(self, arc, filenameWithoutExtension):
		filename = filenameWithoutExtension + self.extensions[self.channeltype]
		if arc.hasfile('rom'):
			rom = arc.getfile('rom')
			print 'Got ROM: %s' % filename
			writerom(rom, filename)
		elif arc.hasfile('romc'):
			rom = arc.getfile('romc')
			print 'Decompressing ROM: %s (this could take a minute or two)' % filename
			try:
				romdata = romc.decompress(rom)
				outfile = open(filename, 'wb')
				outfile.write(romdata)
				outfile.close()
				print 'Got ROM: %s' % filename
			except IndexError: # unknown compression - something besides LZSS and romchu?
				print 'Decompression failed: unknown compression type'
				outfile.close()
				os.remove(filename)
				return False
		else: return False
		
		# extract save file
		savepath = self.extractsave()
		if savepath: print 'Extracted save file(s)'
		else: print 'Failed to extract save file(s)'
		
		return True
	
	def extractrom_sega(self, arc, filenameWithoutExtension):
		filename = filenameWithoutExtension + self.extensions[self.channeltype]
		if arc.hasfile('data.ccf'):
			ccf = CCFArchive(arc.getfile('data.ccf'))
		
			if ccf.hasfile('config'):
				for line in ccf.getfile('config'):
					if line.startswith('romfile='): romname = line[len('romfile='):].strip('/\\\"\0\r\n')
			else:
				print 'config not found'
				return False
			
			if romname:
				print 'Found ROM: %s' % romname
				rom = ccf.find(romname)
				writerom(rom, filename)
				print 'Got ROM: %s' % filename
				
				if self.extractsave(): print 'Extracted save to %s.srm' % self.name
				else: print 'No save file found'
				
				return True
			else:
				print 'ROM filename not specified in config'
				return False
	
	def extractrom_tg16(self, arc, filenameWithoutExtension):
		filename = filenameWithoutExtension + self.extensions[self.channeltype]
		config = arc.getfile('config.ini')
		if not config:
			print 'config.ini not found'
			return False
		
		path = None
		for line in config:
			if line.startswith('ROM='):
				path = line[len('ROM='):].strip('/\\\"\0\r\n')
		
		if not path:
			print 'ROM filename not specified in config.ini'
			return False
		
		print 'Found ROM: %s' % path
		rom = arc.getfile(path)
	
		if rom:
			writerom(rom, filename)
			print 'Got ROM: %s' % filename
			return True
		else: return False
	
	def extractrom_snes(self, arc, filenameWithoutExtension):
		filename = filenameWithoutExtension + self.extensions[self.channeltype]
		extracted = False
		
		# try to find the original ROM first
		for f in arc.files:
			path = f.path.split('.')
			if len(path) == 2 and path[0].startswith('SN') and path[1].isdigit():
				print 'Found original ROM: %s' % f.path
				rom = arc.getfile(f.path)
				writerom(rom, filename)
				print 'Got ROM: %s' % filename
				
				extracted = True
	
		# if original ROM not present, try to create a playable ROM by recreating and injecting the original sounds
		if not extracted:
			for f in arc.files:
				path = f.path.split('.')
				if len(path) == 2 and path[1] == 'rom':
					print "Recreating original ROM from %s" % f.path
					vcrom = arc.getfile(f.path)
					if not vcrom: print "Error in reading ROM file %s" % f.path; return False
			
					# find raw PCM data
					pcm = None
					for f2 in arc.files:
						path2 = f2.path.split('.')
						if len(path2) == 2 and path2[1] == 'pcm':
							pcm = arc.getfile(f2.path)
					if not pcm: print 'Error: PCM audio data not found'; return False
			
					'''# encode raw PCM in SNES BRR format
					print 'Encoding audio as BRR'
					brr = StringIO()
					enc = BRREncoder(pcm, brr)
					enc.encode()
					pcm.close()'''
			
					# inject BRR audio into the ROM
					print 'Encoding and restoring BRR audio data to ROM'
					romdata = restore_brr_samples(vcrom, pcm)
					vcrom.close()
					pcm.close()
			
					# write the recreated ROM to disk
					f = open(filename, 'wb')
					f.write(romdata)
					f.close()
					print 'Got ROM: %s' % filename
					extracted = True
		
		# extract save data (but don't overwrite existing save data)
		if extracted:
			srm = filename[0:filename.rfind('.smc')] + '.srm'
			if os.path.lexists(srm): print 'Not overwriting existing save data'
			elif self.extractsave(): print 'Extracted save data to %s' % srm
			else: print 'Could not extract save data'
		
		return extracted
	
	# copy save file, doing any necessary conversions to common emulator formats
	def extractsave(self):
		datadir = os.path.join(self.nand.path, 'title', '00010001', self.id, 'data')
		datafiles = os.listdir(datadir)
		
		for filename in datafiles:
			path = os.path.join(datadir, filename)
			if filename == 'savedata.bin':
				if self.channeltype == 'SNES':
					# VC SNES saves are standard SRM files
					outpath = self.name + '.srm'
					shutil.copy2(path, outpath)
					return True
				elif self.channeltype == 'NES':
					# VC NES saves use the same format as FCEUX, except with an
					# additional 64-byte header
					outpath = self.name + '.sav'
					infile = open(path, 'rb')
					outfile = open(outpath, 'wb')
					infile.seek(64)
					outfile.write(infile.read())
					outfile.close()
					infile.close()
					return True
				elif self.channeltype == 'Genesis':
					# VC Genesis saves use a slightly different format from 
					# the one used by Gens/GS and other emulators
					outpath = self.name + '.srm'
					gensave.convert(path, outpath)
					return True
			elif filename.startswith('EEP_') or filename.startswith('RAM_'):
				assert self.channeltype == 'Nintendo 64'
				n64save.convert(path, self.name)
				return True
		
		return False
	
	def extractmanual(self, u8path):
		try:
			arc = U8Archive(u8path)
			if not arc: return False
		except AssertionError: 
			return False
	
		man = None
		try:
			if arc.findfile('emanual.arc'):
				man = U8Archive(arc.getfile(arc.findfile('emanual.arc')))
			elif arc.findfile('html.arc'):
				man = U8Archive(arc.getfile(arc.findfile('html.arc')))
			elif arc.findfile('man.arc'):
				man = U8Archive(arc.getfile(arc.findfile('man.arc')))
			elif arc.findfile('data.ccf'):
				ccf = CCFArchive(arc.getfile(arc.findfile('data.ccf')))
				man = U8Archive(ccf.getfile('man.arc'))
			elif arc.findfile('htmlc.arc'):
				manc = arc.getfile(arc.findfile('htmlc.arc'))
				print 'Decompressing manual: htmlc.arc'
				man = U8Archive(StringIO(romc.decompress(manc)))
		except AssertionError: pass
	
		if man:
			man.extract(os.path.join('manuals', self.name))
			print 'Extracted manual to ' + os.path.join('manuals', self.name)
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
				#print title, content + appname
				name = self.gettitle(os.path.join(content, appname), id)
				channeltype = self.channeltype(ticket)
				if name and channeltype:
					print '%s: %s (ID: %s)' % (channeltype, name, id)
					ext = RomExtractor(id, name, channeltype, self)
					ext.extract()
					print
	
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
		if ident[0] == 'F': return 'NES'
		elif ident[0] == 'J': return 'SNES'
		elif ident[0] == 'L': return 'Master System'
		elif ident[0] == 'M': return 'Genesis'
		elif ident[0] == 'N': return 'Nintendo 64'
		elif ident[0] == 'P': return 'TurboGrafx16'
		#elif ident == 'EA': return 'Neo Geo'
		#elif ident[0] == 'E': return 'Arcade'
		#elif ident[0] == 'Q': return 'TurboGrafx CD'
		#elif ident[0] == 'C': return 'Commodore 64'
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
		index = data.find('IMET')
		if index < 0: return None
		engindex = index + 29 + 84
		title = data[engindex:engindex+84]
		
		# Format the title properly
		title = title.strip('\0')
		while title.find('\0\0\0') >= 0: title = title.replace('\0\0\0', '\0\0')
		title = title.replace('\0\0', ' - ')
		title = title.replace('\0', '')
		title = title.replace(':', ' - ')

		# Replace some characters
		title = re.sub('!a', 'II', title) # e.g. Zelda II 
		title = re.sub('!b', 'III', title) # e.g. Ninja Gaiden III
		title = re.sub(' \x19', '\'', title) # e.g. Indiana Jones' GA

		# Delete any characters that are not known to be safe
		title = re.sub('[^A-Za-z0-9\\-\\!\\_\\&\\\'\\. ]', '', title)

		# more than one consequtive spaces --> one space
		while title.find('  ') >= 0: title = title.replace('  ', ' ')

		# Delete any mix of "." and space at beginning or end of string - they are valid in filenames, but not always as head or tail
		title = re.sub('(^[\\s.]*)|([\\s.]*$)', '', title)

		# If we stripped everything (maybe can happen on japanese titles?), fall back to using defaultTitle
		if len(title) <= 0:
			title = defaultTitle

		return title

if __name__ == '__main__':
	import sys
	nand = NandDump(sys.argv[1])
	nand.scantickets()

