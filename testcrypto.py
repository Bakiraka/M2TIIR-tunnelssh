import binascii

password = '8a'
password = bytes(binascii.a2b_hex(password))

bytesarraytosend = bytearray(b'testchiffrement')

print("A chiffrer : " + bytesarraytosend.decode())

for i in range(len(bytesarraytosend)):
    bytesarraytosend[i] ^= password

print("Chiffré : " + bytesarraytosend.decode())

for i in range(len(bytesarraytosend)):
    bytesarraytosend[i] ^= password

print("Déchiffré : " + bytesarraytosend.decode())
