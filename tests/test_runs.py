from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from microstructure_lab.cli import app
from microstructure_lab.execution.comparison import run_strategy_comparison
from microstructure_lab.execution.parent_order import ExecutionSide
from microstructure_lab.execution.simulator import run_execution_file
from microstructure_lab.runs.manifest import (
    create_manifest,
    file_hash,
    list_manifests,
    load_manifest,
    save_manifest,
    stable_hash,
)
from microstructure_lab.simulation.synthetic import generate_events, write_events_csv


def test_manifest_creation_and_load(tmp_path: Path) -> None:
    manifest = create_manifest(
        run_id="run-1",
        command="microstructure-lab test",
        status="completed",
        config={"a": 1},
        output_paths={"result": tmp_path / "result.json"},
        scenario="normal",
        seed=42,
        strategy="twap",
        metrics={"fill_rate": 1.0},
    )

    path = save_manifest(manifest, tmp_path, index_path=tmp_path / "index.json")
    loaded = load_manifest(path)

    assert loaded.run_id == "run-1"
    assert loaded.command == "microstructure-lab test"
    assert loaded.config_hash == stable_hash({"a": 1})


def test_hash_stability(tmp_path: Path) -> None:
    path = tmp_path / "input.csv"
    path.write_text("a,b\n1,2\n")

    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})
    assert file_hash(path) == file_hash(path)


def test_failed_run_recording(tmp_path: Path) -> None:
    missing_events = tmp_path / "missing.csv"
    output = tmp_path / "failed"

    with pytest.raises(FileNotFoundError):
        run_execution_file(
            events_path=missing_events,
            output_dir=output,
            strategy_name="twap",
            side=ExecutionSide.BUY,
            quantity=100,
            duration=10,
        )

    manifest = load_manifest(output)
    assert manifest.status == "failed"
    assert manifest.error


def test_load_and_list_behavior(tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    first = create_manifest(
        run_id="a",
        command="cmd a",
        status="completed",
        config={"run": "a"},
    )
    second = create_manifest(
        run_id="b",
        command="cmd b",
        status="completed",
        config={"run": "b"},
    )

    from microstructure_lab.runs.manifest import update_run_index

    update_run_index(first, tmp_path / "a", index_path=index_path)
    update_run_index(second, tmp_path / "b", index_path=index_path)

    listed = list_manifests(index_path=index_path)
    assert [manifest.run_id for manifest in listed] == ["a", "b"]


def test_reproducibility_command_included_for_comparison(tmp_path: Path) -> None:
    output = tmp_path / "comparison"

    run_strategy_comparison(
        strategies=["twap", "pov"],
        scenario="normal",
        seed=42,
        output_dir=output,
        side=ExecutionSide.BUY,
        quantity=100,
        duration=30,
        event_count=50,
    )

    manifest = load_manifest(output)
    summary = json.loads((output / "summary.json").read_text())
    assert manifest.status == "completed"
    assert "microstructure-lab execute compare" in manifest.command
    assert manifest.input_hash is not None
    assert summary["seed"] == 42


def test_execution_manifest_records_input_hash(tmp_path: Path) -> None:
    events = generate_events(scenario="normal", seed=1, event_count=40)
    events_path = tmp_path / "events.csv"
    output = tmp_path / "run"
    write_events_csv(events, events_path)

    run_execution_file(
        events_path=events_path,
        output_dir=output,
        strategy_name="twap",
        side=ExecutionSide.BUY,
        quantity=100,
        duration=30,
    )

    manifest = load_manifest(output)
    assert manifest.status == "completed"
    assert manifest.input_hash == file_hash(events_path)
    assert manifest.metrics["fill_rate"] >= 0


def test_runs_cli_list_and_show(tmp_path: Path) -> None:
    output = tmp_path / "comparison"
    runner = CliRunner()

    run_strategy_comparison(
        strategies=["twap", "pov"],
        scenario="normal",
        seed=99,
        output_dir=output,
        side=ExecutionSide.BUY,
        quantity=100,
        duration=30,
        event_count=50,
    )

    listed = runner.invoke(app, ["runs", "list"])
    shown = runner.invoke(app, ["runs", "show", "--run-id", "comparison-normal-99-twap-pov"])

    assert listed.exit_code == 0
    assert "comparison-normal-99-twap-pov" in listed.output
    assert shown.exit_code == 0
    assert '"run_id": "comparison-normal-99-twap-pov"' in shown.output
