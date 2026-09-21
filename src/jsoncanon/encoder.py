import json.encoder
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Generator

from jsoncanon.types import FinalJson, JsonWithFinal

_orig_encode_basestring = json.encoder.encode_basestring
_final_json_support_enabled: ContextVar[bool] = ContextVar(
    'final_json_support_enabled', default=False
)


def _encode_basestring_with_final_json_support(s: str) -> str:
    if _final_json_support_enabled.get() and isinstance(s, FinalJson):
        return s
    else:
        return _orig_encode_basestring(s)


json.encoder.encode_basestring = _encode_basestring_with_final_json_support


@contextmanager
def _enable_final_json_support() -> Generator[None, None, None]:
    token = _final_json_support_enabled.set(True)
    try:
        yield None
    finally:
        _final_json_support_enabled.reset(token)


class FinalJsonEncoder(json.encoder.JSONEncoder):
    def __init__(self, *args: Any, ensure_ascii: bool = True, **kwargs: Any):
        assert not ensure_ascii, 'FinalJsonEncoder requires ensure_ascii=False'
        super().__init__(*args, ensure_ascii=ensure_ascii, **kwargs)

    def encode(self, o: JsonWithFinal) -> str:
        with _enable_final_json_support():
            return super().encode(o)

    def iterencode(self, o: JsonWithFinal, _one_shot: bool = False) -> Iterator[str]:
        with _enable_final_json_support():
            yield from super().iterencode(o, _one_shot)
