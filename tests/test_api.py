from __future__ import annotations

from pathlib import Path

from api.main import app
from fastapi.testclient import TestClient

from microstructure_lab.execution.comparison import run_strategy_comparison
from microstructure_lab.execution.parent_order import ExecutionSide
from microstructure_lab.execution.simulator import run_execution_file
from microstructure_lab.simulation.synthetic import generate_events, write_events_csv


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_runs_endpoint_with_temporary_artifact_store(tmp_path: Path) -> None:
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
    client = TestClient(app)

    response = client.get("/runs")

    assert response.status_code == 200
    payload = response.json()
    assert any(item["run_id"] == "comparison-normal-42-twap-pov" for item in payload)


def test_run_detail_and_metrics_endpoints(tmp_path: Path) -> None:
    events = generate_events(scenario="normal", seed=3, event_count=40)
    events_path = tmp_path / "events.csv"
    output = tmp_path / "twap"
    write_events_csv(events, events_path)
    run_execution_file(
        events_path=events_path,
        output_dir=output,
        strategy_name="twap",
        side=ExecutionSide.BUY,
        quantity=100,
        duration=30,
    )
    client = TestClient(app)

    detail = client.get("/runs/execute-twap-buy-100-30")
    metrics = client.get("/runs/execute-twap-buy-100-30/metrics")

    assert detail.status_code == 200
    assert detail.json()["manifest"]["run_id"] == "execute-twap-buy-100-30"
    assert "result.json" in detail.json()["artifacts"]
    assert metrics.status_code == 200
    assert metrics.json()["result_metrics"]["requested_quantity"] == 100


def test_missing_run_returns_404() -> None:
    client = TestClient(app)

    response = client.get("/runs/missing-run")

    assert response.status_code == 404


def test_leaderboard_endpoint(tmp_path: Path) -> None:
    output = tmp_path / "comparison"
    run_strategy_comparison(
        strategies=["twap", "pov"],
        scenario="normal",
        seed=77,
        output_dir=output,
        side=ExecutionSide.BUY,
        quantity=100,
        duration=30,
        event_count=50,
    )
    client = TestClient(app)

    response = client.get("/leaderboard")

    assert response.status_code == 200
    payload = response.json()
    assert any(row["source_run_id"] == "comparison-normal-77-twap-pov" for row in payload)


def test_api_does_not_expose_environment_or_secrets(tmp_path: Path) -> None:
    output = tmp_path / "comparison"
    run_strategy_comparison(
        strategies=["twap"],
        scenario="normal",
        seed=88,
        output_dir=output,
        side=ExecutionSide.BUY,
        quantity=100,
        duration=30,
        event_count=50,
    )
    client = TestClient(app)

    response_text = client.get("/runs/comparison-normal-88-twap").text

    assert "MICROSTRUCTURE_LAB_RUN_INDEX" not in response_text
    assert "SECRET" not in response_text
