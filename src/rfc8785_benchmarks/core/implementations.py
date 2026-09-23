"""Adapters for the JSON libraries compared by the benchmark suite."""

from __future__ import annotations

import json
from io import BytesIO
from typing import Protocol, cast

import jcs  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
import rfc8785
import simplejson

from jsoncanon import canonicalize, is_canonicalized, load_canonicalized
from jsoncanon.types import BigIntsOption, Json

from .models import Dataset
from .protocols import ImplementationOperation


class Canonicalizer(ImplementationOperation[Json, bytes], Protocol):
    """Canonicalize a JSON value to bytes."""


class StreamWriter(Protocol):
    """Write a canonicalized JSON value to a byte stream."""

    def __call__(self, data: Json, sink: BytesIO, /) -> None: ...


class Decoder(ImplementationOperation[bytes, Json], Protocol):
    """Decode canonical JSON bytes."""


class Validator(ImplementationOperation[bytes, bool], Protocol):
    """Report whether JSON bytes are canonical."""


def canonicalize_jcs(data: Json) -> bytes:
    """Canonicalize with jcs."""
    output: bytes | str = jcs.canonicalize(data)  # pyright: ignore[reportUnknownMemberType]
    return output if isinstance(output, bytes) else output.encode()


def canonicalize_jsoncanon(data: Json) -> bytes:
    """Canonicalize with jsoncanon using RFC-compatible big-integer handling."""
    return canonicalize(data, big_ints='as_float')


def canonicalize_rfc8785(data: Json) -> bytes:
    """Canonicalize with rfc8785."""
    return rfc8785.dumps(data)


def stream_writer_for(function: Canonicalizer) -> StreamWriter:
    """Return a stream writer for a canonicalizer that returns bytes."""

    def write(data: Json, sink: BytesIO) -> None:
        sink.write(function(data))

    return write


def stream_write_rfc8785(data: Json, sink: BytesIO) -> None:
    """Write RFC 8785 output directly to a byte stream."""
    rfc8785.dump(data, sink)


def stream_operation_for(function: StreamWriter) -> Canonicalizer:
    """Return a bytes-producing operation that allocates a fresh stream per call."""

    def operation(data: Json) -> bytes:
        sink = BytesIO()
        function(data, sink)
        return sink.getvalue()

    return operation


def canonicalizer_for_mode(mode: BigIntsOption) -> Canonicalizer:
    """Return a jsoncanon canonicalizer configured for one big-integer mode."""

    def canonicalizer(data: Json) -> bytes:
        return canonicalize(data, big_ints=mode)

    return canonicalizer


def decoder_for_mode(mode: BigIntsOption) -> Decoder:
    """Return an unvalidated canonical JSON decoder for one big-integer mode."""

    def decoder(data: bytes) -> Json:
        return load_canonicalized(data, big_ints=mode, validate_func=None)

    return decoder


def decode_json(data: bytes) -> Json:
    """Decode JSON with the standard-library decoder."""
    return cast(Json, json.loads(data))


def decode_simplejson(data: bytes) -> Json:
    """Decode JSON with simplejson."""
    return cast(Json, simplejson.loads(data))


def canonical_input(dataset: Dataset) -> Json:
    """Return the parsed fixture payload for canonicalization benchmarks."""
    return dataset.payload


def canonical_output(dataset: Dataset) -> bytes:
    """Return jsoncanon's canonical bytes for a fixture."""
    return canonicalize_jsoncanon(dataset.payload)


def decoded_output(dataset: Dataset) -> Json:
    """Return the fixture's parsed JSON value for decoder comparisons."""
    return dataset.payload


def canonical_validation_result(_: Dataset) -> bool:
    """Return the expected validator result for internally canonicalized bytes."""
    return True


def validator(data: bytes) -> bool:
    """Report whether data satisfies JSON canonicalization requirements."""
    return is_canonicalized(data)
