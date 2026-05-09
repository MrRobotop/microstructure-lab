from __future__ import annotations

from pathlib import Path

from microstructure_lab.analytics.cost_report import compute_cost_metrics, write_cost_report
from microstructure_lab.analytics.implementation_shortfall import implementation_shortfall_ticks
from microstructure_lab.analytics.leaderboard import LeaderboardRow, rank_strategies
from microstructure_lab.execution.parent_order import (
    ChildOrder,
    ExecutionResult,
    ExecutionSide,
    Fill,
    ParentOrder,
)
from microstructure_lab.execution.simulator import write_execution_artifacts


def result_with_fills(side: ExecutionSide = ExecutionSide.BUY) -> ExecutionResult:
    parent = ParentOrder(side=side, symbol="XYZ", quantity=100, start_time=0, end_time=10)
    child = ChildOrder(
        child_order_id="child-1",
        timestamp=1,
        symbol="XYZ",
        side=side,
        quantity=80,
        strategy="test",
    )
    fills = [
        Fill(
            child_order_id="child-1",
            trade_id="trade-1",
            timestamp=1,
            symbol="XYZ",
            side=side,
            price_ticks=101,
            quantity=50,
            maker_order_id="maker-1",
        ),
        Fill(
            child_order_id="child-1",
            trade_id="trade-2",
            timestamp=2,
            symbol="XYZ",
            side=side,
            price_ticks=102,
            quantity=30,
            maker_order_id="maker-2",
        ),
    ]
    realized = sum(fill.quantity for fill in fills)
    notional = sum(fill.price_ticks * fill.quantity for fill in fills)
    return ExecutionResult(
        strategy="test",
        parent_order=parent,
        child_orders=[child],
        fills=fills,
        requested_quantity=100,
        realized_quantity=realized,
        unfilled_quantity=20,
        average_fill_price_ticks=notional / realized,
        fill_rate=0.8,
        cost_notional_ticks=notional,
    )


def test_deterministic_metric_calculations() -> None:
    result = result_with_fills()

    metrics = compute_cost_metrics(
        result,
        arrival_price_ticks=100,
        benchmark_vwap_ticks=100.5,
        spread_ticks=2,
        terminal_mid_ticks=103,
    )

    assert metrics.average_fill_price_ticks == 101.375
    assert metrics.realized_quantity == 80
    assert metrics.fill_rate == 0.8
    assert metrics.unfilled_quantity == 20
    assert metrics.implementation_shortfall_ticks == 1.375
    assert metrics.implementation_shortfall_bps == 137.5
    assert metrics.vwap_slippage_ticks == 0.875
    assert metrics.spread_cost_ticks == 80
    assert metrics.opportunity_cost_ticks == 2_000


def test_buy_and_sell_sign_conventions() -> None:
    buy = result_with_fills(ExecutionSide.BUY)
    sell = result_with_fills(ExecutionSide.SELL)

    assert implementation_shortfall_ticks(buy, 100) == 1.375
    assert implementation_shortfall_ticks(sell, 100) == -1.375


def test_zero_fill_handling() -> None:
    parent = ParentOrder(side=ExecutionSide.BUY, quantity=100, start_time=0, end_time=10)
    result = ExecutionResult(
        strategy="test",
        parent_order=parent,
        child_orders=[],
        fills=[],
        requested_quantity=100,
        realized_quantity=0,
        unfilled_quantity=100,
        average_fill_price_ticks=None,
        fill_rate=0,
        cost_notional_ticks=0,
    )

    metrics = compute_cost_metrics(result, arrival_price_ticks=100)

    assert metrics.average_fill_price_ticks is None
    assert metrics.fill_rate == 0
    assert metrics.implementation_shortfall_ticks is None
    assert metrics.unfilled_quantity == 100


def test_partial_fill_handling() -> None:
    result = result_with_fills()

    metrics = compute_cost_metrics(result, arrival_price_ticks=100)

    assert metrics.realized_quantity == 80
    assert metrics.unfilled_quantity == 20
    assert metrics.time_to_completion is None


def test_missing_benchmark_handling() -> None:
    result = result_with_fills()

    metrics = compute_cost_metrics(result)

    assert metrics.implementation_shortfall_ticks is None
    assert metrics.implementation_shortfall_bps is None
    assert metrics.vwap_slippage_ticks is None
    assert metrics.spread_cost_ticks is None
    assert metrics.opportunity_cost_ticks is None


def test_report_includes_limitations(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    output = tmp_path / "report.md"
    write_execution_artifacts(result_with_fills(), run_dir)

    write_cost_report(run_dir=run_dir, output_path=output, arrival_price_ticks=100)

    text = output.read_text()
    assert "Transaction Cost Report" in text
    assert "Limitations" in text
    assert "Synthetic results" in text
    assert "Unfilled quantity" in text


def test_report_table_marks_unavailable_metrics(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    output = tmp_path / "report.md"
    write_execution_artifacts(result_with_fills(), run_dir)

    write_cost_report(run_dir=run_dir, output_path=output)

    text = output.read_text()
    assert "| Arrival price | unavailable | ticks |" in text
    assert "| Implementation shortfall | unavailable | ticks/share |" in text
    assert "| VWAP slippage | unavailable | ticks/share |" in text


def test_leaderboard_uses_multiple_metrics() -> None:
    rows = [
        LeaderboardRow(
            "a",
            fill_rate=0.5,
            average_fill_price_ticks=101,
            implementation_shortfall_bps=1,
            unfilled_quantity=50,
        ),
        LeaderboardRow(
            "b",
            fill_rate=1.0,
            average_fill_price_ticks=102,
            implementation_shortfall_bps=10,
            unfilled_quantity=0,
        ),
    ]

    ranked = rank_strategies(rows)

    assert ranked[0].strategy == "b"
