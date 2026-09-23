"""Download checksum-pinned real-world benchmark fixtures."""

from __future__ import annotations

import argparse
import shutil
import urllib.request
from pathlib import Path

from rfc8785_benchmarks.dataset_fixtures import (
    FIXTURES_PATH,
    available_suites,
    fixture_path,
    load_manifest,
    sha256_file,
)


def download_fixture(url: str, destination: Path) -> None:
    """Download a fixture atomically."""
    temporary = destination.with_suffix(f'{destination.suffix}.part')
    request = urllib.request.Request(url, headers={'User-Agent': 'jsoncanon-benchmark/1.0'})
    try:
        with urllib.request.urlopen(request) as response, temporary.open('wb') as file:
            shutil.copyfileobj(response, file)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=available_suites(), default='default')
    parser.add_argument('--force', action='store_true', help='redownload valid existing fixtures')
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fixtures = [fixture for fixture in load_manifest() if args.suite in fixture.suites]
    FIXTURES_PATH.mkdir(parents=True, exist_ok=True)

    for fixture in fixtures:
        destination = fixture_path(fixture)
        if destination.exists() and sha256_file(destination) == fixture.sha256 and not args.force:
            print(f'{fixture.identifier}: verified {destination}')
            continue
        print(f'{fixture.identifier}: downloading {fixture.url}')
        download_fixture(fixture.url, destination)
        actual_sha256 = sha256_file(destination)
        if actual_sha256 != fixture.sha256:
            destination.unlink()
            raise RuntimeError(
                f'{fixture.identifier}: SHA-256 mismatch: expected {fixture.sha256}, '
                f'got {actual_sha256}'
            )
        print(f'{fixture.identifier}: downloaded and verified {destination}')


if __name__ == '__main__':
    main()
