import sys

from hypothesis import given, settings
from hypothesis import strategies as st

from jsoncanon import canonicalize, load_canonicalized
from jsoncanon.functions import is_canonical_big_int_string
from jsoncanon.types import BigIntsOption, JsonWithTuple

_ES6_MAX_SAFE_INTEGER = 2**53 - 1
_MAX_FLOAT_INTEGER = int(sys.float_info.max)


def _optionally_negative_int(negative: bool, integer: int) -> int:
    return -integer if negative else integer


def _optionally_negative_str(negative: bool, digits: str) -> str:
    return ('-' if negative else '') + digits


def _lossless_int_filter(val: int) -> bool:
    return val == float(val)


# Lossless integers (ints that can be represented as a float without loss of precision)

_safe_ints = st.integers(min_value=-_ES6_MAX_SAFE_INTEGER, max_value=_ES6_MAX_SAFE_INTEGER)
_lossless_float_ints = st.integers(
    min_value=-_MAX_FLOAT_INTEGER, max_value=_MAX_FLOAT_INTEGER
).filter(_lossless_int_filter)
_lossless_ints = st.integers().filter(_lossless_int_filter)


# Lossy integers (ints that cannot be represented as a float without loss of precision)

_lossy_big_ints = st.builds(
    _optionally_negative_int,
    st.booleans(),
    st.integers(
        min_value=2**52,
        max_value=2**53 - 1,
    ).map(lambda value: 2 * value + 1),
)

# Strings

# Exclude non-UTF-8-encodable characters (e.g. lone surrogates), which
# `canonicalize` cannot handle.
_any_str = st.text(alphabet=st.characters(codec='utf-8'))

_digit_like_str: st.SearchStrategy[str] = st.builds(
    _optionally_negative_str,
    st.booleans(),
    st.text(alphabet='0123456789', min_size=1, max_size=25),
)

_big_ints_as_str = _digit_like_str.filter(lambda text: is_canonical_big_int_string(text))
_safe_ints_as_str = _digit_like_str.filter(lambda text: not is_canonical_big_int_string(text))
_misc_str = st.one_of(_any_str, _safe_ints_as_str, _big_ints_as_str)
_misc_str_no_big_ints = st.one_of(_any_str, _safe_ints_as_str)


def _json_values(
    integers: st.SearchStrategy[int],
    strs: st.SearchStrategy[str],
    ensure_int_leaves: bool = False,
) -> st.SearchStrategy[JsonWithTuple]:
    if ensure_int_leaves:
        scalars = integers
    else:
        scalars = st.one_of(
            st.none(),
            st.booleans(),
            integers,
            st.floats(allow_nan=False, allow_infinity=False),
            strs,
        )

    return st.recursive(
        scalars,
        lambda children: st.one_of(st.lists(children), st.dictionaries(_any_str, children)),
        min_leaves=1 if ensure_int_leaves else None,
        max_leaves=20,
    )


def _lossless_roundtrip_from_data(data: JsonWithTuple, big_ints: BigIntsOption) -> bool:
    return load_canonicalized(canonicalize(data, big_ints=big_ints), big_ints=big_ints) == data


def _lossless_roundtrip_from_canonical(data: JsonWithTuple, big_ints: BigIntsOption) -> bool:
    canonical = canonicalize(data, big_ints='as_float')
    return (
        canonicalize(load_canonicalized(canonical, big_ints=big_ints), big_ints=big_ints)
        == canonical
    )


@given(
    _json_values(
        _safe_ints,
        _misc_str,
    ),
)
@settings(max_examples=100)
def test_raise_roundtrip_twice_for_supported_values(data: JsonWithTuple) -> None:
    assert _lossless_roundtrip_from_data(data, big_ints='raise')
    assert _lossless_roundtrip_from_canonical(data, big_ints='raise')


@given(
    lossless_data=_json_values(
        _lossless_float_ints,
        _misc_str,
    ),
    lossy_data=_json_values(
        _lossy_big_ints,
        _misc_str,
        ensure_int_leaves=True,
    ),
)
@settings(max_examples=100)
def test_as_float_canonicalization_roundtrip_twice(
    lossless_data: JsonWithTuple, lossy_data: JsonWithTuple
) -> None:
    assert _lossless_roundtrip_from_data(lossless_data, big_ints='as_float')
    assert _lossless_roundtrip_from_canonical(lossless_data, big_ints='as_float')

    assert not _lossless_roundtrip_from_data(lossy_data, big_ints='as_float')
    assert _lossless_roundtrip_from_canonical(lossy_data, big_ints='as_float')


@given(
    lossless_data=_json_values(
        _safe_ints,
        _misc_str,
    ),
    lossy_data=_json_values(
        _lossy_big_ints,
        _misc_str,
        ensure_int_leaves=True,
    ),
)
@settings(max_examples=100)
def test_as_string_canonicalization_roundtrip_twice(
    lossless_data: JsonWithTuple, lossy_data: JsonWithTuple
) -> None:
    assert _lossless_roundtrip_from_data(lossless_data, big_ints='as_string')
    assert _lossless_roundtrip_from_canonical(lossless_data, big_ints='as_string')

    assert not _lossless_roundtrip_from_data(lossy_data, big_ints='as_string')
    assert _lossless_roundtrip_from_canonical(lossy_data, big_ints='as_string')


@given(
    data=_json_values(
        st.one_of(_lossy_big_ints, _safe_ints),
        _misc_str_no_big_ints,
    ),
)
@settings(max_examples=100)
def test_uniquely_as_string_roundtrip_twice(data: JsonWithTuple) -> None:
    assert _lossless_roundtrip_from_data(data, big_ints='uniquely_as_string')
    assert _lossless_roundtrip_from_canonical(data, big_ints='uniquely_as_string')
