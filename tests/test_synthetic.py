from __future__ import annotations

import csv
from pathlib import Path

import pytest

from microstructure_lab.schemas.events import EventType, MarketEvent, OrderSide
from microstructure_lab.simulation.replay import replay_events, replay_file
from microstructure_lab.simulation.synthetic import (
    generate_events,
    read_events_csv,
    write_events_csv,
)


def test_deterministic_generation_with_fixed_seed() -> None:
    first = generate_events(scenario="normal", seed=42, event_count=40)
    second = generate_events(scenario="normal", seed=42, event_count=40)

    assert [event.model_dump() for event in first] == [event.model_dump() for event in second]
    assert all(event.is_synthetic for event in first)


def test_different_scenarios_produce_different_properties() -> None:
    normal = generate_events(scenario="normal", seed=42, event_count=40)
    wide = generate_events(scenario="wide_spread", seed=42, event_count=40)

    normal_first_ask = next(
        event
        for event in normal
        if event.event_type == EventType.ADD and event.side == OrderSide.SELL
    )
    wide_first_ask = next(
        event
        for event in wide
        if event.event_type == EventType.ADD and event.side == OrderSide.SELL
    )

    assert normal_first_ask.price_ticks != wide_first_ask.price_ticks
    assert {event.scenario for event in wide} == {"wide_spread"}


def test_event_csv_round_trip(tmp_path: Path) -> None:
    events = generate_events(scenario="normal", seed=7, event_count=20)
    path = tmp_path / "events.csv"

    write_events_csv(events, path)
    loaded = read_events_csv(path)

    assert [event.model_dump() for event in loaded] == [event.model_dump() for event in events]


def test_replay_produces_snapshots_and_trades() -> None:
    events = [
        MarketEvent(
            timestamp=0,
            sequence=0,
            event_type=EventType.ADD,
            symbol="XYZ",
            order_id="ask-1",
            side=OrderSide.SELL,
            price_ticks=101,
            quantity=10,
            scenario="normal",
            seed=1,
        ),
        MarketEvent(
            timestamp=1,
            sequence=1,
            event_type=EventType.MARKET,
            symbol="XYZ",
            order_id="buy-1",
            side=OrderSide.BUY,
            quantity=4,
            scenario="normal",
            seed=1,
        ),
    ]

    trades, snapshots = replay_events(events)

    assert len(trades) == 1
    assert trades[0].quantity == 4
    assert len(snapshots) == 2
    assert snapshots[-1].best_ask_ticks == 101
    assert snapshots[-1].ask_depth == 6


def test_replay_file_writes_artifacts(tmp_path: Path) -> None:
    events = generate_events(scenario="normal", seed=11, event_count=30)
    event_path = tmp_path / "events.csv"
    output_dir = tmp_path / "replay"
    write_events_csv(events, event_path)

    trades_path, snapshots_path = replay_file(event_path, output_dir)

    assert trades_path.exists()
    assert snapshots_path.exists()
    with snapshots_path.open(newline="") as file:
        rows = list(csv.DictReader(file))
    assert rows


def test_invalid_events_fail_clearly() -> None:
    with pytest.raises(ValueError, match="positive quantity"):
        MarketEvent(
            timestamp=0,
            sequence=0,
            event_type=EventType.MARKET,
            symbol="XYZ",
            order_id="bad",
            side=OrderSide.BUY,
            quantity=0,
            scenario="normal",
            seed=1,
        )


def test_unknown_scenario_fails_clearly() -> None:
    with pytest.raises(ValueError, match="unknown scenario"):
        generate_events(scenario="bad", seed=42, event_count=10)
