# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from text_unidecode import unidecode
import pytest


@pytest.mark.parametrize(("text", "result"), [
    ("Programmes de publicité - Solutions d'entreprise", "Programmes de publicite - Solutions d'entreprise"),
    ("Транслитерирует и русский", "Transliteriruet i russkii"),
    ("kožušček", "kozuscek"),
    ("北亰", "Bei Jing "),
])
def test_transliterate(text, result):
    assert unidecode(text) == result


@pytest.mark.parametrize("code", range(128))
def test_7bit_purity(code):
    ch = chr(code)
    assert unidecode(ch) == ch


def test_7bit_text_purity():
    txt = "".join([chr(x) for x in range(128)])
    assert unidecode(txt) == txt


@pytest.fixture
def fresh(monkeypatch):
    import text_unidecode
    monkeypatch.setattr(text_unidecode, '_blocks', {})
    monkeypatch.setattr(text_unidecode, '_index', None)
    monkeypatch.setattr(text_unidecode, '_replaces', None)
    return text_unidecode


def test_ascii_loads_nothing(fresh):
    assert unidecode("plain ascii") == "plain ascii"
    if fresh._HAS_ISASCII:
        assert fresh._blocks == {}
        assert fresh._replaces is None


def test_only_touched_blocks_loaded(fresh):
    text = "kožušček 北亰"
    assert unidecode(text) == "kozuscek Bei Jing "
    block_size = 1 << fresh._load_index()[0]
    assert set(fresh._blocks) == set((ord(ch) - 1) // block_size for ch in text)
    assert fresh._replaces is None


def test_index_matches_data():
    import pkgutil
    import struct
    import _make_index
    raw = pkgutil.get_data('text_unidecode', 'data.idx')
    data = pkgutil.get_data('text_unidecode', 'data.bin')
    block_size = struct.unpack_from('<I', raw)[0]
    assert raw == _make_index.build_index(data, block_size)


def test_fallback_without_data_file_on_disk(fresh, monkeypatch):
    monkeypatch.setattr(fresh, '_DATA_PATH', fresh._DATA_PATH + '.missing')
    assert unidecode("kožušček 北亰") == "kozuscek Bei Jing "
    assert fresh._index is False
    assert fresh._blocks == {}
    assert fresh._replaces is not None


def test_end_of_table(fresh):
    assert unidecode("a￾￿b") == unidecode("a￾") + "b"
