"""Records shared by RFC 8785 benchmark definitions, execution, and rendering."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Generic

from jsoncanon.types import Json

from .protocols import (
    ExpectedOutputFactory,
    ImplementationOperation,
    InputFactory,
    InputT,
    OutputT,
)


@dataclass(frozen=True)
class Dataset:
    """One checksum-verified JSON fixture and its parsed representation."""

    name: str
    payload: Json
    source: bytes
    sha256: str


@dataclass(frozen=True)
class Implementation(Generic[InputT, OutputT]):
    """A named implementation participating in a benchmark."""

    name: str
    operation: ImplementationOperation[InputT, OutputT]


@dataclass(frozen=True)
class Baseline:
    """A score label and the implementation used as its reference."""

    label: str
    implementation_name: str


@dataclass(frozen=True)
class Score:
    """A point estimate with lower and upper confidence bounds."""

    point: float
    lower: float
    upper: float


@dataclass(frozen=True)
class BenchmarkResult:
    """Per-trial durations for one implementation and dataset."""

    samples: tuple[float, ...]

    @property
    def median(self) -> float:
        return statistics.median(self.samples)


@dataclass(frozen=True)
class Benchmark(Generic[InputT, OutputT]):
    """The configuration needed to execute and render one benchmark table."""

    title: str
    implementations: tuple[Implementation[InputT, OutputT], ...]
    input_factory: InputFactory[InputT]
    expected_output_factory: ExpectedOutputFactory[OutputT] | None
    baselines: tuple[Baseline, ...]


@dataclass(frozen=True)
class CaseBenchmarkResult:
    """Measured results and derived samples for one prepared case."""

    name: str
    byte_size: int
    results: tuple[BenchmarkResult | None, ...]
    bootstrap_median_samples: tuple[list[float] | None, ...]
    errors: tuple[str, ...]
