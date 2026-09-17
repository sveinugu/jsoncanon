import json
from typing import cast, overload

from jsoncanon.encoder import FinalJsonEncoder
from jsoncanon.functions import (
    dict_to_sorted_by_utf16_tuple,
    float_to_final_es6_str,
    int_to_str_if_too_large,
)
from jsoncanon.preprocess import (
    JsonDataPreprocessor,
)
from jsoncanon.types import JsonScalar, JsonWithTuple, JsonWithTupleT


@overload
def canonicalize(data: dict[str, JsonWithTupleT]) -> bytes: ...


@overload
def canonicalize(data: list[JsonWithTupleT]) -> bytes: ...


@overload
def canonicalize(data: tuple[JsonWithTupleT, ...]) -> bytes: ...


@overload
def canonicalize(data: JsonScalar) -> bytes: ...


@overload
def canonicalize(data: JsonWithTuple) -> bytes: ...


def canonicalize(data: object) -> bytes:
    return _canonicalize(cast(JsonWithTuple, data))


_preprocess = JsonDataPreprocessor(
    [
        int_to_str_if_too_large,
        float_to_final_es6_str,
        dict_to_sorted_by_utf16_tuple,
    ]
)


def _canonicalize(data: JsonWithTuple) -> bytes:
    output = json.dumps(
        _preprocess(data),
        separators=(',', ':'),
        ensure_ascii=False,
        allow_nan=False,
        cls=FinalJsonEncoder,
    )
    return output.encode('utf8')
