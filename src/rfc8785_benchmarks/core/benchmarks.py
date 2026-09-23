"""Definitions of the RFC 8785 library benchmark sections."""

from __future__ import annotations

from typing import Any

from jsoncanon.types import BigIntsOption, Json

from .implementations import (
    canonical_input,
    canonical_output,
    canonical_validation_result,
    canonicalize_jcs,
    canonicalize_rfc8785,
    canonicalizer_for_mode,
    decode_json,
    decode_simplejson,
    decoded_output,
    decoder_for_mode,
    stream_operation_for,
    stream_write_rfc8785,
    stream_writer_for,
    validator,
)
from .models import Baseline, Benchmark, Implementation

BIG_INT_MODES: tuple[BigIntsOption, ...] = (
    'raise',
    'as_float',
    'as_string',
    'uniquely_as_string',
)


def canonicalizer_implementations() -> tuple[Implementation[Json, bytes], ...]:
    """Return the canonicalizers used for byte-producing benchmark sections."""
    return (
        *(
            Implementation(f'jsoncanon ({mode})', canonicalizer_for_mode(mode))
            for mode in BIG_INT_MODES
        ),
        Implementation('jcs', canonicalize_jcs),
        Implementation('rfc8785 (dumps)', canonicalize_rfc8785),
    )


def stream_write_implementations() -> tuple[Implementation[Json, bytes], ...]:
    """Return the implementations used for canonicalization plus stream writing."""
    return (
        *(
            Implementation(
                implementation.name,
                stream_operation_for(stream_writer_for(implementation.operation)),
            )
            for implementation in canonicalizer_implementations()
        ),
        Implementation('rfc8785 (dump)', stream_operation_for(stream_write_rfc8785)),
    )


def decoder_implementations() -> tuple[Implementation[bytes, Json], ...]:
    """Return the canonical-JSON decoders used by the benchmark."""
    return (
        *(Implementation(f'jsoncanon {mode}', decoder_for_mode(mode)) for mode in BIG_INT_MODES),
        Implementation('json.loads', decode_json),
        Implementation('simplejson.loads', decode_simplejson),
    )


def validator_implementations() -> tuple[Implementation[bytes, bool], ...]:
    """Return the canonical-JSON validators used by the benchmark."""
    return (Implementation('validation', validator),)


def canonical_baselines() -> tuple[Baseline, Baseline]:
    return (
        Baseline('vs jcs', 'jcs'),
        Baseline('vs rfc8785 (dumps)', 'rfc8785 (dumps)'),
    )


def stream_write_baselines() -> tuple[Baseline, Baseline]:
    return (
        Baseline('vs jcs', 'jcs'),
        Baseline('vs rfc8785 (dump)', 'rfc8785 (dump)'),
    )


def decoded_baselines() -> tuple[Baseline, Baseline]:
    return (
        Baseline('vs json', 'json.loads'),
        Baseline('vs simplejson', 'simplejson.loads'),
    )


def get_canonicalization_benchmark() -> Benchmark[Json, bytes]:
    """Build the canonicalization benchmark."""
    return Benchmark(
        'Canonicalization',
        canonicalizer_implementations(),
        canonical_input,
        canonical_output,
        canonical_baselines(),
    )


def get_stream_write_benchmark() -> Benchmark[Json, bytes]:
    """Build the canonicalization-and-stream-write benchmark."""
    return Benchmark(
        'Canonicalization + stream write',
        stream_write_implementations(),
        canonical_input,
        canonical_output,
        stream_write_baselines(),
    )


def get_decoding_benchmark() -> Benchmark[bytes, Json]:
    """Build the canonical-JSON decoding benchmark."""
    return Benchmark(
        'Canonical decoding',
        decoder_implementations(),
        canonical_output,
        decoded_output,
        decoded_baselines(),
    )


def get_validation_benchmark() -> Benchmark[bytes, bool]:
    """Build the canonical-JSON validation benchmark."""
    return Benchmark(
        'Canonical validation',
        validator_implementations(),
        canonical_output,
        canonical_validation_result,
        (),
    )


def get_benchmarks() -> tuple[Benchmark[Any, Any], ...]:
    """Return every benchmark in display order."""
    return (
        get_canonicalization_benchmark(),
        get_stream_write_benchmark(),
        get_decoding_benchmark(),
        get_validation_benchmark(),
    )
