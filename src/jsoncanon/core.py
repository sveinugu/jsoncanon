import json
from typing import cast, overload

from jsoncanon.encoder import FinalJsonEncoder
from jsoncanon.functions import (
    big_int_as_float,
    big_int_as_str,
    dict_to_sorted_by_utf16_tuple,
    float_to_final_es6_str,
    raise_if_big_int,
)
from jsoncanon.preprocess import (
    JsonDataPreprocessor,
)
from jsoncanon.types import (
    BigIntsOption,
    JsonScalar,
    JsonWithTuple,
    JsonWithTupleT,
    PreprocInputFunc,
)


@overload
def canonicalize(
    data: dict[str, JsonWithTupleT], big_ints: BigIntsOption = 'as_string'
) -> bytes: ...


@overload
def canonicalize(data: list[JsonWithTupleT], big_ints: BigIntsOption = 'as_string') -> bytes: ...


@overload
def canonicalize(
    data: tuple[JsonWithTupleT, ...], big_ints: BigIntsOption = 'as_string'
) -> bytes: ...


@overload
def canonicalize(data: JsonScalar, big_ints: BigIntsOption = 'as_string') -> bytes: ...


@overload
def canonicalize(data: JsonWithTuple, big_ints: BigIntsOption = 'as_string') -> bytes: ...


def canonicalize(data: object, big_ints: BigIntsOption = 'as_string') -> bytes:
    return _canonicalize(cast(JsonWithTuple, data), big_ints)


_common_preproc_funcs: list[PreprocInputFunc] = [
    float_to_final_es6_str,
    dict_to_sorted_by_utf16_tuple,
]


_preprocess_big_ints_as_str = JsonDataPreprocessor([big_int_as_str] + _common_preproc_funcs)

_preprocess_raise_on_big_ints = JsonDataPreprocessor([raise_if_big_int] + _common_preproc_funcs)

_preprocess_allow_big_ints = JsonDataPreprocessor([big_int_as_float] + _common_preproc_funcs)


def _select_preprocessor(big_ints: BigIntsOption) -> JsonDataPreprocessor:
    match big_ints:
        case 'as_string':
            return _preprocess_big_ints_as_str
        case 'as_float':
            return _preprocess_allow_big_ints
        case 'raise':
            return _preprocess_raise_on_big_ints


def _canonicalize(data: JsonWithTuple, big_ints: BigIntsOption) -> bytes:
    preprocess = _select_preprocessor(big_ints)
    output = json.dumps(
        preprocess(data),
        separators=(',', ':'),
        ensure_ascii=False,
        allow_nan=False,
        cls=FinalJsonEncoder,
    )
    return output.encode('utf8')
