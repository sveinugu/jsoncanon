"""Manifest support shared by real-world benchmark scripts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

MANIFEST_PATH = Path(__file__).with_name('datasets') / 'manifest.json'
FIXTURES_PATH = Path(__file__).with_name('datasets') / 'fixtures'


@dataclass(frozen=True)
class DatasetFixture:
    """A checksum-pinned JSON fixture used by the benchmark suite."""

    identifier: str
    filename: str
    url: str
    sha256: str
    suites: tuple[str, ...]


def load_manifest(path: Path = MANIFEST_PATH) -> tuple[DatasetFixture, ...]:
    """Load and validate a dataset fixture manifest."""
    manifest = cast(dict[str, object], json.loads(path.read_text()))
    fixtures_data = manifest.get('fixtures')
    if not isinstance(fixtures_data, list):
        raise ValueError(f'{path} must contain a fixtures list')
    fixtures_data = cast(list[object], fixtures_data)

    fixtures: list[DatasetFixture] = []
    for entry in fixtures_data:
        if not isinstance(entry, dict):
            raise ValueError(f'{path} fixture entries must be objects')
        entry = cast(dict[str, object], entry)
        identifier = entry.get('id')
        filename = entry.get('filename')
        url = entry.get('url')
        sha256 = entry.get('sha256')
        suites_data = entry.get('suites')
        if not isinstance(identifier, str) or not identifier:
            raise ValueError(f'{path} fixture entries require id, filename, url, and sha256')
        if not isinstance(filename, str) or not filename:
            raise ValueError(f'{path} fixture entries require id, filename, url, and sha256')
        if not isinstance(url, str) or not url:
            raise ValueError(f'{path} fixture entries require id, filename, url, and sha256')
        if not isinstance(sha256, str) or not sha256:
            raise ValueError(f'{path} fixture entries require id, filename, url, and sha256')
        if not isinstance(suites_data, list) or not suites_data:
            raise ValueError(f'{path} fixture entries require a non-empty suites list')
        suites_data = cast(list[object], suites_data)
        suites = tuple(suite for suite in suites_data if isinstance(suite, str) and suite)
        if len(suites) != len(suites_data):
            raise ValueError(f'{path} fixture suites must be non-empty strings')
        fixtures.append(
            DatasetFixture(
                identifier=identifier,
                filename=filename,
                url=url,
                sha256=sha256,
                suites=suites,
            )
        )
    return tuple(fixtures)


def available_suites(fixtures: tuple[DatasetFixture, ...] | None = None) -> tuple[str, ...]:
    """Return the configured suite names in manifest order."""
    fixtures = load_manifest() if fixtures is None else fixtures
    return tuple(dict.fromkeys(suite for fixture in fixtures for suite in fixture.suites))


def fixture_path(fixture: DatasetFixture, directory: Path = FIXTURES_PATH) -> Path:
    """Return the fixture's local path, rejecting path traversal in its manifest entry."""
    path = directory / fixture.filename
    if path.parent != directory:
        raise ValueError(f'fixture filename must not contain a directory: {fixture.filename}')
    return path


def sha256_file(path: Path) -> str:
    """Return a file's SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()
