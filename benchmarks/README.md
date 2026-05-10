# Benchmarks

This directory contains deterministic benchmark workloads for `sacagawea`.

Run the default small suite:

```powershell
uv run python -m benchmarks.run_benchmarks --dataset small
```

Run one case across all operations:

```powershell
uv run python -m benchmarks.run_benchmarks -d medium -c deep_path_32
```

Run only interpretation timing after parsing once:

```powershell
uv run python -m benchmarks.run_benchmarks -d medium -o interpret
```

Write JSON output:

```powershell
uv run python -m benchmarks.run_benchmarks --dataset small --output storage/tmp/benchmarks/small.json
```

Compare two JSON result files:

```powershell
uv run python -m benchmarks.run_benchmarks compare benchmarks/results-medium.json benchmarks/results-large.json
```

List available cases:

```powershell
uv run python -m benchmarks.run_benchmarks --list
```

Show parameter help:

```powershell
uv run python -m benchmarks.run_benchmarks --help
```

The runner uses Rich output. While benchmarks run it prints completed
measurements and keeps a progress bar with total measurements, completed
measurements, elapsed time, and average measurement speed. Use `--quiet` to hide
progress output and print only the final results table.

## Datasets

Datasets are generated in memory instead of checked in as large JSON files.

| Dataset | Records | Intended Use |
|---|---:|---|
| `small` | 100 | Fast smoke checks while changing benchmark code. |
| `medium` | 10,000 | Normal local comparison runs. |
| `large` | 100,000 | Longer local runs before publishing performance claims. |

Each record includes scalar fields, nested dictionaries, list-of-dictionaries,
scalar lists, regex-oriented strings, and timezone-aware datetimes.

## Operations

| Operation | Measures |
|---|---|
| `parse` | Parser and parse-time validation cost only. |
| `interpret` | Runtime evaluation cost using an AST parsed outside the timed block. |
| `evaluate` | End-to-end `parse` plus `interpret` cost. |

Every benchmark case validates the expected match count before timing starts so
dataset or query drift fails early.
