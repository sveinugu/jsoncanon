# jsoncanon

Typed Python implementation of JSON Canonicalization Scheme as described in
[RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html). The initial release (v0.2.x) is a partial release focused on the
features needed by the [Sequence Collections working group](https://seqcol.readthedocs.io/) in the
[Global Alliance for Genomics and Health (GA4GH)](https://www.ga4gh.org/).

## Usage

```
>>> import json
>>> from jsoncanon import canonicalize, load_canonicalized
>>>
>>> data = json.loads('{ "b": [1,3,7], "a": { "y": true, "x": null } }')
>>> canonicalize(data)
b'{"a":{"x":null,"y":true},"b":[1,3,7]}'

>>> encoded = canonicalize(9007199254740992, big_ints='uniquely_as_string')
>>> load_canonicalized(encoded, big_ints='uniquely_as_string')
9007199254740992
```

## Benchmark

Compare canonicalization and canonical decoding across `jsoncanon`, `rfc8785`,
and `jcs` using checksum-pinned real-world fixtures:

```shell
uv run python -m rfc8785_benchmarks.compare_libraries
```

The default suite uses checksum-pinned snapshots from
[sample.json-format.com](https://sample.json-format.com/). It includes small API-like
payloads, 1 MiB record collections, and a 10 MiB e-commerce dataset.
Download the ignored local fixtures once, then run the suite:

```shell
uv run python -m rfc8785_benchmarks.download_datasets
uv run python -m rfc8785_benchmarks.compare_libraries
```

The benchmark verifies every local fixture's SHA-256 before timing and verifies each
implementation's canonical output against `jsoncanon`. Real fixtures use size-based
call counts by default; pass `--iterations` to override them. The output presents
canonicalization, stream writing, decoding, and validation with each implementation in a
separate column. Use `--suite quick` for the two smallest fixtures.
