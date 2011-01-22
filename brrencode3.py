#!/usr/bin/env python
# Author: Bryan Cain
# Based on but heavily modified from BRRTools by Bregalad (written in Java)
# Date: January 16, 2011
# Description: Encodes 16-bit signed PCM data to SNES BRR format.

import wave
import struct

class BRREncoder(object):
	def __init__(self, pcm, brr):
		self.pcm_owner = False
		self.brr_owner = False
		
		if type(pcm) == type(''):
			pcm = open(pcm, 'rb')
			self.pcm_owner = True
		if type(brr) == type(''):
			brr = open(brr, 'wb')
			self.brr_owner = True
		
		self.pcm = pcm
		self.brr = brr
		self.p1 = 0
		self.p2 = 0
	
	# clamps value to a signed short
	def sshort(self, n):
		if n > 0x7FFF: return (n - 0x10000)
		elif n < -0x8000: return n & 0x7FFF
		else: return n
	
	# short clamp_16(int n)
	def clamp_16(self, n):
		if n > 0x7FFF: return (0x7FFF - (n>>24))
		else: return n
	
	# void ADPCMBlockMash(short[] PCMData)
	def ADPCMBlockMash(self, PCMData):
		smin=0
		kmin=0
		dmin=2**31
		
		for s in range(13, 0, -1):
			for k in range(4):
				d = self.ADPCMMash(s, k, PCMData, False)
				if d < dmin:
					kmin = k		# Memorize the filter, shift values with smaller error
					dmin = d
					smin = s
				if dmin == 0.0: break
			if dmin == 0.0: break
		
		self.BRRBuffer[0] = (smin<<4)|(kmin<<2)
		self.ADPCMMash(smin, kmin, PCMData, True)
	
	# double ADPCMMash(int shiftamount, int filter, short[] PCMData, boolean write)
	def ADPCMMash(self, shiftamount, filter, PCMData, write):
		d2=0.0
		vlin=0
		l1 = self.p1
		l2 = self.p2
		step = 1<<shiftamount
		
		for i in range(16):
			# Compute linear prediction for filters
			if filter == 0:
				pass
			elif filter == 1:
				vlin = l1 >> 1
				vlin += (-l1) >> 5
			elif filter == 2:
				vlin = l1
				vlin += (-(l1 +(l1>>1)))>>5
				vlin -= l2 >> 1
				vlin += l2 >> 5
			else:
				vlin = l1
				vlin += (-(l1+(l1<<2) + (l1<<3)))>>7
				vlin -= l2>>1
				vlin += (l2+(l2>>1))>>4
			
			d = (PCMData[i]>>1) - vlin		# Difference between linear prediction and current sample
			da = abs(d)

			if da > 16384 and da < 32768:
				d = d - 32768 * ( d >> 24 ) # Take advantage of wrapping
			dp = d + (step << 2) + (step >> 2)
			c = 0
			if dp > 0:
				if step > 1:
					c = dp /(step>>1)
				else:
					c = dp<<1
				if c > 15:
					c = 15
			c -= 8
			dp = (c<<(shiftamount-1))		# quantized estimate of samp - vlin
											# edge case, if caller even wants to use it */
			if shiftamount > 12:
				dp = ( dp >> 14 ) & ~0x7FF
			c &= 0x0f						# mask to 4 bits
			l2 = l1							# shift history
			l1 = self.sshort(self.clamp_16(vlin + dp)*2)
			d = PCMData[i]-l1
			d2 += float(d)*d				# update square-error

			if write:						# if we want output, put it in proper place */
				self.BRRBuffer[(i>>1)+1] |= c<<(4-((i&0x01)<<2))
		
		if write:
			self.p2 = l2
			self.p1 = l1
		
		return d2
	
	# encodes the entire PCM file to BRR
	def encode(self):
		self.BRRBuffer = [0, 0, 0, 0, 0, 0, 0, 0, 0] # byte[9]
		
		#wav = wave.open(wav, 'rb')
		#if wav.getsampwidth() != 2: raise ValueError('must be 16 bits per sample')
		pcm = self.pcm
		brr = self.brr
		self.p1 = 0
		self.p2 = 0
		
		samples2 = pcm.read(32) # the PCM samples in VC PCM files are misaligned for some reason
		while len(samples2) == 32:
			samples2 = struct.unpack('>16h', samples2)
			self.BRRBuffer = [0, 0, 0, 0, 0, 0, 0, 0, 0]
			self.ADPCMBlockMash(samples2)
			brr.write(struct.pack('9B', *self.BRRBuffer))
			#samples2 = wav.readframes(16)
			samples2 = pcm.read(32)
		
		#wav.close()
		if self.pcm_owner: pcm.close()
		if self.brr_owner: brr.close()
	
	# offset: PCM offset (measured in samples, NOT in bytes)
	# returns: 9-byte BRR block
	def encode_block(self, offset):
		# read PCM - the PCM samples in VC PCM files are misaligned for some reason
		self.pcm.seek(offset * 2)
		samples2 = self.pcm.read(32)
		
		if len(samples2) != 32:
			raise ValueError('invalid PCM offset %d (file offset %d)' % (offset, offset*2))
		
		samples2 = struct.unpack('>16h', samples2)
		
		# encode to BRR
		self.BRRBuffer = [0, 0, 0, 0, 0, 0, 0, 0, 0]
		self.ADPCMBlockMash(samples2)
		
		return struct.pack('9B', *self.BRRBuffer)


if __name__ == '__main__':
	import sys
	if len(sys.argv) != 3:
		print 'Usage: %s input.pcm output.brr' % sys.argv[0]
	enc = BRREncoder(sys.argv[1], sys.argv[2])
	enc.encode()
	print 'Wrote file %s' % sys.argv[2]

