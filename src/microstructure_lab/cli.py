"""Command-line interface for Microstructure-Lab."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from microstructure_lab import __version__
from microstructure_lab.analytics.cost_report import write_cost_report
from microstructure_lab.benchmarking.engine import benchmark_engine as run_engine_benchmark
from microstructure_lab.benchmarking.engine import write_benchmark_json
from microstructure_lab.execution.comparison import run_strategy_comparison
from microstructure_lab.execution.parent_order import ExecutionSide
from microstructure_lab.execution.simulator import run_execution_file
from microstructure_lab.reporting.demo import run_demo
from microstructure_lab.runs.manifest import find_manifest, list_manifests
from microstructure_lab.simulation.replay import replay_file
from microstructure_lab.simulation.synthetic import generate_events, write_events_csv

app = typer.Typer(
    name="microstructure-lab",
    help="Market microstructure research and execution simulation toolkit.",
    no_args_is_help=True,
)

simulate_app = typer.Typer(help="Generate synthetic market events.")
book_app = typer.Typer(help="Replay and inspect order book events.")
execute_app = typer.Typer(help="Run execution strategies.")
analytics_app = typer.Typer(help="Compute transaction cost analytics.")
benchmark_app = typer.Typer(help="Run matching engine benchmarks.")
api_app = typer.Typer(help="Serve stored run artifacts through an API.")
dashboard_app = typer.Typer(help="Launch the artifact dashboard.")
runs_app = typer.Typer(help="Inspect run manifests.")

app.add_typer(simulate_app, name="simulate")
app.add_typer(book_app, name="book")
app.add_typer(execute_app, name="execute")
app.add_typer(analytics_app, name="analytics")
app.add_typer(benchmark_app, name="benchmark")
app.add_typer(api_app, name="api")
app.add_typer(dashboard_app, name="dashboard")
app.add_typer(runs_app, name="runs")


def _not_implemented(phase: str) -> None:
    raise typer.BadParameter(
        f"This command is planned for {phase}. It is not implemented in the current phase."
    )


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the Microstructure-Lab version and exit.",
    ),
) -> None:
    """Run Microstructure-Lab commands."""
    if version:
        typer.echo(f"microstructure-lab {__version__}")
        raise typer.Exit()


@simulate_app.command("generate")
def simulate_generate(
    scenario: str = typer.Option("normal", help="Synthetic scenario name."),
    seed: int = typer.Option(42, help="Random seed for deterministic generation."),
    output: Annotated[Path, typer.Option(help="Output event file path.")] = ...,  # type: ignore[assignment]
    events: int = typer.Option(100, "--events", min=1, help="Number of synthetic events."),
) -> None:
    """Generate synthetic events."""
    try:
        generated = generate_events(scenario=scenario, seed=seed, event_count=events)
        write_events_csv(generated, output)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Wrote {len(generated)} synthetic events to {output}")


@book_app.command("replay")
def book_replay(
    events: Annotated[Path, typer.Option(help="Input synthetic events file.")] = ...,  # type: ignore[assignment]
    output: Annotated[Path, typer.Option(help="Output artifact directory.")] = ...,  # type: ignore[assignment]
) -> None:
    """Replay events through the C++ order book."""
    try:
        command = f"microstructure-lab book replay --events {events} --output {output}"
        trades_path, snapshots_path = replay_file(events, output, command=command)
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Wrote replay trades to {trades_path}")
    typer.echo(f"Wrote replay snapshots to {snapshots_path}")


@execute_app.command("run")
def execute_run(
    strategy: str = typer.Option(..., help="Execution strategy name."),
    side: str = typer.Option(..., help="Parent order side: buy or sell."),
    quantity: int = typer.Option(..., help="Parent order quantity."),
    duration: int = typer.Option(..., help="Execution duration in seconds."),
    events: Annotated[Path, typer.Option(help="Input synthetic events file.")] = ...,  # type: ignore[assignment]
    output: Annotated[Path, typer.Option(help="Output artifact directory.")] = ...,  # type: ignore[assignment]
) -> None:
    """Run one execution strategy."""
    try:
        result = run_execution_file(
            events_path=events,
            output_dir=output,
            strategy_name=strategy,
            side=ExecutionSide(side.lower()),
            quantity=quantity,
            duration=duration,
            command=(
                "microstructure-lab execute run "
                f"--strategy {strategy} --side {side} --quantity {quantity} "
                f"--duration {duration} --events {events} --output {output}"
            ),
        )
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(
        "Wrote execution result to "
        f"{output} realized={result.realized_quantity} unfilled={result.unfilled_quantity}"
    )


@execute_app.command("compare")
def execute_compare(
    strategies: str = typer.Option(..., help="Comma-separated strategy names."),
    scenario: str = typer.Option("normal", help="Synthetic scenario name."),
    seed: int = typer.Option(42, help="Random seed for deterministic generation."),
    output: Annotated[Path, typer.Option(help="Output artifact directory.")] = ...,  # type: ignore[assignment]
    side: str = typer.Option("buy", help="Parent order side: buy or sell."),
    quantity: int = typer.Option(10_000, help="Parent order quantity."),
    duration: int = typer.Option(60, help="Execution duration in event-time units."),
    events: int = typer.Option(200, "--events", min=1, help="Number of synthetic events."),
    arrival_price_ticks: int | None = typer.Option(
        None,
        help="Optional arrival price benchmark in integer ticks.",
    ),
) -> None:
    """Compare execution strategies on one scenario."""
    try:
        summary = run_strategy_comparison(
            strategies=[item.strip() for item in strategies.split(",") if item.strip()],
            scenario=scenario,
            seed=seed,
            output_dir=output,
            side=ExecutionSide(side.lower()),
            quantity=quantity,
            duration=duration,
            event_count=events,
            arrival_price_ticks=arrival_price_ticks,
            command=(
                "microstructure-lab execute compare "
                f"--strategies {strategies} --scenario {scenario} --seed {seed} "
                f"--side {side} --quantity {quantity} --duration {duration} "
                f"--events {events} --output {output}"
            ),
        )
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(
        "Wrote strategy comparison to "
        f"{output} strategies={','.join(summary['strategies'])}"
    )


@analytics_app.command("report")
def analytics_report(
    run: Annotated[Path, typer.Option(help="Input run artifact directory.")] = ...,  # type: ignore[assignment]
    output: Annotated[Path, typer.Option(help="Output Markdown report path.")] = ...,  # type: ignore[assignment]
    arrival_price_ticks: int | None = typer.Option(
        None,
        help="Optional arrival price benchmark in integer ticks.",
    ),
    benchmark_vwap_ticks: float | None = typer.Option(
        None,
        help="Optional VWAP benchmark in ticks.",
    ),
    spread_ticks: int | None = typer.Option(
        None,
        help="Optional spread estimate in ticks.",
    ),
    terminal_mid_ticks: int | None = typer.Option(
        None,
        help="Optional terminal mid price in ticks.",
    ),
) -> None:
    """Write a transaction cost report."""
    try:
        metrics = write_cost_report(
            run_dir=run,
            output_path=output,
            arrival_price_ticks=arrival_price_ticks,
            benchmark_vwap_ticks=benchmark_vwap_ticks,
            spread_ticks=spread_ticks,
            terminal_mid_ticks=terminal_mid_ticks,
            command=f"microstructure-lab analytics report --run {run} --output {output}",
        )
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(
        "Wrote analytics report to "
        f"{output} fill_rate={metrics.fill_rate:.4f} unfilled={metrics.unfilled_quantity}"
    )


@benchmark_app.command("engine")
def benchmark_engine(
    events: int = typer.Option(100_000, "--events", min=1, help="Number of events to benchmark."),
    scenario: str = typer.Option("normal", help="Synthetic scenario name."),
    seed: int = typer.Option(42, help="Random seed for deterministic generation."),
    warmup_events: int = typer.Option(
        1_000,
        "--warmup-events",
        min=0,
        help="Synthetic events to apply before timing.",
    ),
    output: Annotated[
        Path | None,
        typer.Option(help="Optional JSON output path for the benchmark observation."),
    ] = None,
) -> None:
    """Benchmark C++ matching engine event application on synthetic flow."""
    try:
        result = run_engine_benchmark(
            event_count=events,
            scenario=scenario,
            seed=seed,
            warmup_events=warmup_events,
        )
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    if output is not None:
        write_benchmark_json(result, output)

    typer.echo("Synthetic benchmark observation")
    typer.echo(f"scenario={result.scenario} seed={result.seed}")
    typer.echo(f"applied_events={result.applied_events} trades={result.trades}")
    typer.echo(f"elapsed_seconds={result.elapsed_seconds:.6f}")
    typer.echo(f"events_per_second={result.events_per_second:.2f}")
    typer.echo("limitation=single-process local observation, not a portable claim")
    if output is not None:
        typer.echo(f"json={output}")


@api_app.command("serve")
def api_serve(
    host: str = typer.Option("127.0.0.1", help="Host interface for the API server."),
    port: int = typer.Option(8000, help="Port for the API server."),
) -> None:
    """Serve run artifacts over HTTP."""
    try:
        import uvicorn
    except ImportError as exc:
        msg = "Install API dependencies with `python -m pip install -e '.[api]'`."
        raise typer.BadParameter(msg) from exc
    uvicorn.run("api.main:app", host=host, port=port)


@dashboard_app.command("run")
def dashboard_run(
    port: int = typer.Option(8501, help="Port for the Streamlit dashboard."),
) -> None:
    """Launch the dashboard."""
    try:
        from streamlit.web.cli import main as streamlit_main
    except ImportError as exc:
        msg = "Install dashboard dependencies with `python -m pip install -e '.[dashboard]'`."
        raise typer.BadParameter(msg) from exc

    import sys

    sys.argv = [
        "streamlit",
        "run",
        "dashboard/app.py",
        "--server.port",
        str(port),
    ]
    streamlit_main()


@runs_app.command("list")
def runs_list() -> None:
    """List indexed run manifests."""
    manifests = list_manifests()
    if not manifests:
        typer.echo("No indexed runs found.")
        return
    for manifest in manifests:
        typer.echo(
            f"{manifest.run_id}\t{manifest.status}\t{manifest.created_at}\t"
            f"{manifest.strategy or ''}\t{manifest.scenario or ''}"
        )


@runs_app.command("show")
def runs_show(
    run_id: Annotated[str, typer.Option(help="Run ID to show.")],
) -> None:
    """Show one indexed run manifest as JSON."""
    manifest = find_manifest(run_id)
    if manifest is None:
        raise typer.BadParameter(f"run_id not found: {run_id}")
    typer.echo(manifest.model_dump_json(indent=2))


@app.command("demo")
def demo(
    output: Annotated[
        Path | None,
        typer.Option(help="Optional demo output directory. Defaults to artifacts/runs/demo."),
    ] = None,
    events: int = typer.Option(150, "--events", min=1, help="Number of synthetic events."),
    quantity: int = typer.Option(1_000, help="Parent order quantity."),
    duration: int = typer.Option(60, help="Execution duration in event-time units."),
) -> None:
    """Run the deterministic synthetic demo."""
    try:
        report_path = run_demo(
            output_dir=output,
            event_count=events,
            quantity=quantity,
            duration=duration,
        )
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Demo report: {report_path}")


if __name__ == "__main__":
    app()
