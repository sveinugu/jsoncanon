import pytest
from jsoncanon import __version__, canonicalize


def test_version() -> None:
    assert __version__ == '0.2.3'


def test_whitespace() -> None:
    assert canonicalize({'a': [2, 3, 4, {'b': 2}, 3]}) == b'{"a":[2,3,4,{"b":2},3]}'


def test_literals() -> None:
    assert canonicalize(None) == b'null'
    assert canonicalize(True) == b'true'
    assert canonicalize(False) == b'false'


def test_strings() -> None:
    for c in range(8):
        assert canonicalize(chr(c)) == b'"\\u00%(c)02x"' % {b'c': c}

    assert canonicalize(chr(8)) == b'"\\b"'

    assert canonicalize(chr(9)) == b'"\\t"'

    assert canonicalize(chr(10)) == b'"\\n"'

    assert canonicalize(chr(11)) == b'"\\u000b"'

    assert canonicalize(chr(12)) == b'"\\f"'

    assert canonicalize(chr(13)) == b'"\\r"'

    for c in range(14, 32):
        assert canonicalize(chr(c)) == b'"\\u00%(c)02x"' % {b'c': c}

    assert canonicalize(chr(32)) == b'" "'

    for c in range(35, 92):
        assert canonicalize(chr(c)) == bytes(f'"{chr(c)}"', 'utf8')

    assert canonicalize(chr(92)) == b'"\\\\"'

    for c in range(93, 55296):
        assert canonicalize(chr(c)) == bytes(f'"{chr(c)}"', 'utf8')

    for c in range(55296, 57344):
        with pytest.raises(UnicodeEncodeError):
            canonicalize(chr(c))

    for c in range(57344, 65536):
        assert canonicalize(chr(c)) == bytes(f'"{chr(c)}"', 'utf8')

    assert canonicalize('€') == bytes('"€"', 'utf8')
    assert canonicalize('דּ') == bytes('"דּ"', 'utf8')
    assert canonicalize('😀') == bytes('"😀"', 'utf8')
    assert canonicalize('\x80') == bytes('"\x80"', 'utf8')
    assert canonicalize('ö') == bytes('"ö"', 'utf8')


def test_numbers() -> None:
    with pytest.raises(ValueError):
        assert canonicalize(float('nan'))
    with pytest.raises(ValueError):
        assert canonicalize(float('inf'))

    assert canonicalize(float(9223372036854775295)) == b'9223372036854775000'
    assert canonicalize(float(9223372036854775296)) == b'9223372036854776000'
    assert canonicalize(float(9007199254740992)) == b'9007199254740992'
    assert canonicalize(float(9007199254740993)) == b'9007199254740992'
    assert canonicalize(9007199254740992) == b'9007199254740992'
    assert canonicalize(9007199254740993) == b'"9007199254740993"'
    assert canonicalize(56.0) == b'56'
    assert canonicalize(1e20) == b'100000000000000000000'
    assert canonicalize(1e21) == b'1e+21'
    assert canonicalize(1e-6) == b'0.000001'

    # ECMAScript Number::toString: exponents carry no leading zero, and the
    # positional form is used across the whole [1e-6, 1e21) range.
    assert canonicalize(1e-7) == b'1e-7'
    assert canonicalize(1e-5) == b'0.00001'
    assert canonicalize(5e-324) == b'5e-324'

    # shortest round-trip: the text must parse back to the same double.
    assert canonicalize(0.1 + 0.2) == b'0.30000000000000004'


def test_sorting() -> None:
    in_data = {
        '€': 'Euro Sign',
        '\r': 'Carriage Return',
        'דּ': 'Hebrew Letter Dalet With Dagesh',
        '1': 'One',
        '😀': 'Emoji: Grinning Face',
        '\x80': 'Control',
        'ö': 'Latin Small Letter O With Diaeresis',
    }

    out_data = bytes(
        '{"\\r":"Carriage Return",'
        '"1":"One",'
        '"\u0080":"Control",'
        '"ö":"Latin Small Letter O With Diaeresis",'
        '"€":"Euro Sign",'
        '"😀":"Emoji: Grinning Face",'
        '"דּ":"Hebrew Letter Dalet With Dagesh"}',
        'utf8',
    )

    assert canonicalize(in_data) == out_data
