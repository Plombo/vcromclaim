#!/usr/bin/env python3

from neogeo_keys import keys
from binascii import unhexlify

try:
    from Crypto.Cipher import AES
except:
    pass

# titleIdString must be the 8 byte string identifying each Wii title, e.g. '421a2b3c'
# fileString input must be a string containing the content of the encrypted romfile, starting with CR00.
# will return a tuple - either (true, decryptedData) or (false, encryptedData)
# note that the decryptedData will still be compressed (zipped), similar to some other neo geo games without encryption.
def decrypt_neogeo(titleIdString, fileString):
    # encrypted files starts with a magic word
    assert fileString[0:4] == b'CR00'

    # ignore the next 16 bytes. The CR00 magic word and these 16 bytes are used to reconstruct the encryption key,
    # together with many other data which we don't have.

    # the rest of the files is AES-CBC-128 encrypted. as such it consists of 16 byte (128bit) blocks. 
    assert (len(fileString) - 4) % 16 == 0

    # The rest is the ecnrypted data
    encryptedString = fileString[4+16:]
    assert len(fileString) == 4+16+len(encryptedString)

    if (titleIdString in keys):

        # The IV is just zeroes.
        # If the IV is wrong, only the first block (16 bytes) will be decrypted incorrectly,
        # but that's bad enough for the decompression to fail
        zeroIv = b'\x00'*16

        key = unhexlify(keys[titleIdString])
        assert len(key) == 16

        try:
            cipher = AES.new(key, AES.MODE_CBC, iv=zeroIv)
            decryptedString = cipher.decrypt(encryptedString)
        except:
            print("Decryption failed. Make sure PyCryptodome or PyCrypto is installed.")
            return (False, encryptedString)

        assert len(decryptedString) == len(encryptedString)

        print("Decrypted ROMs")

        return (True, decryptedString)
    else:
        print("No encryption key found for the title, see Readme about how to get the key")
        return (False, encryptedString)
