from collections.abc import Callable
from typing import Literal, NamedTuple, TypeAlias, TypedDict, TypeVar

from simplejson import RawJSON


class FinalJson(RawJSON):
    def __eq__(self, other: 'FinalJson | object') -> bool:
        return type(other) is FinalJson and other.encoded_json == self.encoded_json


BigIntsOption: TypeAlias = Literal['as_string', 'uniquely_as_string', 'as_float', 'raise']

JsonScalar: TypeAlias = str | int | float | bool | None
Json: TypeAlias = JsonScalar | dict[str, 'Json'] | list['Json']

JsonWithTuple: TypeAlias = (
    JsonScalar | dict[str, 'JsonWithTuple'] | list['JsonWithTuple'] | tuple['JsonWithTuple', ...]
)
JsonWithTupleT = TypeVar('JsonWithTupleT', bound=JsonWithTuple)

JsonScalarWithFinal: TypeAlias = JsonScalar | FinalJson
JsonWithFinal: TypeAlias = JsonScalarWithFinal | dict[str, 'JsonWithFinal'] | list['JsonWithFinal']

# Aliased outside the class below, where the 'str' field shadows the builtin in type expressions
JsonDictWithFinal: TypeAlias = dict[str, JsonWithFinal]


class PreprocFuncDict(TypedDict, total=False):
    str: Callable[[str], JsonWithFinal]
    bool: Callable[[bool], JsonWithFinal]
    int: Callable[[int], JsonWithFinal]
    float: Callable[[float], JsonWithFinal]
    NoneType: Callable[[None], JsonWithFinal]
    dict: Callable[[JsonDictWithFinal], JsonWithFinal]
    list: Callable[[list[JsonWithFinal]], JsonWithFinal]


class DecimalParts(NamedTuple):
    """Normalized decimal components.

    Attributes:
        digits (str): the significant decimal digits, with leading and
            trailing zeroes removed.
        exponent (int): the base-10 exponent of the first digit.
    """

    negative: bool
    digits: str
    exponent: int
