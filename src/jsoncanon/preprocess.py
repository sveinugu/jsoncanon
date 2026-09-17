from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from inspect import Parameter, Signature, signature
from typing import (
    Any,
    cast,
    overload,
)

from jsoncanon.types import (
    JsonScalar,
    JsonType,
    JsonWithFinal,
    JsonWithTuple,
    JsonWithTupleT,
    PreprocFunc,
    PreprocInputFunc,
)
from jsoncanon.util import ensure_plain_type


@dataclass
class PreprocFuncInfo:
    input_type: type[JsonWithFinal]
    return_type: type[JsonWithFinal]
    func: PreprocFunc


@dataclass
class JsonDataPreprocessor:
    def __init__(self, preprocess_funcs: Sequence[PreprocInputFunc] | None = None):
        if preprocess_funcs is None:
            preprocess_funcs = []

        self._preproc_func_info_dict: defaultdict[JsonType, list[PreprocFuncInfo]] = defaultdict(
            list
        )
        for preproc_func in preprocess_funcs:
            func_sign = signature(preproc_func)
            input_type = self._validate_params_and_get_input_type(func_sign, preproc_func)
            return_type = self._validate_and_get_return_type(func_sign, preproc_func)

            self._preproc_func_info_dict[input_type].append(
                PreprocFuncInfo(input_type, return_type, cast(PreprocFunc, preproc_func))
            )

    @staticmethod
    def _validate_and_get_return_type(func_sign: Signature, preproc_func: PreprocInputFunc) -> Any:
        return_type = func_sign.return_annotation
        assert return_type is not Parameter.empty, (
            f'Preprocess function {preproc_func.__name__} must have a return annotation'
        )

        return ensure_plain_type(return_type)

    @staticmethod
    def _validate_params_and_get_input_type(
        func_sign: Signature,
        preproc_func: PreprocInputFunc,
    ) -> Any:
        assert len(func_sign.parameters) == 1, (
            f'Preprocess function {preproc_func.__name__} must have exactly one parameter'
        )

        input_param: Parameter = tuple(func_sign.parameters.values())[0]
        assert input_param.kind == Parameter.POSITIONAL_ONLY, (
            f'Preprocess function {preproc_func.__name__} parameter must be positional only'
        )

        input_annotation = input_param.annotation
        assert input_annotation is not Parameter.empty, (
            f'Preprocess function {preproc_func.__name__} parameter must have type annotation'
        )

        return ensure_plain_type(input_annotation)

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
                output = self._preprocess_for_type(data, str)
            case bool():
                output = self._preprocess_for_type(data, bool)
            case int():
                output = self._preprocess_for_type(data, int)
            case float():
                output = self._preprocess_for_type(data, float)
            case None:
                output = self._preprocess_for_type(data, None)
            case dict():
                output = {key: self._preprocess(val) for (key, val) in data.items()}
                output = self._preprocess_for_type(output, dict)
            case list() | tuple():
                output = [self._preprocess(val) for val in data]
                output = self._preprocess_for_type(output, list)
            case _:  # pyright: ignore[reportUnnecessaryComparison]
                raise TypeError(f'Object of type "{type(data)}" not supported')
        return output

    def _preprocess_for_type(self, data: JsonWithFinal, data_type: JsonType) -> JsonWithFinal:
        preproc_funcs_for_data_type = self._preproc_func_info_dict[data_type]
        for preproc_func_info in preproc_funcs_for_data_type:
            data = preproc_func_info.func(data)
        return data
