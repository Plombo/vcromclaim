#!/usr/bin/env python3
# Original author: ZOINKITY
# Original version? https://pastebin.com/hcRjjTWg
# CRC part copied and downgraded to Python 2 by JanErikGunnar

import struct

class Cart():
    cic_names = {
        "starf":0x3F,
        "lylat":0x3F,
        "mario":0x3F,
        "diddy":0x78,
        "aleck":0xAC,
        "zelda":0x91,
        "yoshi":0x85,
        "ddipl":0xDD,
        "dddev":0xDD,
        "ddusa":0xDE,
        }

    def __init__(self, rom):
        """Sets ROM data, unswaps it if swapped,
            and extracts some handy header data.

        Expects rom to be a byte-like object."""
        self.rom = bytearray(rom)
        self.programCounter = struct.unpack(">I",rom[8:12])[0] # int.from_bytes(data[8:12], byteorder='big')

    @staticmethod
    def cic2seed(cic):
        """Returns (name, seed) for <cic>.
        name: the normalized name of the chip
        seed: unencoded seed value.
            <cic> should be a str, matching the serial or short name of the chip.
        cic types:
            'aleck', '5101'
            'starf', '6101'
            'lylat', '7102'
            'mario', '6102', '7101'
            'diddy', '6103', '7103'
            'ddipl', '8303'
            'dddev'
            'ddusa'
            'zelda', '6105', '7105'
            'yoshi', '6106', '7106'
        """
        # Normalize the names.  (kinda makes the dict pointless...)
        cic = cic.lower()
        if cic in ("6102", "7101", "mario"):
            cic = "mario"
        elif cic in ("6101", "starf"):
            cic = "starf"
        elif cic in ("7102", "lylat"):
            cic = "starf"
        elif cic in ("6103", "7103", "diddy"):
            cic = "diddy"
        elif cic in ("6105", "7105", "zelda"):
            cic = "zelda"
        elif cic in ("6106", "7106", "yoshi"):
            cic = "yoshi"
        elif cic in ("5101", 'aleck'):
            cic = 'aleck'
        elif cic in ("8303", "ddipl"):
            cic = "ddipl"
        elif cic in ("8302", "8301", "dddev"):
            cic = "dddev"
        elif cic in ("ddusa"):
            cic = "ddusa"
        else:
            raise TypeError("Unknown CIC type {}.".format(cic))
        return cic, Cart.cic_names.get(cic)

    @property
    def crc(self):
        """Returns CRC in rom as a tuple of integers."""
        u = struct.unpack(">I",self.rom[16:20])[0] # int.from_bytes(self.rom[16:20], byteorder='big')
        l = struct.unpack(">I",self.rom[20:24])[0] # int.from_bytes(self.rom[20:24], byteorder='big')
        return (u, l)

    def calccrc(self, cic='mario', fix=False, seed=None, base=0x1000, seel=None):
        """Recalculates the CRC based on the CIC chip version given.
        Set fix to True to revise the crc in self.rom.

        cic types:
            'aleck', '5101'
            'starf', '6101'
            'lylat', '7102'
            'mario', '6102', '7101'
            'diddy', '6103', '7103'
            'ddipl', '8303'
            'dddev'
            'ddusa'
            'zelda', '6105', '7105'
            'yoshi', '6106', '7106'
        Setting seed overrides the normal seed value for these types.
        If you need to use one of the particular cic algorithms set the
            string version of the name in cic.  Now that the Aleck64
            CIC has been identified this will probably not be necessary
            unless some repro cic chips start using different values."""
        def rol(v, n):
            return (v % 0x100000000)>>n

        # The algo slightly changes with certain cics.
        cic, s = self.cic2seed(cic)
        # Pull the seed byte and generate the seed from it.
        # Note even if seed is set you'll have to pass a cic "name" to get funky types out.
        if seed is not None:
            s = seed
        if cic in ('diddy', 'yoshi', 'aleck'):
            seed = 0x6C078965 * s
        elif cic in ('ddipl', 'ddusa'):
            seed = 0x2E90EDD * s
        elif cic == 'dddev':
            seed = 0x260BCD5 * s
        else:
            seed = 0x5D588B65 * s
        seed+= 1
        seed&=0xFFFFFFFF
        r1, r2, r3, r4, r5, r6 = seed, seed, seed, seed, seed, seed

        # I wish there was a less horrifying way to do this...
        from array import array
        if seel is None:
            if cic == 'aleck':
                seel = 0x3FE000 if self.programCounter == 0x80100400 else 0x100000
            elif cic in ('ddipl', 'dddev', 'ddusa'):
                seel = 0xA0000
            else:
                seel = 0x100000
        seel += base
        l = min(seel, len(self.rom))

        #in Python 3, bytes(7) returns a null array of length 7
        #in Python 3, bytes(7) returns a 
        m = array("L", struct.unpack(">" + str(int((l-base)/4)) + "L", self.rom[base:l]) + tuple(bytearray(seel - l)))
        #Python3: m = array("L", self.rom[base:l] + bytes(seel - l))
        #Python3: m.byteswap()

        # Zelda updates the second word a different way...
        if cic == 'zelda':
            from itertools import cycle
            n = array("L", struct.unpack(">" + str(int((0x850-0x750)/4)) + "L", self.rom[0x750:0x850]))
            #Python3: n = array("L", self.rom[0x750:0x850])
            #Python3: n.byteswap()
            n = cycle(n)
        
        # Read each word as an integer.
        for i in m:
            v = (r1+i) & 0xFFFFFFFF
            if v < r1:
                if cic in ('ddipl', 'ddusa'):
                    r2^=r3
##                if cic == 'dddev':
##                    pass    # invalid opcode in v1.0: 014A0000
                else:
                    r2+=1
            v = i & 0x1F
            a = (i<<v) | (rol(i, 0x20-v))
            r1+=i
            r3^=i
            r4+=a
            # You have to limit the result here to 32bits.
            r1&= 0xFFFFFFFF
            r4&= 0xFFFFFFFF
            if r5 < i:
                r5^= (r1^i)
            else:
##                if cic in ('ddipl', 'dddev'):
                if cic  == 'ddipl':
                    r5+=a
                else:
                    r5^=a
            if cic == 'zelda':
                r6+= (i ^ next(n))
            else:
                r6+= (i ^ r4)
            # Ditto here.
            r5&= 0xFFFFFFFF
            r6&= 0xFFFFFFFF

        # Assemble upper and lower CRCs
        if cic in ('ddipl', 'dddev', 'ddusa'):
            if fix:
                if isinstance(self.rom, bytes):
                    self.rom = bytearray(self.rom)
                self.setASMvalue(r1, 0x608, 0x60C)
                self.setASMvalue(r2, 0x618, 0x61C)
                self.setASMvalue(r3, 0x628, 0x62C)
                self.setASMvalue(r4, 0x638, 0x63C)
                self.setASMvalue(r5, 0x648, 0x64C)
                self.setASMvalue(r6, 0x658, 0x65C)
            return (r1, r2, r3, r4, r5, r6)
        if cic == 'yoshi':
            r1*=r2
            r4*=r5
        else:
##            r2&= 0xFFFFFFFF
            r1^=r2
            r4^=r5
        if cic in ('diddy', 'yoshi', 'aleck'):
            r1+=r3
            r4+=r6
        else:
            r1^=r3
            r4^=r6
        # Make sure they fit within 4 bytes each.
        r1&= 0xFFFFFFFF
        r4&= 0xFFFFFFFF
        if fix:
            if isinstance(self.rom, bytes):
                self.rom = bytearray(self.rom)
            self.rom[16:20] = struct.pack(">I", r1) #r1.to_bytes(4, 'big')
            self.rom[20:24] = struct.pack(">I", r4) #r4.to_bytes(4, 'big')
        return (r1,r4)

    def bootstrapcrc(self, cic='mario', seed=None):
        if seed is None:
            cic, seed = self.cic2seed(cic)

        def trimult(v1, v2, v3):
            if not v2:
                v2 = v3
            l = v1 * v2
            u = (l>>32) & 0xFFFFFFFF
            l &= 0xFFFFFFFF
            u -= l
            if not u:
                u = v1
            return (u & 0xFFFFFFFF)

        def rol(v, n):
            return (v % 0x100000000)>>n

        data = struct.unpack(">1008L", self.rom[0x40:0x1000])

        seed *= 0x6C078965
        seed += 1
        seed ^= data[0]
        seed &= 0xFFFFFFFF
        regs = [seed, seed, seed, seed, seed, seed, seed, seed,
                seed, seed, seed, seed, seed, seed, seed, seed,]
        count = 0   #S1
        cur = data[0]  #S4
        # First half of the algorithm: read in bootcode.
        while True:
            prev = cur  #S4
            cur = data[count]   #S0
            count += 1
            v = (0x3EF - count) & 0xFFFFFFFF
            regs[0] +=  trimult(v, cur, count)
            regs[0] &= 0xFFFFFFFF
            regs[1] = trimult(regs[1], cur, count)
            regs[2] ^= cur
            regs[3] += trimult(cur + 5, 0x6C078965, count)
            regs[3] &= 0xFFFFFFFF
            # BFC00250
            if prev < cur:
                regs[9] = trimult(regs[9], cur, count)
            else:
                regs[9] += cur
            regs[9] &= 0xFFFFFFFF
            # BFC00288
            b = prev & 0x1F
            u = cur << (32 - b)
            l = rol(cur, b)
            roll1 = (u | l) & 0xFFFFFFFF   #S5
            regs[4] += roll1
            regs[4] &= 0xFFFFFFFF
            b = prev & 0x1F
            u = cur << b
            l = rol(cur, 32 - b)
            v = (u | l) & 0xFFFFFFFF
            regs[7] = trimult(regs[7], v, count)
            # BFC002C0
            if cur < regs[6]:
                regs[6] += regs[3]
                regs[6] ^= cur + count
            else:
                regs[6] ^= regs[4] + cur
            regs[6] &= 0xFFFFFFFF
            # BFC002FC
            b = prev >> 0x1B
            u = cur << b
            l = rol(cur, 32 - b)
            roll2 = (u | l) & 0xFFFFFFFF   #S2
            regs[5] += roll2
            regs[5] &= 0xFFFFFFFF
            u = cur << (32 - b)
            l = rol(cur, b)
            v = (u | l) & 0xFFFFFFFF
            regs[8] = trimult(regs[8], v, count)
            if count == 0x3F0:
                break
            future = data[count]    #S3
            # BFC00340
            regs[15] = trimult(regs[15], roll2, count)
            b = rol(cur, 0x1B)
            u = future << b
            l = rol(future, 32 - b)
            v = (u | l) & 0xFFFFFFFF
            regs[15] = trimult(regs[15], v, count)
            # BFC00374
            regs[14] = trimult(regs[14], roll1, count)
            b = cur & 0x1F  #S2
            u = future << (32 - b)
            l = rol(future, b)
            v = (u | l) & 0xFFFFFFFF
            regs[14] = trimult(regs[14], v, count)
            # BFC003A4
            u = cur << (32 - b)
            l = rol(cur, b)
            v = (u | l) & 0xFFFFFFFF
            regs[13] += v
            b = future & 0x1F
            u = future << (32 - b)
            l = rol(future, b)
            v = (u | l) & 0xFFFFFFFF
            regs[13] += v
            regs[13] &= 0xFFFFFFFF
            # BFC003DC
            regs[10] += cur
            regs[10] = trimult(regs[10] & 0xFFFFFFFF, future, count)
            regs[11] = trimult(regs[11] ^ cur, future, count)
            regs[12] += regs[8] ^ cur
            regs[12] &= 0xFFFFFFFF
        # BFC00420
        buf = [regs[0], regs[0], regs[0], regs[0]]
        for i in range(16):
            cur = regs[i]
            b = cur & 0x1F
            u = cur << (32 - b)
            l = rol(cur, b)
            v = (u | l) & 0xFFFFFFFF
            buf[0] += v
            buf[0] &= 0xFFFFFFFF
            if cur < buf[0]:
                buf[1] += cur
                buf[1] &= 0xFFFFFFFF
            else:
                buf[1] = trimult(buf[1], cur, i)
            # BFC00494
            if (cur & 3) in (0, 3):
                buf[2] += cur
                buf[2] &= 0xFFFFFFFF
            else:
                buf[2] = trimult(buf[2], cur, i)
            # BFC004CC
            if cur & 1:
                buf[3] ^= cur
            else:
                buf[3] = trimult(buf[3], cur, i)
        # BFC00504
        v = trimult(buf[0], buf[1], 16)
        b = buf[2] ^ buf[3]
        return (v & 0xFFFFFFFF, b & 0xFFFFFFFF)

    def getASMvalue(self, upper, lower=None):
        """If <upper> and <lower> are given,
            reads the address given by a LUI+ADDIU or LUI+ORI pair.
            If upper is None only the lower half will be read.
        If only <upper> is given,
            reads the address in a J or JAL instruction, | 80000000."""
        if lower is None:
            u = struct.unpack(">H",self.rom[upper+2:upper+4])[0] & 0x3FFFFFF # int.from_bytes(self.rom[upper+2:upper+4], 'big') & 0x3FFFFFF
            u<<=2
            return u | 0x80000000
        if upper is None:
            u = 0
        else:
            u = struct.unpack(">H",self.rom[upper+2:upper+4])[0] <<16 #int.from_bytes(self.rom[upper+2:upper+4], 'big')<<16

        if self.rom[lower]&0x10:
            l = struct.unpack(">H",self.rom[upper+2:upper+4])[0] # int.from_bytes(self.rom[lower+2:lower+4], 'big', signed=False)
        else:
            l = struct.unpack(">h",self.rom[upper+2:upper+4])[0] # int.from_bytes(self.rom[lower+2:lower+4], 'big', signed=True)
        return u+l

    def setASMvalue(self, value, upper, lower=None):
        """If <upper> and <lower> are given,
            sets the LUI+ADDIU or LUI+ORI pair to value.
            If upper is None only the lower half will be set.
        If only <upper> is given,
            sets value as the address of a J or JAL instruction."""
        if lower is None:
            value>>=2
            value&=0x3FFFFFF
            u = self.rom[upper] & 0xFC
            value|= u<<24
            self.rom[upper:upper+4] = struct.pack(">I", value) #value.to_bytes(4, 'big')
        else:
            u = value>>16
            l = value&0xFFFF
            if not self.rom[lower]&0x10:
                u += bool(l&0x8000)
            if upper is not None:
                self.rom[upper+2:upper+4] = struct.pack(">H", u) # u.to_bytes(2, 'big')
            self.rom[lower+2:lower+4] = struct.pack(">H", l) # l.to_bytes(2, 'big')

def updateN64Crc(romdata):
    cart = Cart(romdata)

    cic = {
    0:"starf",
    0xD5:"lylat",
    0xDE:"mario",
    0xDB:"diddy",
    0xE4:"aleck",
    0x14:"zelda",
    0xEC:"yoshi",
    }.get(cart.rom[0x173], 'mario')
    if cic == "starf":
        if cart.rom[0x16F]==0xDB:
            cic = "ddipl" if cart.rom[0x5F3] == 0x21 else "ddusa"
        elif cart.rom[0x16F]==0xD9:
            cic = "dddev"
    cic = Cart.cic2seed(cic)
    print("Updating the checksum...")
    print("CIC type\t%s" % cic[0])
    if cic[0] in ('ddipl', 'dddev', 'ddusa'):
        print("internal\t{:08X} {:08X} {:08X} {:08X} {:08X} {:08X}".format(cart.getASMvalue(0x608, 0x60C), cart.getASMvalue(0x618, 0x61C), cart.getASMvalue(0x628, 0x62C), cart.getASMvalue(0x638, 0x63C), cart.getASMvalue(0x648, 0x64C), cart.getASMvalue(0x658, 0x65C)))
        print("calculated\t{:08X} {:08X} {:08X} {:08X} {:08X} {:08X}".format(*cart.calccrc(cic[0], fix=True)))
    else:
        print("internal\t{:08X} {:08X}".format(*cart.crc))
        print("calculated\t{:08X} {:08X}".format(*cart.calccrc(cic[0], fix=True)))

    return cart.rom
