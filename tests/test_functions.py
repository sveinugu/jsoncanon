import pytest
from jsoncanon.functions import (
    big_int_as_float,
    big_int_as_str,
    dict_to_sorted_by_utf16_tuple,
    float_to_es6_str,
    float_to_final_es6_str,
    is_canonical_big_int_string,
    is_es6_safe_integer,
    parse_canonical_int,
    raise_if_big_int,
    raise_if_big_int_string,
    restore_unique_big_int_strings,
    to_utf16_tuple,
)
from jsoncanon.preprocess import JsonDataPreprocessor
from jsoncanon.types import FinalJson, JsonWithFinal, JsonWithTuple


def test_float_to_final_es6_str() -> None:
    rendered = float_to_final_es6_str(1e21)
    assert rendered == '1e+21'
    assert type(rendered) is FinalJson


def test_float_to_es6_str() -> None:
    assert float_to_es6_str(333333333.33333329) == '333333333.3333333'
    assert float_to_es6_str(1e30) == '1e+30'
    assert float_to_es6_str(4.50) == '4.5'
    assert float_to_es6_str(2e-3) == '0.002'
    assert float_to_es6_str(0.000000000000000000000000001) == '1e-27'
    assert float_to_es6_str(float(9007199254740992)) == '9007199254740992'
    assert float_to_es6_str(float(9007199254740993)) == '9007199254740992'
    assert float_to_es6_str(float(9223372036854775295)) == '9223372036854775000'


def test_big_int_as_str() -> None:
    assert big_int_as_str(9007199254740991) == 9007199254740991
    assert type(big_int_as_str(9007199254740991)) is int

    assert big_int_as_str(-9007199254740991) == -9007199254740991
    assert type(big_int_as_str(-9007199254740991)) is int

    assert big_int_as_str(9007199254740992) == '9007199254740992'
    assert type(big_int_as_str(9007199254740992)) is str

    assert big_int_as_str(-9007199254740992) == '-9007199254740992'
    assert type(big_int_as_str(-9007199254740992)) is str


def test_is_es6_safe_integer() -> None:
    assert is_es6_safe_integer(9007199254740991)
    assert is_es6_safe_integer(-9007199254740991)
    assert not is_es6_safe_integer(9007199254740992)
    assert not is_es6_safe_integer(-9007199254740992)


def test_big_int_as_float() -> None:
    assert big_int_as_float(9007199254740991) == 9007199254740991
    assert big_int_as_float(-9007199254740991) == -9007199254740991
    assert big_int_as_float(9007199254740992) == '9007199254740992'
    assert big_int_as_float(-9007199254740992) == '-9007199254740992'
    assert big_int_as_float(9223372036854775295) == '9223372036854775000'
    assert big_int_as_float(-9223372036854775295) == '-9223372036854775000'
    assert big_int_as_float(9223372036854775296) == '9223372036854776000'
    assert big_int_as_float(-9223372036854775296) == '-9223372036854776000'


def test_is_canonical_big_int_string() -> None:
    assert is_canonical_big_int_string('9007199254740992')
    assert is_canonical_big_int_string('-9007199254740992')

    assert not is_canonical_big_int_string('9007199254740991')
    assert not is_canonical_big_int_string('-9007199254740991')
    assert not is_canonical_big_int_string('09007199254740992')
    assert not is_canonical_big_int_string('+9007199254740992')
    assert not is_canonical_big_int_string('1e20')

    arabic_indic_big_int = '٩٠٠٧١٩٩٢٥٤٧٤٠٩٩٢'
    assert int(arabic_indic_big_int) == 9007199254740992
    assert not is_canonical_big_int_string(arabic_indic_big_int)


def test_raise_if_big_int_string() -> None:
    with pytest.raises(ValueError):
        raise_if_big_int_string('9007199254740992')

    assert raise_if_big_int_string('9007199254740991')
    assert raise_if_big_int_string('09007199254740992')

    arabic_indic_big_int = '٩٠٠٧١٩٩٢٥٤٧٤٠٩٩٢'
    assert raise_if_big_int_string(arabic_indic_big_int) == arabic_indic_big_int


def test_raise_if_big_int() -> None:
    assert raise_if_big_int(9007199254740991) == 9007199254740991
    assert type(raise_if_big_int(9007199254740991)) is int

    assert raise_if_big_int(-9007199254740991) == -9007199254740991
    assert type(raise_if_big_int(-9007199254740991)) is int

    with pytest.raises(ValueError):
        raise_if_big_int(9007199254740992)

    with pytest.raises(ValueError):
        raise_if_big_int(-9007199254740992)


def test_to_utf16_tuple() -> None:
    assert to_utf16_tuple('€') == (8364,)
    assert to_utf16_tuple('1') == (49,)
    assert to_utf16_tuple('\r') == (13,)
    assert to_utf16_tuple('דּ') == (64307,)
    assert to_utf16_tuple('😀') == (55357, 56832)
    assert to_utf16_tuple('\x80') == (128,)
    assert to_utf16_tuple('ö') == (246,)
    assert to_utf16_tuple('€1\rדּ😀\x80ö') == (8364, 49, 13, 64307, 55357, 56832, 128, 246)


def test_to_utf16_tuple_cache() -> None:
    to_utf16_tuple.cache_clear()
    assert to_utf16_tuple('€') == (8364,)
    to_utf16_tuple('€')
    assert to_utf16_tuple.cache_info().hits == 1


def test_dict_to_sorted_by_utf16_tuple() -> None:
    assert dict_to_sorted_by_utf16_tuple({'b': 2, 'a': 1}) == {'a': 1, 'b': 2}
    assert dict_to_sorted_by_utf16_tuple({'😀דּ': 2, 'דּ😀': 1}) == {'דּ😀': 1, '😀דּ': 2}


def test_dict_to_sorted_by_utf16_tuple_recursive() -> None:
    def dict_to_sorted_by_utf16_tuple_recursive(data: JsonWithTuple) -> JsonWithFinal:
        _dict_to_sorted_by_utf16_tuple_recursive = JsonDataPreprocessor(
            [dict_to_sorted_by_utf16_tuple]
        )
        return _dict_to_sorted_by_utf16_tuple_recursive(data)

    assert dict_to_sorted_by_utf16_tuple_recursive(
        {
            'b': {'d': 3, 'c': 2},
            'a': 1,
        }
    ) == {
        'b': {'c': 2, 'd': 3},
        'a': 1,
    }
    assert dict_to_sorted_by_utf16_tuple_recursive(
        {
            'a': [{'😀דּ': 3, 'דּ😀': 2}, 4],
            'b': 2,
        }
    ) == {
        'a': [{'דּ😀': 2, '😀דּ': 3}, 4],
        'b': 2,
    }


def test_parse_canonical_int() -> None:
    assert parse_canonical_int('9007199254740991') == 9007199254740991
    assert type(parse_canonical_int('9007199254740991')) is int

    assert parse_canonical_int('9007199254740992') == 9007199254740992.0
    assert type(parse_canonical_int('9007199254740992')) is float

    assert parse_canonical_int('-9007199254740992') == -9007199254740992.0
    assert type(parse_canonical_int('-9007199254740992')) is float


def test_restore_unique_big_int_strings() -> None:
    assert restore_unique_big_int_strings('9007199254740992') == 9007199254740992
    assert type(restore_unique_big_int_strings('9007199254740992')) is int

    assert restore_unique_big_int_strings('9007199254740991') == '9007199254740991'
    assert type(restore_unique_big_int_strings('9007199254740991')) is str

    assert restore_unique_big_int_strings(
        {'a': '9007199254740992', 'b': [1, '9007199254740992', 'x']}
    ) == {'a': 9007199254740992, 'b': [1, 9007199254740992, 'x']}

    assert restore_unique_big_int_strings(1) == 1
    assert restore_unique_big_int_strings(None) is None
