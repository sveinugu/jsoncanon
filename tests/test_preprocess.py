from enum import IntEnum
from types import MappingProxyType
from typing import Annotated

import pytest

from jsoncanon.preprocess import JsonDataPreprocessor
from jsoncanon.types import FinalJson, JsonWithFinal, JsonWithTuple


@pytest.fixture
def json_data_preprocessor() -> JsonDataPreprocessor:
    def str_upper_func(s: str, /) -> str:
        return s.upper()

    def int_increase_func(i: int, /) -> int:
        return i + 1

    def float_halve_func(f: float, /) -> float:
        return f / 2

    def bool_invert_func(b: bool, /) -> bool:
        return not b

    def none_to_raw_json_func(n: None, /) -> FinalJson:
        return FinalJson(str(n))

    def dict_upper_keys_func(d: dict[str, JsonWithFinal], /) -> dict[str, JsonWithFinal]:
        return {key.upper(): val for key, val in d.items()}

    def list_reverse_func(li: list[JsonWithFinal], /) -> list[JsonWithFinal]:
        return [_ for _ in reversed(li)]

    return JsonDataPreprocessor(
        {
            'str': str_upper_func,
            'int': int_increase_func,
            'float': float_halve_func,
            'bool': bool_invert_func,
            'NoneType': none_to_raw_json_func,
            'dict': dict_upper_keys_func,
            'list': list_reverse_func,
        }
    )


def test_preprocess_json_data_core_types(
    json_data_preprocessor: Annotated[JsonDataPreprocessor, pytest.fixture],
) -> None:
    data: JsonWithTuple = {
        'outer_key': [
            'text',
            1,
            2.0,
            True,
            None,
            {
                'key_1': ['string', 3, 5.0, False, None],
                'key_2': ['content', 5, 6.0, True, None],
            },
            (True, False, 'maybe'),
        ],
    }
    assert json_data_preprocessor(
        data,
    ) == {
        'OUTER_KEY': [
            ['MAYBE', True, False],
            {
                'KEY_1': [FinalJson('None'), True, 2.5, 4, 'STRING'],
                'KEY_2': [FinalJson('None'), False, 3.0, 6, 'CONTENT'],
            },
            FinalJson('None'),
            False,
            1.0,
            2,
            'TEXT',
        ],
    }


def test_preprocess_json_data_int_enum(
    json_data_preprocessor: Annotated[JsonDataPreprocessor, pytest.fixture],
) -> None:
    class Choice(IntEnum):
        Yes = 1
        No = 0

    assert json_data_preprocessor([Choice.Yes, Choice.No]) == [1, 2]


@pytest.mark.parametrize(
    'data',
    [
        b'bytes',
        {1, 2, 3},
        MappingProxyType({'a': 1, 'b': 2}),
        range(3),
        (_ for _ in range(3)),
    ],
    ids=['bytes', 'set', 'mapping_proxy', 'range', 'generator'],
)
def test_preprocess_json_incorrect_data(
    json_data_preprocessor: Annotated[JsonDataPreprocessor, pytest.fixture],
    data: object,
) -> None:
    with pytest.raises(TypeError):
        assert json_data_preprocessor(data)  # type: ignore[call-overload]
