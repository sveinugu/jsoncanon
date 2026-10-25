from importlib.metadata import version
from typing import cast

import pytest

from jsoncanon import (
    __version__,
    canonicalize,
    is_canonicalized,
    load_canonicalized,
    validate_canonicalized,
)
from jsoncanon.types import BigIntsOption


def test_version() -> None:
    assert __version__ == version('jsoncanon')


def test_canonicalize_whitespace() -> None:
    assert canonicalize({'a': [2, 3, 4, {'b': 2}, 3]}) == b'{"a":[2,3,4,{"b":2},3]}'


def test_canonicalize_literals() -> None:
    assert canonicalize(None) == b'null'
    assert canonicalize(True) == b'true'
    assert canonicalize(False) == b'false'


def test_canonicalize_strings() -> None:
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


def test_canonicalize_ints() -> None:
    assert canonicalize(0) == b'0'
    assert canonicalize(-0) == b'0'
    assert canonicalize(12345) == b'12345'
    assert canonicalize(-12345) == b'-12345'
    assert canonicalize(9007199254740991) == b'9007199254740991'


def test_canonicalize_big_ints_default() -> None:
    assert canonicalize(9007199254740992) == b'"9007199254740992"'
    assert canonicalize(9007199254740993) == b'"9007199254740993"'
    assert canonicalize(9223372036854775295) == b'"9223372036854775295"'
    assert canonicalize(9223372036854775296) == b'"9223372036854775296"'


def test_canonicalize_big_ints_as_string() -> None:
    assert canonicalize(9007199254740992, big_ints='as_string') == b'"9007199254740992"'
    assert canonicalize(9007199254740993, big_ints='as_string') == b'"9007199254740993"'
    assert canonicalize(9223372036854775295, big_ints='as_string') == b'"9223372036854775295"'
    assert canonicalize(9223372036854775296, big_ints='as_string') == b'"9223372036854775296"'


def test_canonicalize_big_ints_uniquely_as_string() -> None:
    assert canonicalize(9007199254740992, big_ints='uniquely_as_string') == b'"9007199254740992"'
    assert canonicalize(9007199254740993, big_ints='uniquely_as_string') == b'"9007199254740993"'
    assert (
        canonicalize(9223372036854775295, big_ints='uniquely_as_string') == b'"9223372036854775295"'
    )
    assert (
        canonicalize(9223372036854775296, big_ints='uniquely_as_string') == b'"9223372036854775296"'
    )

    # Disallow strings of big integers
    with pytest.raises(ValueError):
        canonicalize('9007199254740992', big_ints='uniquely_as_string')
    with pytest.raises(ValueError):
        canonicalize('9223372036854775296', big_ints='uniquely_as_string')

    # Allow strings of big integers starting with 0
    assert (
        canonicalize('09007199254740992', big_ints='uniquely_as_string') == b'"09007199254740992"'
    )

    # Allow non-ascii strings of big integers
    arabic_indic_big_int = '٩٠٠٧١٩٩٢٥٤٧٤٠٩٩٢'
    assert int(arabic_indic_big_int) == 9007199254740992
    assert canonicalize(arabic_indic_big_int, big_ints='uniquely_as_string') == (
        f'"{arabic_indic_big_int}"'.encode()
    )


def test_canonicalize_big_ints_as_float() -> None:
    assert canonicalize(9007199254740992, big_ints='as_float') == b'9007199254740992'
    assert canonicalize(9007199254740993, big_ints='as_float') == b'9007199254740992'
    assert canonicalize(9223372036854775295, big_ints='as_float') == b'9223372036854775000'
    assert canonicalize(9223372036854775296, big_ints='as_float') == b'9223372036854776000'


def test_canonicalize_big_ints_raise() -> None:
    with pytest.raises(ValueError):
        assert canonicalize(9007199254740992, big_ints='raise')
    with pytest.raises(ValueError):
        assert canonicalize(9007199254740993, big_ints='raise')
    with pytest.raises(ValueError):
        assert canonicalize(9223372036854775295, big_ints='raise')
    with pytest.raises(ValueError):
        assert canonicalize(9223372036854775295, big_ints='raise')


def test_canonicalize_floats() -> None:
    with pytest.raises(ValueError):
        assert canonicalize(float('nan'))
    with pytest.raises(ValueError):
        assert canonicalize(float('inf'))

    assert canonicalize(float(0)) == b'0'
    assert canonicalize(float(-0)) == b'0'

    assert canonicalize(float(9223372036854775295)) == b'9223372036854775000'
    assert canonicalize(float(9223372036854775296)) == b'9223372036854776000'
    assert canonicalize(float(9007199254740991)) == b'9007199254740991'
    assert canonicalize(float(9007199254740992)) == b'9007199254740992'
    assert canonicalize(float(9007199254740993)) == b'9007199254740992'

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


def test_canonicalize_sorting() -> None:
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


def test_validate_canonicalized() -> None:
    validate_canonicalized(b'{"a":1}')

    with pytest.raises(ValueError):
        validate_canonicalized(b'{"a": 1}')


def test_is_canonicalized() -> None:
    assert is_canonicalized(b'{"a":1}')
    assert not is_canonicalized(b'{"a": 1}')


def test_load_canonicalized_empty_containers() -> None:
    assert load_canonicalized(b'{}') == {}
    assert load_canonicalized(b'[]') == []


def test_load_canonicalized_scalars() -> None:
    assert load_canonicalized(b'1') == 1
    assert type(load_canonicalized(b'1')) is int

    assert load_canonicalized(b'1.5') == 1.5
    assert type(load_canonicalized(b'1.5')) is float

    assert load_canonicalized(b'"text"') == 'text'
    assert type(load_canonicalized(b'"text"')) is str

    assert load_canonicalized(b'true') is True
    assert load_canonicalized(b'false') is False
    assert load_canonicalized(b'null') is None


def test_load_canonicalized_nested_containers() -> None:
    loaded = load_canonicalized(b'{"a":[1,1.5,"text",{"b":2},null,true,false]}')
    assert loaded == {'a': [1, 1.5, 'text', {'b': 2}, None, True, False]}

    assert isinstance(loaded, dict)
    a = loaded['a']
    assert isinstance(a, list)
    assert type(a[0]) is int
    assert type(a[1]) is float
    assert type(a[2]) is str
    assert isinstance(a[3], dict)
    assert a[4] is None
    assert a[5] is True
    assert a[6] is False


def test_load_canonicalized_default_big_ints_is_as_string() -> None:
    assert load_canonicalized(b'"9007199254740992"') == '9007199254740992'
    assert load_canonicalized(b'9007199254740992') == 9007199254740992.0


@pytest.mark.parametrize('big_ints', ['as_string', 'uniquely_as_string', 'as_float', 'raise'])
def test_load_canonicalized_bare_numbers_are_mode_independent(big_ints: BigIntsOption) -> None:
    # A safe bare integer always parses as int. A bare integer-looking token
    # beyond the ES6 safe-integer bound only ever comes from a genuine float
    # (application-level big integers are always quoted), so it round-trips
    # as a float identically in every big_ints mode.
    assert load_canonicalized(b'1', big_ints=big_ints) == 1
    assert type(load_canonicalized(b'1', big_ints=big_ints)) is int

    loaded_big = load_canonicalized(b'9007199254740992', big_ints=big_ints)
    assert loaded_big == 9007199254740992.0
    assert type(loaded_big) is float


@pytest.mark.parametrize('sign', ['', '-'])
@pytest.mark.parametrize(
    ('big_ints', 'restores_to_int'),
    [
        ('as_string', False),
        ('as_float', False),
        ('raise', False),
        ('uniquely_as_string', True),
    ],
)
def test_load_canonicalized_quoted_big_int_string(
    sign: str, big_ints: BigIntsOption, restores_to_int: bool
) -> None:
    # A quoted canonical big-int string is only restored to a Python int by
    # 'uniquely_as_string'; every other mode leaves it as a plain string.
    token = f'{sign}9007199254740992'
    expected: str | int = int(token) if restores_to_int else token
    assert load_canonicalized(f'"{token}"'.encode(), big_ints=big_ints) == expected


def test_load_canonicalized_uniquely_as_string_restores_values_not_keys() -> None:
    # Only values are restored to integers; dict keys remain strings.
    assert load_canonicalized(
        b'{"9007199254740992":"9007199254740992"}', big_ints='uniquely_as_string'
    ) == {'9007199254740992': 9007199254740992}


def test_load_canonicalized_rejects_invalid_constants() -> None:
    for token in (b'NaN', b'Infinity', b'-Infinity'):
        with pytest.raises(ValueError):
            load_canonicalized(token)


def test_load_canonicalized_validates_accepted_edge_cases() -> None:
    assert load_canonicalized(b'{"\\r":0,"1":0,"\xc2\x80":0,"\xc3\xb6":0,"\xe2\x82\xac":0}') == {
        '\r': 0,
        '1': 0,
        '\x80': 0,
        'ö': 0,
        '€': 0,
    }
    assert load_canonicalized(b'"\\b\\t\\n\\u000b\\f\\r"') == '\b\t\n\x0b\f\r'
    assert load_canonicalized(b'1e+21') == 1e21


def test_load_canonicalized_rejects_noncanonical_input_unless_validation_is_disabled() -> None:
    cases = [
        (b'{"a": 1}', {'a': 1}),
        (b'{"b":1,"a":2}', {'b': 1, 'a': 2}),
        (b'{"a":1,"a":2}', {'a': 2}),
        (b'"\\u0041"', 'A'),
        (b'1.0', 1.0),
        (b'1e5', 100000.0),
    ]
    for data, expected in cases:
        with pytest.raises(ValueError):
            load_canonicalized(data)
        assert load_canonicalized(data, validate_func=None) == expected


def test_load_canonicalized_str_input() -> None:
    data = cast(bytes, '{"number":1}')
    with pytest.raises(TypeError):
        load_canonicalized(data)

    assert load_canonicalized(data, validate_func=None) == {'number': 1}
