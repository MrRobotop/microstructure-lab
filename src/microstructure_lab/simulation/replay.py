"""Replay synthetic events through the C++ matching engine."""

from __future__ import annotations

import csv
from pathlib import Path

from microstructure_lab.orderbook import core
from microstructure_lab.runs.manifest import create_manifest, make_run_id, save_manifest
from microstructure_lab.schemas.events import EventType, MarketEvent, OrderSide
from microstructure_lab.simulation.synthetic import read_events_csv

TRADE_COLUMNS = [
    "trade_id",
    "timestamp",
    "symbol",
    "price_ticks",
    "quantity",
    "aggressor_side",
    "maker_order_id",
    "taker_order_id",
]

SNAPSHOT_COLUMNS = [
    "timestamp",
    "symbol",
    "best_bid_ticks",
    "best_ask_ticks",
    "spread_ticks",
    "mid_price_ticks_x2",
    "bid_depth",
    "ask_depth",
]


def replay_events(events: list[MarketEvent]) -> tuple[list[core.Trade], list[core.Snapshot]]:
    """Replay validated events through the C++ engine."""
    if not events:
        msg = "cannot replay an empty event stream"
        raise ValueError(msg)

    engine = core.MatchingEngine()
    trades: list[core.Trade] = []
    snapshots: list[core.Snapshot] = []

    for event in sorted(events, key=lambda item: (item.timestamp, item.sequence)):
        result = engine.apply_event(_to_core_event(event))
        if result.status == core.EngineStatus.REJECTED:
            msg = f"event {event.sequence} rejected by C++ engine: {result.message}"
            raise RuntimeError(msg)
        trades.extend(result.trades)
        snapshots.append(engine.snapshot(event.timestamp, event.symbol))

    return trades, snapshots


def replay_file(
    events_path: Path,
    output_dir: Path,
    command: str | None = None,
) -> tuple[Path, Path]:
    run_id = make_run_id("book-replay", [events_path.stem])
    config = {"events_path": str(events_path)}
    try:
        events = read_events_csv(events_path)
        trades, snapshots = replay_events(events)

        output_dir.mkdir(parents=True, exist_ok=True)
        trades_path = output_dir / "trades.csv"
        snapshots_path = output_dir / "snapshots.csv"
        write_trades_csv(trades, trades_path)
        write_snapshots_csv(snapshots, snapshots_path)
        manifest = create_manifest(
            run_id=run_id,
            command=command
            or f"microstructure-lab book replay --events {events_path} --output {output_dir}",
            status="completed",
            config=config,
            input_path=events_path,
            output_paths={"trades": trades_path, "snapshots": snapshots_path},
            scenario=events[0].scenario if events else None,
            seed=events[0].seed if events else None,
            metrics={"trades": len(trades), "snapshots": len(snapshots)},
            limitations=["Synthetic replay through the C++ matching engine."],
        )
        save_manifest(manifest, output_dir)
        return trades_path, snapshots_path
    except Exception as exc:
        manifest = create_manifest(
            run_id=run_id,
            command=command
            or f"microstructure-lab book replay --events {events_path} --output {output_dir}",
            status="failed",
            config=config,
            input_path=events_path,
            output_paths={},
            error=str(exc),
            limitations=["Failed replay recorded for auditability."],
        )
        save_manifest(manifest, output_dir)
        raise


def write_trades_csv(trades: list[core.Trade], output: Path) -> None:
    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=TRADE_COLUMNS)
        writer.writeheader()
        for trade in trades:
            writer.writerow(
                {
                    "trade_id": trade.trade_id,
                    "timestamp": trade.timestamp,
                    "symbol": trade.symbol,
                    "price_ticks": trade.price_ticks,
                    "quantity": trade.quantity,
                    "aggressor_side": _side_to_str(trade.aggressor_side),
                    "maker_order_id": trade.maker_order_id,
                    "taker_order_id": trade.taker_order_id,
                }
            )


def write_snapshots_csv(snapshots: list[core.Snapshot], output: Path) -> None:
    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=SNAPSHOT_COLUMNS)
        writer.writeheader()
        for snapshot in snapshots:
            writer.writerow(
                {
                    "timestamp": snapshot.timestamp,
                    "symbol": snapshot.symbol,
                    "best_bid_ticks": _optional_int(snapshot.best_bid_ticks),
                    "best_ask_ticks": _optional_int(snapshot.best_ask_ticks),
                    "spread_ticks": _optional_int(snapshot.spread_ticks),
                    "mid_price_ticks_x2": _optional_int(snapshot.mid_price_ticks_x2),
                    "bid_depth": snapshot.bid_depth,
                    "ask_depth": snapshot.ask_depth,
                }
            )


def _to_core_event(event: MarketEvent) -> core.Event:
    if event.event_type == EventType.ADD:
        return core.Event.add_limit(
            event.timestamp,
            event.symbol,
            event.order_id,
            _to_core_side(event.side),
            _require_int(event.price_ticks, "price_ticks"),
            _require_int(event.quantity, "quantity"),
        )
    if event.event_type == EventType.CANCEL:
        return core.Event.cancel(event.timestamp, event.symbol, event.order_id)
    if event.event_type == EventType.MODIFY:
        return core.Event.modify(
            event.timestamp,
            event.symbol,
            event.order_id,
            _require_int(event.price_ticks, "price_ticks"),
            _require_int(event.quantity, "quantity"),
        )
    if event.event_type == EventType.MARKET:
        return core.Event.market(
            event.timestamp,
            event.symbol,
            event.order_id,
            _to_core_side(event.side),
            _require_int(event.quantity, "quantity"),
        )
    msg = f"unsupported event type: {event.event_type}"
    raise ValueError(msg)


def _to_core_side(side: OrderSide | None) -> core.OrderSide:
    if side == OrderSide.BUY:
        return core.OrderSide.BUY
    if side == OrderSide.SELL:
        return core.OrderSide.SELL
    msg = "side is required"
    raise ValueError(msg)


def _side_to_str(side: core.OrderSide) -> str:
    if side == core.OrderSide.BUY:
        return "buy"
    if side == core.OrderSide.SELL:
        return "sell"
    msg = f"unknown core side: {side}"
    raise ValueError(msg)


def _require_int(value: int | None, name: str) -> int:
    if value is None:
        msg = f"{name} is required"
        raise ValueError(msg)
    return value


def _optional_int(value: int | None) -> int | str:
    return "" if value is None else value
