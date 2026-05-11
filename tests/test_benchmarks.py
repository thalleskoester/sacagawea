import json
from dataclasses import asdict

from typer.testing import CliRunner

from benchmarks.datasets import DATASET_SIZES, build_dataset
from benchmarks.queries import QUERY_CASES
from benchmarks.run_benchmarks import app, run_benchmark_suite
from sacagawea import evaluate

RUNNER = CliRunner()


def test_small_benchmark_dataset_is_deterministic():
    first = build_dataset("small")
    second = build_dataset("small")

    assert first.name == "small"
    assert len(first.records) == DATASET_SIZES["small"]
    assert first.records == second.records
    assert first.expected_counts == second.expected_counts
    assert (
        first.records[0]["deep"]["level_01"]["level_02"]["level_03"]["level_04"]["level_05"]["level_06"]["value"]
        == "target"
    )


def test_benchmark_queries_match_expected_counts_on_small_dataset():
    dataset = build_dataset("small")

    for case in QUERY_CASES:
        result = evaluate(case.query, dataset.records)

        assert len(result.result) == dataset.expected_counts[case.name], case.name


def test_benchmark_runner_returns_parse_interpret_and_evaluate_measurements():
    measurements = run_benchmark_suite(
        dataset_name="small",
        selected_cases=("scalar_eq",),
        selected_operations=("parse", "interpret", "evaluate"),
        repeat=1,
        warmup=0,
    )

    assert [measurement.operation for measurement in measurements] == ["parse", "interpret", "evaluate"]
    assert {measurement.case_name for measurement in measurements} == {"scalar_eq"}
    assert all(measurement.median_ms >= 0 for measurement in measurements)


def test_benchmark_cli_help_documents_options():
    result = RUNNER.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "--dataset" in result.output
    assert "Dataset size to generate" in result.output
    assert "--operation" in result.output
    assert "Operation to time" in result.output
    assert "--output" in result.output


def test_benchmark_cli_prints_progress_while_running():
    result = RUNNER.invoke(app, ["--dataset", "small", "--case", "scalar_eq", "--repeat", "1", "--warmup", "0"])

    assert result.exit_code == 0
    assert "Building dataset 'small'" in result.output
    assert "completed scalar_eq parse" in result.output
    assert "completed scalar_eq interpret" in result.output
    assert "completed scalar_eq evaluate" in result.output
    assert "Completed 3 measurements" in result.output
    assert "3/3" in result.output
    assert "avg" in result.output


def test_benchmark_cli_progress_counts_warmups_and_repeats():
    result = RUNNER.invoke(
        app,
        [
            "--dataset",
            "small",
            "--case",
            "scalar_eq",
            "--operation",
            "parse",
            "--repeat",
            "2",
            "--warmup",
            "1",
        ],
    )

    assert result.exit_code == 0
    assert "Running 3 benchmark executions" in result.output
    assert "Completed 1 measurements" in result.output
    assert "3/3" in result.output


def test_benchmark_cli_compares_result_files(tmp_path):
    baseline = run_benchmark_suite(
        dataset_name="small",
        selected_cases=("scalar_eq",),
        selected_operations=("parse",),
        repeat=1,
        warmup=0,
    )
    contender = run_benchmark_suite(
        dataset_name="small",
        selected_cases=("scalar_eq",),
        selected_operations=("parse",),
        repeat=1,
        warmup=0,
    )
    baseline_path = tmp_path / "baseline.json"
    contender_path = tmp_path / "contender.json"
    baseline_path.write_text(json.dumps([asdict(item) for item in baseline]), encoding="utf-8")
    contender_path.write_text(json.dumps([asdict(item) for item in contender]), encoding="utf-8")

    result = RUNNER.invoke(app, ["compare", str(baseline_path), str(contender_path)])

    assert result.exit_code == 0
    assert "Benchmark Comparison" in result.output
    assert "Baseline:" in result.output
    assert "parse" in result.output
    assert "Ratio" in result.output


def test_benchmark_cli_sorts_results_table():
    result = RUNNER.invoke(
        app,
        [
            "--dataset",
            "small",
            "--case",
            "scalar_eq",
            "--case",
            "many_args",
            "--operation",
            "interpret",
            "--repeat",
            "1",
            "--warmup",
            "0",
            "--sort",
            "median-ms",
            "--descending",
            "--quiet",
        ],
    )

    assert result.exit_code == 0
    assert result.output.find("many_args") < result.output.find("scalar_eq")


def test_benchmark_cli_sorts_comparison_table(tmp_path):
    baseline = run_benchmark_suite(
        dataset_name="small",
        selected_cases=("scalar_eq", "many_args"),
        selected_operations=("interpret",),
        repeat=1,
        warmup=0,
    )
    contender = run_benchmark_suite(
        dataset_name="small",
        selected_cases=("scalar_eq", "many_args"),
        selected_operations=("interpret",),
        repeat=1,
        warmup=0,
    )
    baseline_path = tmp_path / "baseline.json"
    contender_path = tmp_path / "contender.json"
    baseline_path.write_text(json.dumps([asdict(item) for item in baseline]), encoding="utf-8")
    contender_path.write_text(json.dumps([asdict(item) for item in contender]), encoding="utf-8")

    result = RUNNER.invoke(app, ["compare", str(baseline_path), str(contender_path), "--sort", "baseline-ms"])

    assert result.exit_code == 0
    assert "Benchmark Comparison" in result.output
