import binascii
import sys

password = int(sys.argv[1],16)
#password = bytes(binascii.a2b_hex(password))

bytesarraytosend = bytearray(b'testchiffrement')

print("A chiffrer : " + bytesarraytosend.decode())

for i in range(len(bytesarraytosend)):
    print("Element {} to cipher : {}".format(i, bytesarraytosend[i]))
    bytesarraytosend[i] ^= password

print("Chiffré : " + str(bytesarraytosend))

for i in range(len(bytesarraytosend)):
    print("Element {} to decipher : {}".format(i, bytesarraytosend[i]))
    bytesarraytosend[i] ^= password

print("Déchiffré : " + bytesarraytosend.decode())
