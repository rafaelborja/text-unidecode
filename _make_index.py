#!/usr/bin/env python
"""Write src/text_unidecode/data.idx, the block offset index for data.bin.

data.bin holds one NUL-terminated replacement per codepoint, starting at U+0001.
The index lets text_unidecode read only the blocks of codepoints it needs.

Layout, all little-endian uint32:
    block size, size of data.bin in bytes, then one byte offset per block
    (where that block's first entry starts), then the size of data.bin again.

Re-run after regenerating data.bin with _dump.pl:
    python _make_index.py

The block size must be a power of 2.
"""
import os
import struct

BLOCK_SIZE = 256

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, 'src', 'text_unidecode')


def build_index(data, block_size=BLOCK_SIZE):
    assert block_size > 0 and block_size & (block_size - 1) == 0, 'block size must be a power of 2'
    offsets = [0]
    count = 0
    for pos, byte in enumerate(bytearray(data)):
        if byte == 0:
            count += 1
            if count % block_size == 0:
                offsets.append(pos + 1)
    if offsets[-1] == len(data):
        offsets.pop()
    offsets.append(len(data))
    return struct.pack('<%dI' % (len(offsets) + 2), block_size, len(data), *offsets)


def main():
    with open(os.path.join(PKG, 'data.bin'), 'rb') as f:
        data = f.read()
    with open(os.path.join(PKG, 'data.idx'), 'wb') as f:
        f.write(build_index(data))


if __name__ == '__main__':
    main()
