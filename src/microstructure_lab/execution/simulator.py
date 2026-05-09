"""Execution simulator that injects strategy child orders into C++ replay."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from microstructure_lab.orderbook import core
from microstructure_lab.runs.manifest import create_manifest, make_run_id, save_manifest
from microstructure_lab.schemas.events import EventType, MarketEvent
from microstructure_lab.simulation.replay import _to_core_event
from microstructure_lab.simulation.synthetic import read_events_csv

from .adaptive import AdaptivePOVStrategy
from .base import ExecutionState, ExecutionStrategy
from .iceberg import IcebergStrategy
from .parent_order import ChildOrder, ExecutionResult, ExecutionSide, Fill, ParentOrder
from .pov import POVStrategy
from .twap import TWAPStrategy
from .vwap import VWAPStrategy


def strategy_from_name(name: str, events: list[MarketEvent]) -> ExecutionStrategy:
    normalized = name.lower()
    if normalized == "twap":
        return TWAPStrategy()
    if normalized == "vwap":
        return VWAPStrategy(expected_volume_by_timestamp=_expected_volume_schedule(events))
    if normalized == "pov":
        return POVStrategy()
    if normalized == "iceberg":
        return IcebergStrategy(display_quantity=100)
    if normalized == "adaptive":
        return AdaptivePOVStrategy()
    msg = f"unknown strategy {name!r}; expected one of: adaptive, iceberg, pov, twap, vwap"
    raise ValueError(msg)


def run_execution(
    *,
    events: list[MarketEvent],
    parent_order: ParentOrder,
    strategy: ExecutionStrategy,
) -> ExecutionResult:
    if not events:
        msg = "cannot execute against an empty event stream"
        raise ValueError(msg)

    engine = core.MatchingEngine()
    child_orders: list[ChildOrder] = []
    fills: list[Fill] = []
    realized_quantity = 0
    child_sequence = 0

    for replay_event in sorted(events, key=lambda item: (item.timestamp, item.sequence)):
        market_result = engine.apply_event(_to_core_event(replay_event))
        if market_result.status == core.EngineStatus.REJECTED:
            msg = f"event {replay_event.sequence} rejected by C++ engine: {market_result.message}"
            raise RuntimeError(msg)

        snapshot = engine.snapshot(replay_event.timestamp, parent_order.symbol)
        state = ExecutionState(
            timestamp=replay_event.timestamp,
            elapsed_steps=max(0, replay_event.timestamp - parent_order.start_time),
            remaining_quantity=parent_order.quantity - realized_quantity,
            last_event=replay_event,
            best_bid_ticks=snapshot.best_bid_ticks,
            best_ask_ticks=snapshot.best_ask_ticks,
            bid_depth=snapshot.bid_depth,
            ask_depth=snapshot.ask_depth,
            observed_market_volume=_observed_market_volume(replay_event),
        )

        for child in strategy.generate_child_orders(parent_order, state):
            if realized_quantity >= parent_order.quantity:
                break
            child_sequence += 1
            child_order_id = f"{strategy.name}-{replay_event.timestamp}-{child_sequence}"
            child = child.model_copy(
                update={"child_order_id": child_order_id}
            )
            child_orders.append(child)
            result = engine.submit_market_order(_child_to_core_order(child))
            if result.status == core.EngineStatus.REJECTED:
                msg = f"child order {child.child_order_id} rejected by C++ engine: {result.message}"
                raise RuntimeError(msg)
            for trade in result.trades:
                fill = Fill(
                    child_order_id=child.child_order_id,
                    trade_id=trade.trade_id,
                    timestamp=trade.timestamp,
                    symbol=trade.symbol,
                    side=child.side,
                    price_ticks=trade.price_ticks,
                    quantity=trade.quantity,
                    maker_order_id=trade.maker_order_id,
                )
                fills.append(fill)
                realized_quantity += fill.quantity

    return _build_result(strategy.name, parent_order, child_orders, fills)


def run_execution_file(
    *,
    events_path: Path,
    output_dir: Path,
    strategy_name: str,
    side: ExecutionSide,
    quantity: int,
    duration: int,
    command: str | None = None,
) -> ExecutionResult:
    run_id = make_run_id("execute", [strategy_name, side.value, quantity, duration])
    config: dict[str, Any] = {
        "strategy": strategy_name,
        "side": side.value,
        "quantity": quantity,
        "duration": duration,
        "events_path": str(events_path),
    }
    try:
        events = read_events_csv(events_path)
        parent = ParentOrder(side=side, quantity=quantity, start_time=0, end_time=duration)
        strategy = strategy_from_name(strategy_name, events)
        result = run_execution(events=events, parent_order=parent, strategy=strategy)
        write_execution_artifacts(result, output_dir)
        manifest = create_manifest(
            run_id=run_id,
            command=command or _execution_command(config, output_dir),
            status="completed",
            config=config,
            input_path=events_path,
            output_paths={
                "child_orders": output_dir / "child_orders.csv",
                "fills": output_dir / "fills.csv",
                "result": output_dir / "result.json",
            },
            scenario=events[0].scenario if events else None,
            seed=events[0].seed if events else None,
            strategy=result.strategy,
            parent_order=result.parent_order.model_dump(mode="json"),
            metrics={
                "realized_quantity": result.realized_quantity,
                "unfilled_quantity": result.unfilled_quantity,
                "fill_rate": result.fill_rate,
            },
            limitations=[
                "Synthetic execution simulation.",
                "Strategies currently use market child orders only.",
            ],
        )
        save_manifest(manifest, output_dir)
        return result
    except Exception as exc:
        manifest = create_manifest(
            run_id=run_id,
            command=command or _execution_command(config, output_dir),
            status="failed",
            config=config,
            input_path=events_path,
            output_paths={},
            strategy=strategy_name,
            error=str(exc),
            limitations=["Failed run recorded for auditability."],
        )
        save_manifest(manifest, output_dir)
        raise


def write_execution_artifacts(result: ExecutionResult, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_child_orders(result.child_orders, output_dir / "child_orders.csv")
    _write_fills(result.fills, output_dir / "fills.csv")
    with (output_dir / "result.json").open("w") as file:
        json.dump(result.model_dump(mode="json"), file, indent=2)


def _build_result(
    strategy_name: str,
    parent_order: ParentOrder,
    child_orders: list[ChildOrder],
    fills: list[Fill],
) -> ExecutionResult:
    realized_quantity = sum(fill.quantity for fill in fills)
    cost_notional_ticks = sum(fill.price_ticks * fill.quantity for fill in fills)
    average_fill_price = (
        cost_notional_ticks / realized_quantity if realized_quantity > 0 else None
    )
    return ExecutionResult(
        strategy=strategy_name,
        parent_order=parent_order,
        child_orders=child_orders,
        fills=fills,
        requested_quantity=parent_order.quantity,
        realized_quantity=realized_quantity,
        unfilled_quantity=parent_order.quantity - realized_quantity,
        average_fill_price_ticks=average_fill_price,
        fill_rate=realized_quantity / parent_order.quantity,
        cost_notional_ticks=cost_notional_ticks,
    )


def _child_to_core_order(child: ChildOrder) -> core.Order:
    return core.Order(
        order_id=child.child_order_id,
        timestamp=child.timestamp,
        symbol=child.symbol,
        side=core.OrderSide.BUY if child.side == ExecutionSide.BUY else core.OrderSide.SELL,
        type=core.OrderType.MARKET,
        price_ticks=0,
        quantity=child.quantity,
    )


def _observed_market_volume(event: MarketEvent) -> int:
    if event.event_type == EventType.MARKET and event.quantity is not None:
        return event.quantity
    return 0


def _expected_volume_schedule(events: list[MarketEvent]) -> dict[int, int]:
    schedule: dict[int, int] = {}
    for event in events:
        if event.quantity is not None:
            schedule[event.timestamp] = schedule.get(event.timestamp, 0) + event.quantity
    return schedule


def _write_child_orders(child_orders: list[ChildOrder], output: Path) -> None:
    with output.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["child_order_id", "timestamp", "symbol", "side", "quantity", "strategy"],
        )
        writer.writeheader()
        for child in child_orders:
            writer.writerow(child.model_dump(mode="json"))


def _write_fills(fills: list[Fill], output: Path) -> None:
    with output.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "child_order_id",
                "trade_id",
                "timestamp",
                "symbol",
                "side",
                "price_ticks",
                "quantity",
                "maker_order_id",
            ],
        )
        writer.writeheader()
        for fill in fills:
            writer.writerow(fill.model_dump(mode="json"))


def _execution_command(config: dict[str, object], output_dir: Path) -> str:
    return (
        "microstructure-lab execute run "
        f"--strategy {config['strategy']} "
        f"--side {config['side']} "
        f"--quantity {config['quantity']} "
        f"--duration {config['duration']} "
        f"--events {config['events_path']} "
        f"--output {output_dir}"
    )
