import pytest
from jsoncanon.functions import (
    big_int_as_float,
    big_int_as_str,
    dict_to_sorted_by_utf16_tuple,
    float_to_final_es6_str,
    raise_if_big_int,
    to_utf16_tuple,
)
from jsoncanon.preprocess import JsonDataPreprocessor
from jsoncanon.types import FinalJson, JsonWithFinal, JsonWithTuple


def test_float_to_final_es6_str() -> None:
    assert float_to_final_es6_str(333333333.33333329) == FinalJson('333333333.3333333')
    assert float_to_final_es6_str(1e30) == FinalJson('1e+30')
    assert float_to_final_es6_str(4.50) == FinalJson('4.5')
    assert float_to_final_es6_str(2e-3) == FinalJson('0.002')
    assert float_to_final_es6_str(0.000000000000000000000000001) == FinalJson('1e-27')
    assert float_to_final_es6_str(float(9007199254740992)) == FinalJson('9007199254740992')
    assert float_to_final_es6_str(float(9007199254740993)) == FinalJson('9007199254740992')
    assert float_to_final_es6_str(float(9223372036854775295)) == FinalJson('9223372036854775000')


def test_big_int_as_str() -> None:
    assert big_int_as_str(9007199254740991) == 9007199254740991
    assert type(big_int_as_str(9007199254740991)) is int

    assert big_int_as_str(-9007199254740991) == -9007199254740991
    assert type(big_int_as_str(-9007199254740991)) is int

    assert big_int_as_str(9007199254740992) == '9007199254740992'
    assert type(big_int_as_str(9007199254740992)) is str

    assert big_int_as_str(-9007199254740992) == '-9007199254740992'
    assert type(big_int_as_str(-9007199254740992)) is str


def test_big_int_as_float() -> None:
    assert big_int_as_float(9007199254740991) == 9007199254740991
    assert big_int_as_float(-9007199254740991) == -9007199254740991
    assert big_int_as_float(9007199254740992) == '9007199254740992'
    assert big_int_as_float(-9007199254740992) == '-9007199254740992'
    assert big_int_as_float(9223372036854775295) == '9223372036854775000'
    assert big_int_as_float(-9223372036854775295) == '-9223372036854775000'
    assert big_int_as_float(9223372036854775296) == '9223372036854776000'
    assert big_int_as_float(-9223372036854775296) == '-9223372036854776000'


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
