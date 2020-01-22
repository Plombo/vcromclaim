#!/usr/bin/env python
# Author: Bryan Cain
# Original software (romchu 0.3) written in C by hcs
# Date: January 17, 2011
# Description: Decompresses Nintendo's N64 romc compression, type 2 (LZ77+Huffman)

import sys, struct, time
from array import array

VERSION = "0.6"

class backref(object):
	def __init__(self):
		self.bits = 0
		self.base = 0

#backref backref_len[0x1D], backref_disp[0x1E];
backref_len, backref_disp = [], []
for i in xrange(0x1D):
	backref_len.append(backref())
for i in xrange(0x1E):
	backref_disp.append(backref())

#easiest to call through lz77.py
def decompress(infile, inputOffset, nominal_size):
	#print "Decompressing Romchu"

	#block_mult = 0x10000 - unused
	block_count = 0
	out_offset = 0
	
	#header parsing moved to lz77.py
	# read header
	#infile.seek(0)
	#head_buf = infile.read(4)
	#bs = init_bitstream(head_buf, 0, 4*8)

	#nominal_size = ord(head_buf[0])
	#nominal_size *= 0x100
	#nominal_size |= ord(head_buf[1])
	#nominal_size *= 0x100
	#nominal_size |= ord(head_buf[2])
	#nominal_size *= 0x40
	#nominal_size |= ord(head_buf[3]) >> 2
	#romc_type = ord(head_buf[3]) & 0x3

	#if romc_type != 2:
	#	raise ValueError("Expected type 2 romc, got %d\n" % romc_type)

	#free_bitstream(bs)

	infile.seek(inputOffset)

	# initialize backreference lookup tables
	for i in xrange(8):
		backref_len[i].bits = 0
		backref_len[i].base = i
	
	i = 8
	for scale in xrange(1, 6):
		k = (1<<(scale+2))
		while k < (1<<(scale+3)):
			backref_len[i].bits = scale
			backref_len[i].base = k
			k += (1<<scale)
			i += 1

	backref_len[28].bits = 0
	backref_len[28].base = 255

	for i in xrange(4):
		backref_disp[i].bits = 0
		backref_disp[i].base = i
	
	i = 4
	k = 4
	#for (unsigned int i = 4, scale = 1, k = 4; scale < 14; scale ++)
	for scale in xrange(1, 14):
		#for (unsigned int j = 0; j < 2; j ++, k += (1 << scale), i++)
		for j in xrange(2):
			backref_disp[i].bits = scale
			backref_disp[i].base = k
			k += (1 << scale)
			i += 1

	# be lazy and just allocate memory for the whole file
	out_buf = array('B', '\0' * nominal_size)
	out_offset = 0
	
	# decode each block
	while True:
		head_buf = infile.read(4)
		if len(head_buf) != 4: break
		
		'''
		printf("%08lx=%08lx\n",
			(unsigned long)(ftell(infile)-4),
			(unsigned long)block_count*block_mult);
		'''

		head_bs = init_bitstream(head_buf, 0, 4*8)

		compression_flag = get_bits(head_bs, 1)
		if compression_flag: # compressed
			# number of bits, including this header
			block_size = get_bits(head_bs, 31) - 32
			payload_bytes = block_size/8
			payload_bits = block_size%8
		else: # uncompressed
			# number of bytes
			block_size = get_bits(head_bs, 31)
			payload_bytes = block_size
			payload_bits = 0

		#free_bitstream(head_bs)
		head_bs = None

		# read payload
		read_size = payload_bytes
		if payload_bits > 0:
			read_size += 1

		#this is not needed in Python
		'''if read_size > len(payload_buf):
			raise ValueError("payload too large")'''
		
		payload_buf = infile.read(read_size)

		# attempt to parse...
		if compression_flag:
			# read table 1 size
			tab1_offset = 0
			bs = init_bitstream(payload_buf, tab1_offset, payload_bytes*8+payload_bits)
			tab1_size = get_bits(bs, 16)
			#free_bitstream(bs)

			# load table 1
			bs = init_bitstream(payload_buf, tab1_offset + 2, tab1_size)
			table1 = load_table(bs, 0x11D)
			#free_bitstream(bs)

			# read table 2 size
			tab2_offset = tab1_offset + 2 + (tab1_size+7) / 8
			bs = init_bitstream(payload_buf, tab2_offset, 2*8)
			tab2_size = get_bits(bs, 16)
			#free_bitstream(bs)

			# load table 2
			bs = init_bitstream(payload_buf, tab2_offset + 2, tab2_size)
			table2 = load_table(bs, 0x1E)
			#free_bitstream(bs)

			# decode body
			body_offset = tab2_offset + 2 + (tab2_size+7) / 8
			body_size = payload_bytes*8 + payload_bits - body_offset*8
			bs = init_bitstream(payload_buf, body_offset, body_size)

			while (bs.bits_left + bs.first_byte_bits) != 0:
				symbol = huf_lookup(bs, table1)

				if symbol < 0x100:
					# byte literal
					#unsigned char b = symbol;
					b = symbol
					assert out_offset <= nominal_size # generated too many bytes
					out_buf[out_offset] = b
					out_offset += 1
				else:
					# backreference
					len_bits = backref_len[symbol-0x100].bits
					length = backref_len[symbol-0x100].base
					if len_bits > 0:
						length += get_bits(bs, len_bits)
					length += 3

					symbol2 = huf_lookup(bs, table2)

					disp_bits = backref_disp[symbol2].bits
					disp = backref_disp[symbol2].base
					if disp_bits > 0:
						disp += get_bits(bs, disp_bits)
					disp += 1

					assert disp <= out_offset # backreference too far
					assert (out_offset + length) <= nominal_size # generated too many bytes
					
					#for i in range(length):
					count = 0
					while count < length:
						#for i in range(length):
						out_buf[out_offset] = out_buf[out_offset-disp]
						out_offset += 1
						count += 1

			#free_table(table1)
			#free_table(table2)
			#free_bitstream(bs)
		else: # not compression_flag
			assert (out_offset + payload_bytes) <= nominal_size # generated too many bytes
			out_buf[out_offset:out_offset+payload_bytes] = array('B', payload_buf[0:payload_bytes])
			out_offset += payload_bytes

		block_count += 1
		sys.stdout.write("\rDecompressed %d of %d bytes [%x/%x] (%5.2f%%)" % (out_offset, nominal_size, out_offset, nominal_size, 100.0 * out_offset / nominal_size))
		sys.stdout.flush()
		#print '\nDecompressed block %d in %.2f seconds' % (block_count, time.clock() - start)
	
	print # start a new line after the progress counter
	assert out_offset == nominal_size # size mismatch
	
	#print 'Average block time: %.2f seconds' % (time.clock() / block_count)
	
	return out_buf
	

# bitstream reader
class bitstream(object):
	def __init__(self):
		#const unsigned char* pool
		#long bits_left
		#uint8_t first_byte
		#int first_byte_bits
		self.pool = None
		self.bits_left = 0
		self.first_byte = 0
		self.first_byte_bits = 0
		self.index = 0

# struct bitstream *init_bitstream(const unsigned char *pool, unsigned long pool_size)
def init_bitstream(pool_buf, pool_start, pool_size):
	bs = bitstream()

	bs.pool = array('B', pool_buf[pool_start:pool_start+pool_size])
	bs.bits_left = pool_size
	bs.first_byte_bits = 0

	# check that padding bits are 0 (to ensure we aren't ignoring anything)
	if pool_size % 8:
		if bs.pool[pool_size/8] & ~((1<<(pool_size%8))-1):
			raise ValueError("nonzero padding at end of bitstream")
	
	return bs

# uint32_t get_bits(struct bitstream *bs, int bits)
def get_bits(bs, bits):
	accum = 0

	if bits > 32:
		raise ValueError("get_bits() supports max 32")
	if bits > (bs.bits_left + bs.first_byte_bits):
		raise ValueError("get_bits() underflow")
	
	count = 0
	#for i in range(bits):
	while count < bits:
		if bs.first_byte_bits == 0:
			#print bs.bits_left, len(bs.pool), i
			bs.first_byte = bs.pool[bs.index]
			bs.index += 1
			if bs.bits_left >= 8:
				bs.first_byte_bits = 8
				bs.bits_left -= 8
			else:
				bs.first_byte_bits = bs.bits_left
				bs.bits_left = 0

		accum >>= 1
		accum |= (bs.first_byte & 1) << 31
		bs.first_byte >>= 1
		bs.first_byte_bits -= 1
		count += 1

	return accum >> (32-bits)

def free_bitstream(bs):
	pass

# Huffman code handling
'''class hufnode_inner(object):
	def __init__(self):
		self.left, self.right = 0, 0

class hufnode_leaf(object):
	def __init__(self):
		self.symbol = 0

class hufnode_union(object):
	def __init__(self):
		self.inner = hufnode_inner()
		self.leaf = hufnode_leaf()'''

class hufnode(object):
	def __init__(self):
		self.is_leaf = False
		self.symbol = 0
		self.left = 0
		self.right = 0
		#self.u = hufnode_union()

class huftable(object):
	def __init__(self):
		self.symbols = 0
		self.t = []

# struct huftable *load_table(struct bitstream *bs, int symbols)
def load_table(bs, symbols):
	len_count = [0] * 32
	codes = [0] * 32
	length_of = [0] * symbols
	i = 0
	
	while i < symbols:
		if get_bits(bs, 1):
			# run of equal lengths
			count = get_bits(bs, 7) + 2
			length = get_bits(bs, 5)

			len_count[length] += count
			for j in xrange(count):
				length_of[i] = length
				i += 1
		else:
			# set of inequal lengths
			count = get_bits(bs, 7) + 1

			for j in xrange(count):
				length = get_bits(bs, 5)
				length_of[i] = length
				len_count[length] += 1
				i += 1

	assert (bs.bits_left + bs.first_byte_bits) == 0 # did not exhaust bitstream reading table

	# compute the first canonical Hufman code for each length
	accum = 0
	for i in xrange(1, 32):
		accum = (accum + len_count[i-1]) << 1
		codes[i] = accum

	# determine codes and build a tree
	ht = huftable()
	ht.symbols = symbols
	for i in xrange(symbols * 2):
		node = hufnode()
		node.is_leaf = 0
		node.left = 0
		node.right = 0
		ht.t.append(node)
	
	next_free_node = 1
	for i in xrange(symbols):
		cur = 0
		if length_of[i] == 0:
			# 0 length indicates absent symbol
			continue
		
		#for (int j = length_of[i]-1; j >= 0; j --)
		for j in xrange(length_of[i]-1, -1, -1):
			#next = 0 # shouldn't be necessary
			assert not ht.t[cur].is_leaf # oops, walked onto a leaf

			if codes[length_of[i]] & (1<<j):
				# 1 == right
				next = ht.t[cur].right
				if 0 == next:
					next = next_free_node
					ht.t[cur].right = next
					next_free_node += 1
			else:
				# 0 == left
				next = ht.t[cur].left
				if 0 == next:
					next = next_free_node
					ht.t[cur].left = next
					next_free_node += 1

			cur = next

		ht.t[cur].is_leaf = 1
		ht.t[cur].symbol = i

		codes[length_of[i]] += 1

	return ht

# int huf_lookup(struct bitstream *bs, struct huftable *ht)
def huf_lookup(bs, ht):
	cur = 0
	while not ht.t[cur].is_leaf:
		if bs.first_byte_bits == 0:
			bs.first_byte = bs.pool[bs.index]
			bs.index += 1
			if bs.bits_left >= 8:
				bs.first_byte_bits = 8
				bs.bits_left -= 8
			else:
				bs.first_byte_bits = bs.bits_left
				bs.bits_left = 0
		
		#if get_bits(bs, 1):
		if bs.first_byte & 1:
			# 1 == right
			cur = ht.t[cur].right
		else:
			cur = ht.t[cur].left
		
		bs.first_byte >>= 1
		bs.first_byte_bits -= 1

	return ht.t[cur].symbol


