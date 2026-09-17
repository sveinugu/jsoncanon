import os
import struct
from binascii import a2b_hex
from json import loads

import pytest
from jsoncanon import canonicalize

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'json-canonicalization', 'testdata')
INPUT_DIR = os.path.join(TESTDATA_DIR, 'input')
OUTPUT_DIR = os.path.join(TESTDATA_DIR, 'output')
OUTHEX_DIR = os.path.join(TESTDATA_DIR, 'outhex')
ES6_TESTFILE = os.path.join(TESTDATA_DIR, 'es6testfile10k.txt')

TEST_FILE_NAMES = sorted(os.listdir(INPUT_DIR))

INVALID_NUMBER = 'null'

# Fixed test vectors from json-canonicalization/test/verify-numbers.py
FIXED_VECTORS = [
    ('4340000000000001', '9007199254740994'),
    ('4340000000000002', '9007199254740996'),
    ('444b1ae4d6e2ef50', '1e+21'),
    ('3eb0c6f7a0b5ed8d', '0.000001'),
    ('3eb0c6f7a0b5ed8c', '9.999999999999997e-7'),
    ('8000000000000000', '0'),
    ('7fffffffffffffff', INVALID_NUMBER),
    ('7ff0000000000000', INVALID_NUMBER),
    ('fff0000000000000', INVALID_NUMBER),
]


def _read_file(path: str) -> str:
    with open(path, encoding='utf-8') as f:
        return f.read()


def _read_hex_file(path: str) -> bytes:
    return bytes.fromhex(_read_file(path))


@pytest.mark.parametrize('file_name', TEST_FILE_NAMES)
def test_json_canonicalization(file_name: str) -> None:
    json_data = _read_file(os.path.join(INPUT_DIR, file_name))

    actual = canonicalize(loads(json_data))

    # Canonicalizing an already-canonicalized document must be a no-op.
    recycled = canonicalize(loads(actual.decode('utf-8', 'strict')))

    expected = _read_file(os.path.join(OUTPUT_DIR, file_name)).encode()
    expected_hex = _read_hex_file(os.path.join(OUTHEX_DIR, os.path.splitext(file_name)[0] + '.txt'))

    assert actual == expected
    assert recycled == expected
    assert actual == expected_hex


def _ieee_hex_to_float(ieee_hex: str) -> float:
    parsed: float = struct.unpack('>d', a2b_hex(ieee_hex.rjust(16, '0')))[0]
    return parsed


def _verify_es6_number(ieee_hex: str, expected: str) -> None:
    value = _ieee_hex_to_float(ieee_hex)

    if expected == INVALID_NUMBER:
        with pytest.raises(ValueError):
            canonicalize(value)
        return

    actual = canonicalize(value).decode('utf8')

    assert actual == expected, f'IEEE: {ieee_hex}, Python: {actual}, Expected: {expected}'
    assert float(actual) == value


@pytest.mark.parametrize('ieee_hex, expected', FIXED_VECTORS)
def test_es6_number_fixed_vectors(ieee_hex: str, expected: str) -> None:
    _verify_es6_number(ieee_hex, expected)


def test_es6_number_testfile() -> None:
    with open(ES6_TESTFILE, encoding='utf-8') as f:
        for line in f:
            ieee_hex, expected = line.strip().split(',', 1)
            _verify_es6_number(ieee_hex, expected)
