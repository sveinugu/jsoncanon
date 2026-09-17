from jsoncanon.functions import (
    dict_to_sorted_by_utf16_tuple,
    float_to_final_es6_str,
    int_to_str_if_too_large,
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


def test_int_to_str_if_too_large() -> None:
    assert int_to_str_if_too_large(9007199254740992) == 9007199254740992
    assert type(int_to_str_if_too_large(9007199254740992)) is int

    assert int_to_str_if_too_large(-9007199254740992) == -9007199254740992
    assert type(int_to_str_if_too_large(-9007199254740992)) is int

    assert int_to_str_if_too_large(9007199254740993) == '9007199254740993'
    assert type(int_to_str_if_too_large(9007199254740993)) is str

    assert int_to_str_if_too_large(-9007199254740993) == '-9007199254740993'
    assert type(int_to_str_if_too_large(-9007199254740993)) is str


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
