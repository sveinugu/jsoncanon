import pytest
from jsoncanon.types import BigIntsOption
from jsoncanon.validator import CanonicalJsonValidator


def _assert_accepted(data: bytes, big_ints: BigIntsOption = 'as_string') -> None:
    CanonicalJsonValidator(data, big_ints).validate()


def _assert_rejected(
    data: bytes | str,
    big_ints: BigIntsOption = 'as_string',
    exc_class: type[Exception] = ValueError,
) -> None:
    with pytest.raises(exc_class):
        CanonicalJsonValidator(data, big_ints).validate()


def test_validate_canonicalized_accepts_canonical_json() -> None:
    _assert_accepted(b'{"a":[0,-1,1.5,1e+21,1e-7,0.000001,"text",null,true,false]}')
    _assert_accepted(b'{"\\r":0,"1":0,"\xc2\x80":0,"\xc3\xb6":0,"\xe2\x82\xac":0}')
    _assert_accepted(b'"\\b\\t\\n\\u000b\\f\\r"')
    _assert_accepted(b'9007199254740992', big_ints='as_float')
    _assert_accepted(b'9007199254740994', big_ints='as_float')
    _assert_accepted(b'"9007199254740992"', big_ints='as_string')
    _assert_accepted(b'"9007199254740993"', big_ints='as_string')
    _assert_accepted(b'"9007199254740994"', big_ints='as_string')
    _assert_accepted(b'"9007199254740992"', big_ints='uniquely_as_string')
    _assert_accepted(b'"9007199254740993"', big_ints='uniquely_as_string')
    _assert_accepted(b'"9007199254740994"', big_ints='uniquely_as_string')
    _assert_accepted(b'9007199254740991', big_ints='raise')


@pytest.mark.parametrize(
    ('data', 'exc_class'),
    [
        ('{"a":1}', TypeError),
        (b'{"a": 1}', ValueError),
        (b'{"b":1,"a":2}', ValueError),
        (b'{"a":1,"a":2}', ValueError),
        (b'"\\u0041"', ValueError),
        (b'"a\\/b"', ValueError),
        (b'"\\uD83D\\uDE00"', ValueError),
        (b'"\x80"', ValueError),
        (b'-0', ValueError),
        (b'1.0', ValueError),
        (b'1e5', ValueError),
        (b'1E+5', ValueError),
        (b'1e+05', ValueError),
    ],
)
def test_validate_canonicalized_rejects_noncanonical_json(
    data: bytes, exc_class: type[Exception]
) -> None:
    _assert_rejected(data, exc_class=exc_class)


@pytest.mark.parametrize(
    ('data', 'big_ints'),
    [
        (b'9007199254740992', 'as_string'),
        (b'9007199254740992', 'uniquely_as_string'),
        (b'9007199254740992', 'raise'),
        (b'9007199254740993', 'as_float'),  # Not possible by ECMAScript Number::toString algorithm
    ],
)
def test_validate_canonicalized_rejects_non_canonical_bigints(
    data: bytes, big_ints: BigIntsOption
) -> None:
    _assert_rejected(data, big_ints=big_ints)
