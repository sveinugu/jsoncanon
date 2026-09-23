"""Benchmark preparation, verification, and measurement."""

from __future__ import annotations

import gc
import time
import tracemalloc
from collections.abc import Iterator
from dataclasses import InitVar, dataclass, field
from typing import Generic, cast

from .models import Benchmark, BenchmarkResult, CaseBenchmarkResult, Dataset
from .protocols import (
    ExpectedOutputFactory,
    ImplementationOperation,
    InputFactory,
    InputT,
    OutputT,
)
from .statistics import bootstrap_medians

FactoryCache = dict[tuple[str, object], object]


def cached_factory_result(
    dataset: Dataset,
    factory: InputFactory[OutputT] | ExpectedOutputFactory[OutputT],
    cache: FactoryCache,
) -> OutputT:
    """Return a dataset-factory value cached by fixture checksum and factory."""
    key = (dataset.sha256, factory)
    try:
        return cast(OutputT, cache[key])
    except KeyError:
        result = factory(dataset)
        cache[key] = result
        return result


def real_iterations(size: int) -> int:
    """Choose a practical number of calls for a real-world fixture size."""
    if size <= 10 * 1024:
        return 100
    if size <= 1024 * 1024:
        return 50
    return 5


@dataclass(frozen=True)
class PreparedCase(Generic[InputT, OutputT]):
    """The dataset-specific input, expectation, size, and call count for a benchmark."""

    dataset: Dataset
    benchmark: Benchmark[InputT, OutputT]
    byte_size: int = field(init=False)
    calls: int = field(init=False)
    input_value: InputT = field(init=False)
    expected_output: OutputT | None = field(init=False)
    has_expected_output: bool = field(init=False)
    _factory_cache: InitVar[FactoryCache]
    _iterations: InitVar[int | None]

    def __post_init__(self, factory_cache: FactoryCache, iterations: int | None) -> None:
        input_value = cached_factory_result(
            self.dataset, self.benchmark.input_factory, factory_cache
        )
        expected_output = (
            cached_factory_result(
                self.dataset, self.benchmark.expected_output_factory, factory_cache
            )
            if self.benchmark.expected_output_factory is not None
            else None
        )
        byte_size = len(input_value) if isinstance(input_value, bytes) else len(self.dataset.source)
        calls = iterations if iterations is not None else real_iterations(byte_size)
        object.__setattr__(self, 'input_value', input_value)
        object.__setattr__(self, 'expected_output', expected_output)
        object.__setattr__(
            self, 'has_expected_output', self.benchmark.expected_output_factory is not None
        )
        object.__setattr__(self, 'byte_size', byte_size)
        object.__setattr__(self, 'calls', calls)


def run_benchmark(
    function: ImplementationOperation[InputT, OutputT],
    value: InputT,
    iterations: int,
    trials: int,
) -> BenchmarkResult:
    """Return timing samples and peak Python allocation for one operation."""
    durations: list[float] = []
    for _ in range(trials):
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            start = time.perf_counter()
            for _ in range(iterations):
                function(value)
            durations.append((time.perf_counter() - start) / iterations)
        finally:
            if gc_was_enabled:
                gc.enable()
    gc.collect()
    tracemalloc.start()
    try:
        function(value)
        _, peak_memory_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return BenchmarkResult(tuple(durations), peak_memory_bytes)


def check_expected_output(actual: object, expected: object) -> None:
    """Raise when an implementation does not produce the prepared expectation."""
    if actual != expected:
        raise ValueError('result differs from the expected output')


def run_benchmark_cases(
    benchmark_definition: Benchmark[InputT, OutputT],
    datasets: list[Dataset],
    iterations: int | None,
    trials: int,
    factory_cache: FactoryCache,
    seed_offset: int,
) -> Iterator[CaseBenchmarkResult]:
    """Prepare, verify, and yield each dataset result for one benchmark definition."""
    for case_index, dataset in enumerate(datasets):
        prepared = PreparedCase(dataset, benchmark_definition, factory_cache, iterations)
        results: list[BenchmarkResult | None] = []
        errors: list[str] = []
        for implementation in benchmark_definition.implementations:
            try:
                if prepared.has_expected_output:
                    check_expected_output(
                        implementation.operation(prepared.input_value), prepared.expected_output
                    )
                results.append(
                    run_benchmark(
                        implementation.operation, prepared.input_value, prepared.calls, trials
                    )
                )
            except (TypeError, ValueError, OverflowError, RuntimeError) as error:
                results.append(None)
                errors.append(f'{dataset.name} / {implementation.name}: {error}')
        bootstrap_median_samples = tuple(
            bootstrap_medians(result, seed_offset + case_index * 100 + implementation_index)
            if result is not None
            else None
            for implementation_index, result in enumerate(results)
        )
        yield CaseBenchmarkResult(
            dataset.name,
            prepared.byte_size,
            tuple(results),
            bootstrap_median_samples,
            tuple(errors),
        )
