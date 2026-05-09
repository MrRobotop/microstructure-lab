from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from microstructure_lab.cli import app
from microstructure_lab.reporting.demo import run_demo
from microstructure_lab.runs.manifest import find_manifest


def test_demo_workflow_writes_expected_artifacts(tmp_path: Path) -> None:
    report = run_demo(output_dir=tmp_path / "demo")

    assert report.exists()
    assert (tmp_path / "demo" / "events.csv").exists()
    assert (tmp_path / "demo" / "summary.json").exists()
    assert (tmp_path / "demo" / "twap" / "result.json").exists()
    assert (tmp_path / "demo" / "pov" / "result.json").exists()
    assert (tmp_path / "demo" / "book_replay" / "trades.csv").exists()
    assert (tmp_path / "demo" / "book_replay" / "snapshots.csv").exists()

    text = report.read_text()
    assert "Strategy Comparison Report" in text
    assert "synthetic execution simulation" in text


def test_demo_registers_runs_for_dashboard_and_runs_cli(tmp_path: Path) -> None:
    run_demo(output_dir=tmp_path / "demo")

    comparison_manifest = find_manifest("comparison-normal-42-twap-pov")
    replay_manifest = find_manifest("book-replay-events")

    assert comparison_manifest is not None
    assert comparison_manifest.status == "completed"
    assert replay_manifest is not None
    assert replay_manifest.status == "completed"


def test_cli_demo_prints_report_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()

    result = runner.invoke(app, ["demo"])

    assert result.exit_code == 0
    assert "Demo report:" in result.output
    report_path = Path(result.output.strip().removeprefix("Demo report: "))
    assert report_path.exists()
    assert report_path.name == "comparison_report.md"
