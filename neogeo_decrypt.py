#!/usr/bin/env python3

#from neogeo_keys import keys
from binascii import unhexlify
import os, hashlib
from u8archive import U8Archive

try:
    from Crypto.Cipher import AES
except:
    pass

#TODO: stop using neogeo_keys.py


def tryGetU8Archive(path):
    try:
        u8arc = U8Archive(path)
        if not u8arc:
            return None
        else:
            return u8arc
    except AssertionError:
        return None


def get_work_key_iv():
    # corresponds with code at 8013bbf8
    return bytearray(unhexlify('67452301efcdab8998badcfe10325476'))


def get_sha1_of_static_random_data():
    # there is a block in the main DOL file that we look for. it is the same for all games and the SHA1 of this block is this
    return bytearray(unhexlify('dcfefa9a3a27ff9746d9fe80712f2629332572ed'))


def get_banner(folder):
    # find the banner.bin file, which may be in any of the U8Archives in the folder
    for app in os.listdir(folder):
        app_path = os.path.join(folder, app) 
        u8arc = tryGetU8Archive(app_path)
        if u8arc:
            for file in u8arc.files:
                if file.name == 'banner.bin':
                    file_as_bytesIO = u8arc.getfile(file.path)
                    file_as_bytearray = bytearray(file_as_bytesIO.read())
                    file_as_bytesIO.close()
                    return file_as_bytearray

    raise ValueError

def get_random_static_data(folder):
    # find a block of specific data, which i sin the main DOL file
    sha1 = get_sha1_of_static_random_data()
    
    for app in os.listdir(folder):
        app_path = os.path.join(folder, app) 
        u8arc = tryGetU8Archive(app_path)
        # we are looking for a DOL, which are hard to identify...
        # but if it's an U8 archive, it is definitely not it
        if not u8arc:
            dol_file = open(os.path.join(folder, app), 'rb')
            dol_content = dol_file.read()
            for pos in range(0, len(dol_content)-0x1C0):
                if bytearray(unhexlify(hashlib.sha1(dol_content[pos:pos+0x1C0]).hexdigest())) == sha1:
                    return_value = dol_content[pos:pos+0x1C0]
                    dol_file.close()

                    return return_value
            dol_file.close()
    raise ValueError


def xor_bytearray(ba1, ba2):
    assert len(ba1) == len(ba2)
    out = bytearray(len(ba1))
    for i in range(0, len(out)):
        out[i] = ba1[i] ^ ba2[i]
    return out


def mangle_data(big_file_content, work_key_iv_untouched, static_random_data):

    work_key_iv = work_key_iv_untouched.copy()

    # 802f73b0--80306450

    work_key = [
        int.from_bytes(work_key_iv[0x00:0x04]),
        int.from_bytes(work_key_iv[0x04:0x08]),
        int.from_bytes(work_key_iv[0x08:0x0C]),
        int.from_bytes(work_key_iv[0x0C:0x10])
    ]

    for b in range(0, len(big_file_content), 0x40):
        big_file_block = big_file_content[b : b + 0x40]

        # UNKNOWN: what if file fits exactly into blocks? is a last block always added?

        magic_1 = 0x80000000 # magic value #1 
        magic_2 = 0x00000000 # magic value #2

        padding_needed = 0x40 - (len(big_file_block) % 0x40)

        # set the first byte of padding to the first byte of magic_1.
        # if there is less than 8 bytes REMAINING:
        #       pad with 00.
        # else (there is 8 bytes or more remaining:
        #       set the last 8 bytes to some mangled value derived from the total file size.
        #       if any bytes inbetween the first 1 byte and the last 8 bytes, set it to 00. 

        if padding_needed >= 0x01:
            big_file_block.append(magic_1.to_bytes(4)[0])

        if padding_needed > 0x01 and padding_needed < 0x09:
            big_file_block += bytearray((padding_needed - 1)*b'\x00')

        if padding_needed > 0x01 and padding_needed > 0x09:
            big_file_block += bytearray((padding_needed - 9)*b'\x00')

        if padding_needed >= 0x09:
            # 8013bac4--8013bb70

            ##11223344 -> 44332211

            big_file_block += ((len(big_file_content) << 3) & 0xFFFFFFFF).to_bytes(4, byteorder="little")
            big_file_block += (
                ((magic_2 << 3) & 0xfffffff8)
                |
                ((len(big_file_content) >> 29) & 0x00000007)
            ).to_bytes(4, byteorder="little")

        assert len(big_file_block) % 0x40 == 0

        work_key_block = [
            work_key[0],
            work_key[1],
            work_key[2],
            work_key[3]
        ]
            
        funcs = [
            lambda a, b, c, d : ((a + ((b & c) | (d & (b ^ 0xFFFFFFFF)))) & 0xFFFFFFFF),
            lambda a, b, c, d : ((a + ((b & d) | (c & (d ^ 0xFFFFFFFF)))) & 0xFFFFFFFF),
            lambda a, b, c, d : ((a + ((d ^ b) ^ c)) & 0xFFFFFFFF),
            lambda a, b, c, d : ((a + (c ^ (b | (d ^ 0xFFFFFFFF)))) & 0xFFFFFFFF)
        ]

        shift_amounts = [
            [7,12,17,22],
            [5, 9,14,20],
            [4,11,16,23],
            [6,10,15,21]
        ]

        #8013BC0C--8013bd00
        for h in range(0,4): # for each set of rules/shift_amounts
            for i in range(0, 4): # repeat 4 times
                for j in range(0, 4): #for each of the 4 blocks in the work_key

                    #static_random_data is actually two tables:
                    #first 0x100 is random data, to be merged with banner_block
                    #the rest 0xC0 contains smaller digits specifying which of the banner_block to use.
                    
                    index = h*4*4*4 + i*4*4 + j*4

                    random_data = int.from_bytes(static_random_data[index : index + 4])

                    if h == 0:
                        bbi = index
                    else:
                        # get index rom second block of static_random_data
                        # on > first iteration, index will be 0x40 or higher
                        bbi = int.from_bytes(static_random_data[0x100 - 0x40 + index : 0x100 - 0x40 + index + 4]) << 2

                    combined = (
                            funcs[h](
                            work_key_block[(4-j) % 4],
                            work_key_block[(5-j) % 4],
                            work_key_block[(6-j) % 4],
                            work_key_block[(7-j) % 4]
                        ) +
                            int.from_bytes(big_file_block[bbi : bbi+4], byteorder="little") +
                            random_data
                        ) & 0xFFFFFFFF

                    work_key_block[(4-j) % 4] = ((
                            work_key_block[(5-j) % 4] + (
                                (combined << shift_amounts[h][j]) # can clamp this at 0xFFFFFFFF but clamped also after the "+""
                                |
                                (combined >> (32 - shift_amounts[h][j]))
                            )
                        ) & 0xFFFFFFFF)


        # 8013c058--8013c084
        for i in range(0,4):
            work_key[i] = (work_key[i] + work_key_block[i]) & 0xFFFFFFFF

    # 8013c098
    return (
        # byteorder = "big" is the norm but this place reverse them
        work_key[0].to_bytes(4, byteorder = "little") +
        work_key[1].to_bytes(4, byteorder = "little") +
        work_key[2].to_bytes(4, byteorder = "little") +
        work_key[3].to_bytes(4, byteorder = "little")
        )

def merge_banner_key_and_cr00_key(banner_key, cr00_key):
    return xor_bytearray(banner_key, cr00_key) 


def scramble_16_bytes(input_data):
    # 8019a5c4--8019a630
    data_1 = bytearray(0x10)
    for i in range(0,16):
        data_1[i] = input_data[i] ^ 0xFF

    # 8019a644--8019a6b0
    data_2 = bytearray(0x10)
    work_byte = 0xFF
    for i in range(0,16):
        work_byte ^= data_1[i]
        data_2[i] = work_byte

    # 8019a6c0--8019a764
    data_3 = bytearray(16)
    for i in range(0,16):
        work_byte = data_2[i]
        for j in [0,3,3]:
            shift_amount = (work_byte >> j) & 7
            work_byte = ((work_byte << (8-shift_amount)) | (work_byte >> shift_amount)) & 0xFF
        data_3[i] = work_byte

    # 8019a77c--8019a834
    data_4 = bytearray(16)
    carry_over_to_next_byte = 0
    for i in range(0,16):
        shift_amount = (data_3[i] >> (carry_over_to_next_byte & 7)) & 7
        shifted = carry_over_to_next_byte | ((data_3[i] << shift_amount) & 0xFF)
        data_4[i] = shifted
        carry_over_to_next_byte = shifted >> (8-shift_amount)

    # 8019a844--8019a8d0
    data_5 = bytearray(16)
    last_input_byte = 0
    for i in range(0,16):
        data_5[i] = (last_input_byte + data_4[i]) & 0xFF
        last_input_byte = data_4[i]

    return data_5
    

def get_aes_key(folder, cr00_key):
    random_static_data = get_random_static_data(folder)
    work_key_iv = get_work_key_iv()

    return scramble_16_bytes(
        mangle_data(
            merge_banner_key_and_cr00_key(
                mangle_data(
                    get_banner(folder),
                    work_key_iv,
                    random_static_data
                ),
                cr00_key
            ),
            work_key_iv,
            random_static_data
        )
    )


# titleIdString must be the 8 byte string identifying each Wii title, e.g. '421a2b3c'
# fileString input must be a string containing the content of the encrypted romfile, starting with CR00.
# will return a tuple - either (true, decryptedData) or (false, encryptedData)
# note that the decryptedData will still be compressed (zipped), similar to some other neo geo games without encryption.
def decrypt_neogeo(sourceFolderPath, titleIdString, fileString):
    # encrypted files starts with a magic word
    assert fileString[0:4] == b'CR00'

    # the rest of the files is AES-CBC-128 encrypted. as such it consists of 16 byte (128bit) blocks.
    assert (len(fileString) - 0x14) % 0x10 == 0

    encryptedString = fileString[0x14:]
    assert len(fileString) == 0x14+len(encryptedString)

    # the next 16 bytes are used as part of key generation.
    key = get_aes_key(sourceFolderPath, bytearray(fileString[4:0x14]))

    #if (titleIdString in keys):
    #    if key == unhexlify(keys[titleIdString]):
    #        print("FOUND MATCHING KEY!!!!!!!!!! SUCCESS",key, keys[titleIdString])
    #    else:
    #        print("NOT MATCHING! :(",key, keys[titleIdString])
    #else:
    #        print("key not found in good list, assuming it's OK")
#
    # The IV is just zeroes.
    # If the IV is wrong, only the first block (16 bytes) will be decrypted incorrectly,
    # but that's bad enough for the decompression to fail
    zeroIv = b'\x00'*16

    assert len(key) == 16

    try:
        cipher = AES.new(key, AES.MODE_CBC, iv=zeroIv)
        decryptedString = cipher.decrypt(encryptedString)
    except:
        print("Got the key, but AES decryption failed. Make sure PyCryptodome or PyCrypto is installed.")
        return (False, encryptedString)

    assert len(decryptedString) == len(encryptedString)

    print("Found the AES key and decrypted the ROMs")

    return (True, decryptedString)
