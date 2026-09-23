"""Statistical calculations for benchmark timings."""

from __future__ import annotations

import random
import statistics

from .models import BenchmarkResult, CaseBenchmarkResult, Score

BOOTSTRAP_SAMPLES = 1_000


def percentile(values: list[float], quantile: float) -> float:
    """Return a linearly interpolated percentile from sorted values."""
    index = (len(values) - 1) * quantile
    lower = int(index)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def bootstrap_medians(result: BenchmarkResult, seed: int) -> list[float]:
    """Return bootstrap medians for a result's trial durations."""
    random_source = random.Random(seed)
    return [
        statistics.median(random_source.choices(result.samples, k=len(result.samples)))
        for _ in range(BOOTSTRAP_SAMPLES)
    ]


def confidence_interval(samples: list[float]) -> tuple[float, float]:
    """Return a deterministic bootstrap 95% interval for the median."""
    ordered = sorted(samples)
    return percentile(ordered, 0.025), percentile(ordered, 0.975)


def relative_scores(
    results: tuple[BenchmarkResult | None, ...],
    bootstrap_median_samples: tuple[list[float] | None, ...],
    baseline_index: int,
) -> list[Score | None]:
    """Score implementations against a selected baseline, with bootstrap intervals."""
    baseline = results[baseline_index]
    baseline_samples = bootstrap_median_samples[baseline_index]
    if baseline is None or baseline_samples is None:
        return [None] * len(results)
    point_scores = [
        result.median / baseline.median * 100 if result is not None else None for result in results
    ]
    distributions: list[list[float] | None] = [
        [] if result is not None else None for result in results
    ]
    for sample_index in range(BOOTSTRAP_SAMPLES):
        trial_medians = [
            samples[sample_index] if samples is not None else None
            for samples in bootstrap_median_samples
        ]
        for index, value in enumerate(trial_medians):
            if value is not None:
                distribution = distributions[index]
                assert distribution is not None
                distribution.append(value / baseline_samples[sample_index] * 100)
    return [
        Score(score, *confidence_interval(distribution))
        if score is not None and distribution is not None
        else None
        for score, distribution in zip(point_scores, distributions, strict=True)
    ]


def relative_memory_scores(
    results: tuple[BenchmarkResult | None, ...], baseline_index: int
) -> list[float | None]:
    """Return peak-memory ratios relative to the selected baseline."""
    baseline = results[baseline_index]
    if baseline is None or baseline.peak_memory_bytes == 0:
        return [None] * len(results)
    return [
        result.peak_memory_bytes / baseline.peak_memory_bytes * 100 if result is not None else None
        for result in results
    ]


def geometric_mean_scores(
    cases: tuple[CaseBenchmarkResult, ...], baseline_index: int
) -> list[Score | None]:
    """Return geometric-mean relative scores across compatible datasets."""
    scores: list[Score | None] = []
    for implementation_index in range(len(cases[0].results)):
        compatible_cases: list[
            tuple[BenchmarkResult, BenchmarkResult, list[float], list[float]]
        ] = []
        for case in cases:
            result = case.results[implementation_index]
            baseline = case.results[baseline_index]
            result_samples = case.bootstrap_median_samples[implementation_index]
            baseline_samples = case.bootstrap_median_samples[baseline_index]
            if (
                result is not None
                and baseline is not None
                and result_samples is not None
                and baseline_samples is not None
            ):
                compatible_cases.append((result, baseline, result_samples, baseline_samples))
        if not compatible_cases:
            scores.append(None)
            continue
        point = statistics.geometric_mean(
            result.median / baseline.median * 100 for result, baseline, _, _ in compatible_cases
        )
        distribution = [
            statistics.geometric_mean(
                samples[sample_index] / baseline_samples[sample_index] * 100
                for _, _, samples, baseline_samples in compatible_cases
            )
            for sample_index in range(BOOTSTRAP_SAMPLES)
        ]
        scores.append(Score(point, *confidence_interval(distribution)))
    return scores


def geometric_mean_memory_scores(
    cases: tuple[CaseBenchmarkResult, ...], baseline_index: int
) -> list[float | None]:
    """Return geometric-mean peak-memory ratios across compatible datasets."""
    scores: list[float | None] = []
    for implementation_index in range(len(cases[0].results)):
        ratios = [
            result.peak_memory_bytes / baseline.peak_memory_bytes * 100
            for case in cases
            if (result := case.results[implementation_index]) is not None
            and (baseline := case.results[baseline_index]) is not None
            and baseline.peak_memory_bytes > 0
        ]
        scores.append(statistics.geometric_mean(ratios) if ratios else None)
    return scores
