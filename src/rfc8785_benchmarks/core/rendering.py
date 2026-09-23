"""Text-table rendering for RFC 8785 benchmark results."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from .models import Baseline, Benchmark, BenchmarkResult, CaseBenchmarkResult, Score
from .statistics import (
    confidence_interval,
    geometric_mean_memory_scores,
    geometric_mean_scores,
    relative_memory_scores,
    relative_scores,
)

COLUMN_WIDTH = 27
STATISTIC_WIDTH = 34


def column_labels(name: str) -> tuple[str, str]:
    """Split an implementation name into library and variant header lines."""
    if name.startswith('jsoncanon '):
        return 'jsoncanon', name.removeprefix('jsoncanon ')
    if name == 'validation':
        return 'jsoncanon', 'validation'
    if '.' in name:
        library, variant = name.split('.', 1)
        return library, variant
    if ' ' in name:
        library, variant = name.split(' ', 1)
        return library, variant
    return name, ''


def print_header(benchmark_definition: Benchmark[Any, Any]) -> None:
    """Print aligned two-line implementation headers."""
    labels = [
        column_labels(implementation.name)
        for implementation in benchmark_definition.implementations
    ]
    prefix = f'{"dataset":<20} {"bytes":<10} {"statistic":<{STATISTIC_WIDTH}}'
    print(' ' * len(prefix) + ''.join(f' {library:<{COLUMN_WIDTH}}' for library, _ in labels))
    print(prefix + ''.join(f' {variant:<{COLUMN_WIDTH}}' for _, variant in labels))
    print()


def format_timing(
    result: BenchmarkResult | None, bootstrap_median_samples: list[float] | None
) -> str:
    """Format median milliseconds with its 95% confidence interval."""
    if result is None:
        return 'incompatible'
    assert bootstrap_median_samples is not None
    lower, upper = confidence_interval(bootstrap_median_samples)
    return f'{result.median * 1_000:.3f} [{lower * 1_000:.3f}, {upper * 1_000:.3f}]'


def format_memory(result: BenchmarkResult | None) -> str:
    """Format peak traced Python allocation in kibibytes."""
    if result is None:
        return 'incompatible'
    return f'{result.peak_memory_bytes / 1024:.1f}'


def format_memory_score(score: float | None) -> str:
    """Format a peak-memory ratio without a confidence interval."""
    return 'incompatible' if score is None else f'{score:.0f}%'


def format_score(score: Score | None) -> str:
    """Format a relative score with its 95% confidence interval."""
    if score is None:
        return 'incompatible'
    return f'{score.point:.0f}% [{score.lower:.0f}, {score.upper:.0f}]'


def baseline_index(benchmark_definition: Benchmark[Any, Any], baseline: Baseline) -> int:
    """Return a baseline implementation's position in its benchmark."""
    for index, implementation in enumerate(benchmark_definition.implementations):
        if implementation.name == baseline.implementation_name:
            return index
    raise ValueError(
        f'{benchmark_definition.title}: baseline implementation '
        f'{baseline.implementation_name!r} is not configured'
    )


def print_case_rows(case: CaseBenchmarkResult, benchmark_definition: Benchmark[Any, Any]) -> None:
    """Print timing, peak-memory, and relative-score rows for one dataset."""
    timings = [
        format_timing(result, samples)
        for result, samples in zip(case.results, case.bootstrap_median_samples, strict=True)
    ]
    timing_result_content = f'{"time (ms)":<{STATISTIC_WIDTH}}' + ''.join(
        f' {timing:<{COLUMN_WIDTH}}' for timing in timings
    )
    memory_result_content = f'{"memory peak (KiB)":<{STATISTIC_WIDTH}}' + ''.join(
        f' {format_memory(result):<{COLUMN_WIDTH}}' for result in case.results
    )
    print(
        f'{case.name:<20} {case.byte_size:<10,} '
        f'{timing_result_content if not benchmark_definition.baselines else ""}'
    )
    if benchmark_definition.baselines:
        print(f'{"":<20} {"":<10} {timing_result_content}')

    for baseline in benchmark_definition.baselines:
        baseline_position = baseline_index(benchmark_definition, baseline)
        scores = relative_scores(
            case.results,
            case.bootstrap_median_samples,
            baseline_position,
        )
        print(
            f'{"":<20} {"":<10} {f"time % {baseline.label}":<{STATISTIC_WIDTH}}'
            + ''.join(f' {format_score(score):<{COLUMN_WIDTH}}' for score in scores)
        )
    print(f'{"":<20} {"":<10} {memory_result_content}')
    for baseline in benchmark_definition.baselines:
        baseline_position = baseline_index(benchmark_definition, baseline)
        memory_scores = relative_memory_scores(case.results, baseline_position)
        print(
            f'{"":<20} {"":<10} {f"peak % {baseline.label}":<{STATISTIC_WIDTH}}'
            + ''.join(f' {format_memory_score(score):<{COLUMN_WIDTH}}' for score in memory_scores)
        )
    if benchmark_definition.baselines:
        print()


def print_summary_rows(
    benchmark_definition: Benchmark[Any, Any], cases: tuple[CaseBenchmarkResult, ...]
) -> None:
    """Print geometric-mean relative scores for every configured baseline."""
    print('Summary')
    for baseline in benchmark_definition.baselines:
        baseline_position = baseline_index(benchmark_definition, baseline)
        scores = geometric_mean_scores(cases, baseline_position)
        print(
            f'{"":<20} {"":<10} {f"geomean time % {baseline.label}":<{STATISTIC_WIDTH}}'
            + ''.join(f' {format_score(score):<{COLUMN_WIDTH}}' for score in scores)
        )
    for baseline in benchmark_definition.baselines:
        baseline_position = baseline_index(benchmark_definition, baseline)
        memory_scores = geometric_mean_memory_scores(cases, baseline_position)
        print(
            f'{"":<20} {"":<10} {f"geomean peak % {baseline.label}":<{STATISTIC_WIDTH}}'
            + ''.join(f' {format_memory_score(score):<{COLUMN_WIDTH}}' for score in memory_scores)
        )
    print()


def print_benchmark(
    benchmark_definition: Benchmark[Any, Any], case_results: Iterator[CaseBenchmarkResult]
) -> None:
    """Render each finished case immediately, then render the summary."""
    print(benchmark_definition.title)
    print('-' * len(benchmark_definition.title))
    print_header(benchmark_definition)
    cases: list[CaseBenchmarkResult] = []
    for case in case_results:
        for error in case.errors:
            print(f'  {error}')
        print_case_rows(case, benchmark_definition)
        cases.append(case)
    if benchmark_definition.baselines:
        print_summary_rows(benchmark_definition, tuple(cases))
