# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
import os
import pkgutil
import struct

# data.bin holds one NUL-terminated replacement per codepoint from U+0001.
# Decoded whole it is ~3 MB, so only the blocks of codepoints actually used are
# read from disk, through the offset index in data.idx (see _make_index.py).
_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.bin')

_blocks = {}
_index = None
# The whole table; only loaded when data.bin can't be read in blocks from disk
# (e.g. a zipped install) or data.idx doesn't match it.
_replaces = None

# 7-bit ASCII maps to itself, so it never needs the table (Python 3.7+).
_HAS_ISASCII = hasattr(str, 'isascii')


def _load_index():
    global _index
    if _index is None:
        index = False
        try:
            raw = pkgutil.get_data(__name__, 'data.idx')
            block_size, size = struct.unpack_from('<2I', raw)
            offsets = struct.unpack_from('<%dI' % (len(raw) // 4 - 2), raw, 8)
            shift = block_size.bit_length() - 1
            if (block_size == 1 << shift and len(offsets) > 1 and offsets[-1] == size
                    and os.path.getsize(_DATA_PATH) == size):
                index = (shift, offsets)
        except (IOError, OSError, struct.error, TypeError, ValueError):
            pass
        _index = index
    return _index


def _get_replaces():
    global _replaces
    if _replaces is None:
        _replaces = pkgutil.get_data(__name__, 'data.bin').decode('utf8').split('\x00')
    return _replaces


def _read_block(number, offsets):
    start, end = offsets[number], offsets[number + 1]
    with open(_DATA_PATH, 'rb') as f:
        f.seek(start)
        data = f.read(end - start)
    # Like the full-table split, this ends with an extra '' after the last NUL,
    # which is never reached except in the final block.
    return data.decode('utf8').split('\x00')


def unidecode(txt):
    if _HAS_ISASCII and type(txt) is str and txt.isascii():
        return txt
    index = _load_index()
    if not index:
        return _unidecode_whole_table(txt)
    shift, offsets = index
    mask = (1 << shift) - 1
    last_block = len(offsets) - 2
    blocks = _blocks
    chars = []
    append = chars.append
    for ch in txt:
        codepoint = ord(ch)

        if not codepoint:
            append('\x00')
            continue

        i = codepoint - 1
        try:
            append(blocks[i >> shift][i & mask])
        except KeyError:
            number = i >> shift
            if number > last_block:
                continue
            block = blocks[number] = _read_block(number, offsets)
            try:
                append(block[i & mask])
            except IndexError:
                pass
        except IndexError:
            pass
    return "".join(chars)


def _unidecode_whole_table(txt):
    replaces = _get_replaces()
    chars = []
    for ch in txt:
        codepoint = ord(ch)

        if not codepoint:
            chars.append('\x00')
            continue

        try:
            chars.append(replaces[codepoint-1])
        except IndexError:
            pass
    return "".join(chars)
