from __future__ import annotations

from typer.testing import CliRunner

from microstructure_lab import __version__
from microstructure_lab.cli import app


def test_package_has_version() -> None:
    assert __version__


def test_cli_help() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Market microstructure research" in result.output


def test_cli_version() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "microstructure-lab" in result.output


def test_cli_generate_and_replay(tmp_path) -> None:
    runner = CliRunner()
    events_path = tmp_path / "events.csv"
    output_dir = tmp_path / "book_replay"

    generate = runner.invoke(
        app,
        [
            "simulate",
            "generate",
            "--scenario",
            "normal",
            "--seed",
            "42",
            "--events",
            "30",
            "--output",
            str(events_path),
        ],
    )
    replay = runner.invoke(
        app,
        ["book", "replay", "--events", str(events_path), "--output", str(output_dir)],
    )

    assert generate.exit_code == 0
    assert events_path.exists()
    assert replay.exit_code == 0
    assert (output_dir / "trades.csv").exists()
    assert (output_dir / "snapshots.csv").exists()


def test_cli_execute_run(tmp_path) -> None:
    runner = CliRunner()
    events_path = tmp_path / "events.csv"
    output_dir = tmp_path / "twap_run"

    generate = runner.invoke(
        app,
        [
            "simulate",
            "generate",
            "--scenario",
            "normal",
            "--seed",
            "42",
            "--events",
            "40",
            "--output",
            str(events_path),
        ],
    )
    execute = runner.invoke(
        app,
        [
            "execute",
            "run",
            "--strategy",
            "twap",
            "--side",
            "buy",
            "--quantity",
            "100",
            "--duration",
            "40",
            "--events",
            str(events_path),
            "--output",
            str(output_dir),
        ],
    )

    assert generate.exit_code == 0
    assert execute.exit_code == 0
    assert (output_dir / "child_orders.csv").exists()
    assert (output_dir / "fills.csv").exists()
    assert (output_dir / "result.json").exists()
