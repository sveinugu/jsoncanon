import json.encoder
import threading

import pytest
from jsoncanon.encoder import FinalJsonEncoder
from jsoncanon.types import FinalJson, JsonWithFinal


@pytest.mark.parametrize(
    'data, expected',
    [
        ('test', '"test"'),
        (123, '123'),
        (123.456, '123.456'),
        (True, 'true'),
        (False, 'false'),
        (None, 'null'),
        ([123, '456'], '[123, "456"]'),
        ({'key': 'value'}, '{"key": "value"}'),
        (FinalJson('test'), 'test'),
    ],
    ids=['str', 'int', 'float', 'true', 'false', 'null', 'list', 'dict', 'FinalJson'],
)
def test_final_json_encoder(data: JsonWithFinal, expected: str) -> None:
    encoder = FinalJsonEncoder(ensure_ascii=False)
    encoded = encoder.encode(data)
    assert encoded == expected
    assert ''.join(encoder.iterencode(data)) == expected


def test_final_json_encoder_resets_context_after_error() -> None:
    wrapped_encode_basestring = json.encoder.encode_basestring
    encoder = FinalJsonEncoder(ensure_ascii=False, allow_nan=False)
    with pytest.raises(ValueError):
        encoder.encode(float('nan'))
    assert json.encoder.encode_basestring is wrapped_encode_basestring
    assert json.encoder.encode_basestring(FinalJson('123')) == '"123"'


def test_final_json_encoder_is_thread_safe() -> None:
    encoding_started = threading.Event()
    continue_encoding = threading.Event()
    chunks: list[str] = []

    def encode_final_json() -> None:
        iterator = FinalJsonEncoder(ensure_ascii=False).iterencode([FinalJson('123')])
        chunks.append(next(iterator))
        encoding_started.set()
        continue_encoding.wait()
        chunks.extend(iterator)

    thread = threading.Thread(target=encode_final_json)
    thread.start()
    try:
        assert encoding_started.wait(timeout=1)
        assert json.encoder.JSONEncoder(ensure_ascii=False).encode(FinalJson('123')) == '"123"'
    finally:
        continue_encoding.set()
        thread.join(timeout=1)

    assert not thread.is_alive()
    assert ''.join(chunks) == '[123]'


def test_raw_json_encoder_ensure_ascii_true() -> None:
    with pytest.raises(AssertionError, match='FinalJsonEncoder requires ensure_ascii=False'):
        FinalJsonEncoder(ensure_ascii=True)
