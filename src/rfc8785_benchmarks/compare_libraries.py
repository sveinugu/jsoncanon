"""Compare RFC 8785 canonicalization and decoding across Python implementations."""

from __future__ import annotations

import argparse

from rfc8785_benchmarks.core.benchmarks import get_benchmarks
from rfc8785_benchmarks.core.datasets import load_datasets
from rfc8785_benchmarks.core.execution import FactoryCache, run_benchmark_cases
from rfc8785_benchmarks.core.rendering import print_benchmark
from rfc8785_benchmarks.dataset_fixtures import available_suites


def run_real_cases(suite: str, iterations: int | None, trials: int) -> None:
    """Load, verify, and benchmark real-world fixtures across library implementations."""
    datasets = load_datasets(suite)
    print('Fixtures are checksum-validated. Timings are milliseconds per call.')
    print('Timings and scores show median [bootstrap 95% confidence interval].')
    print('Scores show relative time; each named competitor is 100% on its score row.')
    print('Summary scores are the geometric mean of compatible datasets.')
    print(f'Median of {trials} trials.')
    factory_cache: FactoryCache = {}
    for benchmark_index, benchmark_definition in enumerate(get_benchmarks()):
        print()
        print_benchmark(
            benchmark_definition,
            run_benchmark_cases(
                benchmark_definition,
                datasets,
                iterations,
                trials,
                factory_cache,
                benchmark_index * 1_000,
            ),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--iterations',
        type=int,
        help='calls per trial (default: size-based for fixture byte size)',
    )
    parser.add_argument('--trials', type=int, default=7, help='timing trials (default: 7)')
    parser.add_argument(
        '--suite',
        choices=available_suites(),
        default='default',
        help='fixture suite to benchmark (default: default)',
    )
    args = parser.parse_args()
    if args.trials < 1 or (args.iterations is not None and args.iterations < 1):
        parser.error('trials and iterations (when set) must be positive')
    return args


def main() -> None:
    args = parse_args()
    run_real_cases(args.suite, args.iterations, args.trials)


if __name__ == '__main__':
    main()
