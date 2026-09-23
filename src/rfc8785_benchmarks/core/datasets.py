"""Checksum-verified fixture loading for RFC 8785 benchmarks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from jsoncanon.types import Json
from rfc8785_benchmarks.dataset_fixtures import (
    FIXTURES_PATH,
    fixture_path,
    load_manifest,
    sha256_file,
)

from .models import Dataset


def load_datasets(suite: str) -> list[Dataset]:
    """Load a suite of local fixtures after verifying their manifest checksums."""
    datasets: list[Dataset] = []
    for fixture in load_manifest():
        if suite not in fixture.suites:
            continue
        path: Path = fixture_path(fixture, FIXTURES_PATH)
        if not path.exists():
            raise FileNotFoundError(
                f'{path} is missing; run python -m rfc8785_benchmarks.download_datasets '
                f'--suite {suite}'
            )
        actual_sha256 = sha256_file(path)
        if actual_sha256 != fixture.sha256:
            raise RuntimeError(
                f'{fixture.identifier}: SHA-256 mismatch: expected {fixture.sha256}, '
                f'got {actual_sha256}'
            )
        source = path.read_bytes()
        datasets.append(
            Dataset(fixture.identifier, cast(Json, json.loads(source)), source, actual_sha256)
        )
    if not datasets:
        raise RuntimeError(f'no fixtures are configured for suite {suite!r}')
    return datasets
