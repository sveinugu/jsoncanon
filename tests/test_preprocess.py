from enum import IntEnum
from types import MappingProxyType
from typing import Annotated

import pytest

from jsoncanon.preprocess import JsonDataPreprocessor
from jsoncanon.types import FinalJson, JsonWithFinal, JsonWithTuple, PreprocFunc


def invalid_preproc_func_two_params(_i: int, _s: str) -> str: ...  # type: ignore[empty-body]


def invalid_preproc_func_one_param_pos_or_keyword(_s: str) -> str: ...  # type: ignore[empty-body]


def invalid_preproc_func_one_param_no_annotation(_s) -> str: ...  # type: ignore[empty-body, no-untyped-def]


def invalid_preproc_func_no_return_annotation(_s) -> str: ...  # type: ignore[empty-body, no-untyped-def]


@pytest.mark.parametrize(
    'preproc_func',
    [  # pyright: ignore[reportUnknownArgumentType]
        invalid_preproc_func_two_params,
        invalid_preproc_func_one_param_pos_or_keyword,
        invalid_preproc_func_one_param_no_annotation,
        invalid_preproc_func_no_return_annotation,
    ],
)
def test_json_preprocessor_valid_funcs(preproc_func: PreprocFunc) -> None:
    with pytest.raises(AssertionError):
        JsonDataPreprocessor([preproc_func])


@pytest.fixture
def json_data_preprocessor() -> JsonDataPreprocessor:
    def str_upper_func(s: str, /) -> str:
        return s.upper()

    def int_increase_func(i: int, /) -> int:
        return i + 1

    def float_halve_func(f: float, /) -> float:
        return f / 2

    def float_to_raw_json_func(f: float, /) -> FinalJson:
        return FinalJson(str(f))

    def bool_invert_func(b: bool, /) -> bool:
        return not b

    def none_to_raw_json_func(n: None, /) -> FinalJson:
        return FinalJson(str(n))

    def dict_upper_keys_func(d: dict[str, JsonWithFinal], /) -> dict[str, JsonWithFinal]:
        return {key.upper(): val for key, val in d.items()}

    def list_reverse_func(li: list[JsonWithFinal], /) -> list[JsonWithFinal]:
        return [_ for _ in reversed(li)]

    return JsonDataPreprocessor(
        [
            str_upper_func,
            int_increase_func,
            float_halve_func,
            float_to_raw_json_func,
            bool_invert_func,
            none_to_raw_json_func,
            dict_upper_keys_func,
            list_reverse_func,
        ]
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
                'KEY_1': [FinalJson('None'), True, FinalJson('2.5'), 4, 'STRING'],
                'KEY_2': [FinalJson('None'), False, FinalJson('3.0'), 6, 'CONTENT'],
            },
            FinalJson('None'),
            False,
            FinalJson('1.0'),
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
