from typing import (
    cast,
    overload,
)

from jsoncanon.types import (
    JsonScalar,
    JsonWithFinal,
    JsonWithTuple,
    JsonWithTupleT,
    PreprocFuncDict,
)


class JsonDataPreprocessor:
    def __init__(self, preproc_funcs: PreprocFuncDict | None = None):
        if preproc_funcs is None:
            preproc_funcs = {}

        self._funcs: PreprocFuncDict = preproc_funcs

    @overload
    def __call__(self, data: dict[str, JsonWithTupleT]) -> JsonWithFinal: ...

    @overload
    def __call__(self, data: list[JsonWithTupleT]) -> JsonWithFinal: ...

    @overload
    def __call__(self, data: tuple[JsonWithTupleT, ...]) -> JsonWithFinal: ...

    @overload
    def __call__(self, data: JsonScalar) -> JsonWithFinal: ...

    @overload
    def __call__(self, data: JsonWithTuple) -> JsonWithFinal: ...

    def __call__(self, data: object) -> JsonWithFinal:
        return self._preprocess(cast(JsonWithTuple, data))

    def _preprocess(self, data: JsonWithTuple) -> JsonWithFinal:
        output: JsonWithFinal
        match data:
            case str():
                return self._funcs['str'](data) if 'str' in self._funcs else data
            case bool():
                return self._funcs['bool'](data) if 'bool' in self._funcs else data
            case int():
                return self._funcs['int'](data) if 'int' in self._funcs else data
            case float():
                return self._funcs['float'](data) if 'float' in self._funcs else data
            case None:
                return self._funcs['NoneType'](data) if 'NoneType' in self._funcs else data
            case dict():
                output = {key: self._preprocess(val) for (key, val) in data.items()}
                return self._funcs['dict'](output) if 'dict' in self._funcs else output
            case list() | tuple():
                output = [self._preprocess(val) for val in data]
                return self._funcs['list'](output) if 'list' in self._funcs else output
            case _:  # pyright: ignore[reportUnnecessaryComparison]
                raise TypeError(f'Object of type "{type(data)}" not supported')
