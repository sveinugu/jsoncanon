from collections.abc import Callable
from typing import NoReturn, cast, overload

import simplejson

from jsoncanon.functions import (
    big_int_as_float,
    big_int_as_str,
    dict_to_sorted_by_utf16_tuple,
    float_to_final_es6_str,
    parse_canonical_int,
    raise_if_big_int,
    raise_if_big_int_string,
    restore_unique_big_int_strings,
)
from jsoncanon.preprocess import (
    JsonDataPreprocessor,
)
from jsoncanon.types import (
    BigIntsOption,
    FinalJson,
    Json,
    JsonScalar,
    JsonWithTuple,
    JsonWithTupleT,
    PreprocFuncDict,
)
from jsoncanon.validator import CanonicalJsonValidator


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


@overload
def canonicalize(data: Json, big_ints: BigIntsOption = 'as_string') -> bytes: ...


def canonicalize(data: object, big_ints: BigIntsOption = 'as_string') -> bytes:
    return _canonicalize(cast(JsonWithTuple, data), big_ints)


_common_preproc_funcs: PreprocFuncDict = {
    'float': float_to_final_es6_str,
    'dict': dict_to_sorted_by_utf16_tuple,
}


_preprocess_big_ints_as_str = JsonDataPreprocessor(
    _common_preproc_funcs
    | {
        'int': big_int_as_str,
    }
)


_preprocess_big_ints_uniquely_as_str = JsonDataPreprocessor(
    _common_preproc_funcs
    | {
        'int': big_int_as_str,
        'str': raise_if_big_int_string,
    }
)


_preprocess_raise_on_big_ints = JsonDataPreprocessor(
    _common_preproc_funcs
    | {
        'int': raise_if_big_int,
    }
)


_preprocess_allow_big_ints = JsonDataPreprocessor(
    _common_preproc_funcs
    | {
        'int': big_int_as_float,
    }
)


def _select_preprocessor(big_ints: BigIntsOption) -> JsonDataPreprocessor:
    match big_ints:
        case 'as_string':
            return _preprocess_big_ints_as_str
        case 'uniquely_as_string':
            return _preprocess_big_ints_uniquely_as_str
        case 'as_float':
            return _preprocess_allow_big_ints
        case 'raise':
            return _preprocess_raise_on_big_ints


def _canonicalize(data: JsonWithTuple, big_ints: BigIntsOption) -> bytes:
    preprocess = _select_preprocessor(big_ints)
    preprocessed = preprocess(data)
    if isinstance(preprocessed, FinalJson):
        return preprocessed.encoded_json.encode('utf8')

    output: str = simplejson.dumps(
        preprocessed,
        separators=(',', ':'),
        ensure_ascii=False,
        allow_nan=False,
    )
    del preprocessed
    return output.encode('utf8')


def validate_canonicalized(data: object) -> None:
    CanonicalJsonValidator(data).validate()


def is_canonicalized(data: object) -> bool:
    try:
        validate_canonicalized(data)
        return True
    except (ValueError, TypeError):
        return False


def load_canonicalized(
    data: bytes,
    big_ints: BigIntsOption = 'as_string',
    validate_func: Callable[[object], None] | None = validate_canonicalized,
) -> Json:
    if validate_func:
        validate_func(data)

    loaded: Json = simplejson.loads(
        data,
        parse_int=parse_canonical_int,
        parse_float=float,
        parse_constant=_raise_invalid_json_constant,
    )

    if big_ints == 'uniquely_as_string':
        return restore_unique_big_int_strings(loaded)
    return loaded


def _raise_invalid_json_constant(value: str) -> NoReturn:
    raise ValueError(f'{value} is not valid JSON')
