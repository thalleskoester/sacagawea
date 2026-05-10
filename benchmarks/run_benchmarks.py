"""Command-line benchmark runner for sacagawea."""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal, cast

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from benchmarks.datasets import build_dataset
from benchmarks.queries import DEFAULT_OPERATIONS, QUERY_CASES, QUERY_CASES_BY_NAME
from sacagawea import evaluate, interpret, parse

if TYPE_CHECKING:
    from collections.abc import Callable

    from rich.progress import TaskID

    from benchmarks.queries import BenchmarkOperation, QueryCase
    from sacagawea import AST

type ProgressEventKind = Literal[
    "status", "start", "measurement_start", "execution_complete", "measurement_complete", "complete"
]

app = typer.Typer(
    add_completion=False,
    help="Run deterministic sacagawea benchmark workloads.",
    invoke_without_command=True,
)


class DatasetOption(StrEnum):
    """Dataset sizes accepted by the benchmark CLI."""

    small = "small"
    medium = "medium"
    large = "large"


class OperationOption(StrEnum):
    """Benchmark operations accepted by the benchmark CLI."""

    parse = "parse"
    interpret = "interpret"
    evaluate = "evaluate"


@dataclass(frozen=True, slots=True)
class BenchmarkMeasurement:
    """Timing result for one case and operation."""

    dataset: str
    dataset_size: int
    case_name: str
    group: str
    operation: BenchmarkOperation
    expected_matches: int
    repeat: int
    warmup: int
    median_ms: float
    min_ms: float
    max_ms: float
    samples_ms: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class BenchmarkProgressEvent:
    """Structured event emitted while benchmarks are running."""

    kind: ProgressEventKind
    message: str
    total: int | None = None
    case_name: str | None = None
    operation: str | None = None
    measurement: BenchmarkMeasurement | None = None


def run_benchmark_suite(
    *,
    dataset_name: str,
    selected_cases: tuple[str, ...] | None = None,
    selected_operations: tuple[BenchmarkOperation, ...] | None = None,
    repeat: int = 8,
    warmup: int = 2,
    progress: Callable[[BenchmarkProgressEvent], None] | None = None,
) -> list[BenchmarkMeasurement]:
    """Run benchmark measurements for a dataset and selected cases.

    Returns:
        Measurements in case order and then operation order.

    Raises:
        ValueError: If repeat, warmup, selected cases, or selected operations
            are invalid.

    """
    if repeat < 1:
        message = "repeat must be at least 1"
        raise ValueError(message)
    if warmup < 0:
        message = "warmup must be non-negative"
        raise ValueError(message)

    _report(progress, "status", f"Building dataset '{dataset_name}'")
    dataset = build_dataset(dataset_name)
    _report(progress, "status", f"Built dataset '{dataset.name}' with {len(dataset.records)} records")
    cases = _resolve_cases(selected_cases)
    operations = selected_operations or DEFAULT_OPERATIONS
    _validate_operations(operations)
    total_measurements = len(cases) * len(operations) * (warmup + repeat)
    _report(
        progress,
        "start",
        f"Running {total_measurements} benchmark executions across {len(cases)} case(s)",
        total=total_measurements,
    )

    measurements: list[BenchmarkMeasurement] = []
    for case in cases:
        expected_matches = dataset.expected_counts[case.name]
        _report(progress, "status", f"Validating {case.name} expected match count")
        _validate_case(case, dataset.records, expected_matches)
        parsed = parse(case.query)
        for operation in operations:
            _report(
                progress,
                "measurement_start",
                f"Running {case.name} {operation} ({warmup} warmup, {repeat} timed)",
                case_name=case.name,
                operation=operation,
            )
            benchmark = _operation_callable(operation, case, dataset.records, parsed)
            for _ in range(warmup):
                benchmark()
                _report(
                    progress,
                    "execution_complete",
                    f"Completed warmup for {case.name} {operation}",
                    case_name=case.name,
                    operation=operation,
                )
            samples: list[float] = []
            for _ in range(repeat):
                samples.append(_time_once_ms(benchmark))
                _report(
                    progress,
                    "execution_complete",
                    f"Completed timed sample for {case.name} {operation}",
                    case_name=case.name,
                    operation=operation,
                )
            measurement = BenchmarkMeasurement(
                dataset=dataset.name,
                dataset_size=len(dataset.records),
                case_name=case.name,
                group=case.group,
                operation=operation,
                expected_matches=expected_matches,
                repeat=repeat,
                warmup=warmup,
                median_ms=statistics.median(samples),
                min_ms=min(samples),
                max_ms=max(samples),
                samples_ms=tuple(samples),
            )
            measurements.append(measurement)
            _report(
                progress,
                "measurement_complete",
                f"Completed {case.name} {operation}",
                case_name=case.name,
                operation=operation,
                measurement=measurement,
            )
    _report(progress, "complete", f"Completed {len(measurements)} measurements", total=total_measurements)
    return measurements


@app.callback()
def main(
    context: typer.Context,
    *,
    dataset: Annotated[
        DatasetOption,
        typer.Option(
            "--dataset",
            "-d",
            help="Dataset size to generate before timing. Use small for smoke checks, medium for normal local runs, "
            "and large for longer comparison runs.",
        ),
    ] = DatasetOption.small,
    case: Annotated[
        list[str] | None,
        typer.Option(
            "--case",
            "-c",
            help="Benchmark case name to run. Repeat the option to run multiple cases. Omit it to run every case.",
        ),
    ] = None,
    operation: Annotated[
        list[OperationOption] | None,
        typer.Option(
            "--operation",
            "-o",
            help="Operation to time. Repeat the option to run multiple operations. Defaults to parse, interpret, "
            "and evaluate.",
        ),
    ] = None,
    repeat: Annotated[
        int,
        typer.Option(
            "--repeat",
            "-r",
            min=1,
            help="Number of timed samples to collect for each selected case and operation.",
        ),
    ] = 8,
    warmup: Annotated[
        int,
        typer.Option(
            "--warmup",
            "-w",
            min=0,
            help="Number of untimed warmup executions before collecting timed samples.",
        ),
    ] = 2,
    output: Annotated[
        Path | None,
        typer.Option(
            "--output",
            help="Optional JSON file path for machine-readable benchmark results.",
        ),
    ] = None,
    list_cases: Annotated[
        bool,
        typer.Option(
            "--list",
            help="List benchmark cases with their groups and descriptions, then exit without running benchmarks.",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress progress messages and print only the final result table.",
        ),
    ] = False,
) -> None:
    """Run selected benchmark cases against generated datasets."""
    if context.invoked_subcommand is not None:
        return

    console = Console()
    if list_cases:
        _print_available_cases(console)
        return

    try:
        if quiet:
            measurements = run_benchmark_suite(
                dataset_name=dataset.value,
                selected_cases=tuple(case) if case else None,
                selected_operations=tuple(item.value for item in operation) if operation else None,
                repeat=repeat,
                warmup=warmup,
            )
        else:
            with RichBenchmarkProgress(console) as progress:
                measurements = run_benchmark_suite(
                    dataset_name=dataset.value,
                    selected_cases=tuple(case) if case else None,
                    selected_operations=tuple(item.value for item in operation) if operation else None,
                    repeat=repeat,
                    warmup=warmup,
                    progress=progress,
                )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    except AssertionError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    _print_measurements(console, measurements)
    if output is not None:
        _write_json(output, measurements)


@app.command()
def compare(
    baseline: Annotated[
        Path,
        typer.Argument(
            help="Path to the baseline benchmark JSON file, usually the smaller or older run.",
        ),
    ],
    contender: Annotated[
        Path,
        typer.Argument(
            help="Path to the contender benchmark JSON file, usually the larger or newer run.",
        ),
    ],
) -> None:
    """Compare two benchmark JSON files by case and operation."""
    console = Console()
    baseline_rows = _read_measurements_json(baseline)
    contender_rows = _read_measurements_json(contender)
    _print_comparison(console, baseline_rows, contender_rows)


def _resolve_cases(selected_cases: tuple[str, ...] | None) -> tuple[QueryCase, ...]:
    if selected_cases is None:
        return QUERY_CASES
    unknown = sorted(set(selected_cases).difference(QUERY_CASES_BY_NAME))
    if unknown:
        choices = ", ".join(sorted(QUERY_CASES_BY_NAME))
        message = f"Unknown benchmark case(s) {', '.join(unknown)}; expected one of: {choices}"
        raise ValueError(message)
    return tuple(QUERY_CASES_BY_NAME[name] for name in selected_cases)


def _validate_operations(operations: tuple[BenchmarkOperation, ...]) -> None:
    unknown = sorted(set(operations).difference(DEFAULT_OPERATIONS))
    if unknown:
        choices = ", ".join(DEFAULT_OPERATIONS)
        message = f"Unknown operation(s) {', '.join(unknown)}; expected one of: {choices}"
        raise ValueError(message)


def _validate_case(case: QueryCase, records: list[dict], expected_matches: int) -> None:
    actual_matches = len(evaluate(case.query, records).result)
    if actual_matches != expected_matches:
        message = f"Benchmark case {case.name!r} expected {expected_matches} matches but returned {actual_matches}"
        raise AssertionError(message)


def _operation_callable(
    operation: BenchmarkOperation, case: QueryCase, records: list[dict], parsed: AST
) -> Callable[[], object]:
    if operation == "parse":
        return lambda: parse(case.query)
    if operation == "interpret":
        return lambda: interpret(parsed, records)
    if operation == "evaluate":
        return lambda: evaluate(case.query, records)
    raise AssertionError(operation)


def _time_once_ms(benchmark: Callable[[], object]) -> float:
    start = time.perf_counter_ns()
    benchmark()
    elapsed_ns = time.perf_counter_ns() - start
    return elapsed_ns / 1_000_000


def _read_measurements_json(path: Path) -> list[BenchmarkMeasurement]:
    try:
        raw_payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        message = f"Could not read benchmark results from {path}: {exc}"
        raise typer.BadParameter(message) from exc
    except json.JSONDecodeError as exc:
        message = f"Benchmark results file is not valid JSON: {path}"
        raise typer.BadParameter(message) from exc
    if not isinstance(raw_payload, list):
        message = f"Benchmark results file must contain a JSON array: {path}"
        raise typer.BadParameter(message)
    measurements: list[BenchmarkMeasurement] = []
    for index, item in enumerate(raw_payload):
        if not isinstance(item, dict):
            message = f"Benchmark result at index {index} must be an object: {path}"
            raise typer.BadParameter(message)
        measurements.append(_measurement_from_json_item(item, path, index))
    return measurements


def _measurement_from_json_item(item: dict, path: Path, index: int) -> BenchmarkMeasurement:
    try:
        operation = str(item["operation"])
        if operation not in DEFAULT_OPERATIONS:
            message = f"Benchmark result at index {index} has an invalid operation: {path}"
            raise typer.BadParameter(message)
        return BenchmarkMeasurement(
            dataset=str(item["dataset"]),
            dataset_size=int(item["dataset_size"]),
            case_name=str(item["case_name"]),
            group=str(item["group"]),
            operation=cast("BenchmarkOperation", operation),
            expected_matches=int(item["expected_matches"]),
            repeat=int(item["repeat"]),
            warmup=int(item["warmup"]),
            median_ms=float(item["median_ms"]),
            min_ms=float(item["min_ms"]),
            max_ms=float(item["max_ms"]),
            samples_ms=tuple(float(sample) for sample in item["samples_ms"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        message = f"Benchmark result at index {index} has an invalid shape: {path}"
        raise typer.BadParameter(message) from exc


def _report(
    progress: Callable[[BenchmarkProgressEvent], None] | None,
    kind: ProgressEventKind,
    message: str,
    *,
    total: int | None = None,
    case_name: str | None = None,
    operation: str | None = None,
    measurement: BenchmarkMeasurement | None = None,
) -> None:
    if progress is not None:
        progress(
            BenchmarkProgressEvent(
                kind=kind,
                message=message,
                total=total,
                case_name=case_name,
                operation=operation,
                measurement=measurement,
            )
        )


class MeasurementSpeedColumn(ProgressColumn):
    """Render average completed measurements per second."""

    def render(self, task: object) -> Text:
        """Render average speed for the current progress task."""
        speed = getattr(task, "speed", None)
        if speed is None:
            return Text("avg --/s", style="progress.data.speed")
        return Text(f"avg {speed:.2f}/s", style="progress.data.speed")


class RichBenchmarkProgress:
    """Render benchmark progress events with Rich."""

    def __init__(self, console: Console) -> None:
        """Initialize the Rich progress renderer."""
        self._console = console
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("elapsed"),
            TimeElapsedColumn(),
            MeasurementSpeedColumn(),
            console=console,
        )
        self._task_id: TaskID | None = None

    def __enter__(self) -> RichBenchmarkProgress:
        """Start rendering progress."""
        self._progress.start()
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        """Stop rendering progress."""
        self._progress.stop()

    def __call__(self, event: BenchmarkProgressEvent) -> None:
        """Handle one benchmark progress event."""
        if event.kind == "status":
            self._progress.console.print(f"[dim]{event.message}[/]")
        elif event.kind == "start":
            total = 0 if event.total is None else event.total
            self._progress.console.print(f"[dim]{event.message}[/]")
            self._task_id = self._progress.add_task(event.message, total=total)
        elif event.kind == "measurement_start":
            if self._task_id is not None:
                self._progress.update(self._task_id, description=event.message)
        elif event.kind == "execution_complete":
            if self._task_id is not None:
                self._progress.advance(self._task_id)
        elif event.kind == "measurement_complete":
            if event.measurement is not None:
                self._progress.console.print(
                    "[green]completed[/] "
                    f"{event.measurement.case_name} {event.measurement.operation} "
                    f"median={event.measurement.median_ms:.3f}ms "
                    f"matches={event.measurement.expected_matches}"
                )
        elif event.kind == "complete" and self._task_id is not None:
            self._progress.update(self._task_id, description=event.message)


def _print_available_cases(console: Console) -> None:
    table = Table(title="Benchmark Cases")
    table.add_column("Case", style="cyan")
    table.add_column("Group", style="magenta")
    table.add_column("Description")
    for case in QUERY_CASES:
        table.add_row(case.name, case.group, case.description)
    console.print(table)


def _print_measurements(console: Console, measurements: list[BenchmarkMeasurement]) -> None:
    table = Table(title="Benchmark Results")
    table.add_column("Dataset", style="cyan")
    table.add_column("Size", justify="right")
    table.add_column("Operation", style="magenta")
    table.add_column("Case")
    table.add_column("Median ms", justify="right")
    table.add_column("Min ms", justify="right")
    table.add_column("Max ms", justify="right")
    table.add_column("Matches", justify="right")
    for measurement in measurements:
        table.add_row(
            measurement.dataset,
            str(measurement.dataset_size),
            measurement.operation,
            measurement.case_name,
            f"{measurement.median_ms:.3f}",
            f"{measurement.min_ms:.3f}",
            f"{measurement.max_ms:.3f}",
            str(measurement.expected_matches),
        )
    console.print(table)


def _print_comparison(
    console: Console,
    baseline_rows: list[BenchmarkMeasurement],
    contender_rows: list[BenchmarkMeasurement],
) -> None:
    baseline_index = _index_measurements(baseline_rows)
    contender_index = _index_measurements(contender_rows)
    common_keys = sorted(set(baseline_index).intersection(contender_index))
    if not common_keys:
        console.print("[yellow]No matching benchmark case/operation rows found.[/]")
        return

    table = Table(title="Benchmark Comparison")
    table.add_column("Case")
    table.add_column("Operation", style="magenta")
    table.add_column("Baseline ms", justify="right")
    table.add_column("Contender ms", justify="right")
    table.add_column("Ratio", justify="right")
    table.add_column("Baseline ms/1k", justify="right")
    table.add_column("Contender ms/1k", justify="right")
    table.add_column("Contender Spread", justify="right")

    baseline_label = _dataset_summary(baseline_rows)
    contender_label = _dataset_summary(contender_rows)
    console.print(f"[dim]Baseline: {baseline_label} | Contender: {contender_label}[/]")
    for key in common_keys:
        baseline = baseline_index[key]
        contender = contender_index[key]
        ratio = contender.median_ms / baseline.median_ms if baseline.median_ms else 0.0
        contender_spread = contender.max_ms / contender.min_ms if contender.min_ms else 0.0
        row_style = "yellow" if ratio >= 12.0 or contender_spread >= 1.5 else None
        table.add_row(
            baseline.case_name,
            baseline.operation,
            f"{baseline.median_ms:.3f}",
            f"{contender.median_ms:.3f}",
            f"{ratio:.2f}x",
            f"{_milliseconds_per_thousand_records(baseline):.3f}",
            f"{_milliseconds_per_thousand_records(contender):.3f}",
            f"{contender_spread:.2f}x",
            style=row_style,
        )
    console.print(table)


def _index_measurements(measurements: list[BenchmarkMeasurement]) -> dict[tuple[str, str], BenchmarkMeasurement]:
    return {(measurement.case_name, measurement.operation): measurement for measurement in measurements}


def _dataset_summary(measurements: list[BenchmarkMeasurement]) -> str:
    labels = {f"{measurement.dataset} ({measurement.dataset_size})" for measurement in measurements}
    return ", ".join(sorted(labels))


def _milliseconds_per_thousand_records(measurement: BenchmarkMeasurement) -> float:
    if measurement.dataset_size <= 0:
        return 0.0
    return measurement.median_ms / (measurement.dataset_size / 1_000)


def _write_json(path: Path, measurements: list[BenchmarkMeasurement]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(measurement) for measurement in measurements]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    app()
