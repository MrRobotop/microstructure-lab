from __future__ import annotations

from microstructure_lab.orderbook import core


def limit_order(
    order_id: str,
    timestamp: int,
    side: core.OrderSide,
    price_ticks: int,
    quantity: int,
) -> core.Order:
    return core.Order(
        order_id=order_id,
        timestamp=timestamp,
        symbol="XYZ",
        side=side,
        type=core.OrderType.LIMIT,
        price_ticks=price_ticks,
        quantity=quantity,
    )


def market_order(
    order_id: str,
    timestamp: int,
    side: core.OrderSide,
    quantity: int,
) -> core.Order:
    return core.Order(
        order_id=order_id,
        timestamp=timestamp,
        symbol="XYZ",
        side=side,
        type=core.OrderType.MARKET,
        price_ticks=0,
        quantity=quantity,
    )


def test_import_extension() -> None:
    extension = core.load_core()

    assert extension.engine_model_version() == 4


def test_add_orders_and_read_snapshot() -> None:
    engine = core.MatchingEngine()

    result = engine.add_limit_order(
        limit_order("bid-1", 100, core.OrderSide.BUY, price_ticks=99, quantity=10)
    )

    assert result.status == core.EngineStatus.ACCEPTED
    assert result.trades == []

    snapshot = engine.snapshot(101, "XYZ")
    assert snapshot.best_bid_ticks == 99
    assert snapshot.best_ask_ticks is None
    assert snapshot.bid_depth == 10


def test_match_market_order_and_read_trades() -> None:
    engine = core.MatchingEngine()
    engine.add_limit_order(
        limit_order("ask-1", 100, core.OrderSide.SELL, price_ticks=101, quantity=10)
    )

    result = engine.submit_market_order(
        market_order("buy-1", 101, core.OrderSide.BUY, quantity=6)
    )

    assert result.status == core.EngineStatus.ACCEPTED
    assert len(result.trades) == 1
    assert result.trades[0].price_ticks == 101
    assert result.trades[0].quantity == 6
    assert result.trades[0].maker_order_id == "ask-1"
    assert result.trades[0].taker_order_id == "buy-1"

    stored_trades = engine.trades("XYZ")
    assert len(stored_trades) == 1
    assert stored_trades[0].trade_id == "trade-1"


def test_cancel_order() -> None:
    engine = core.MatchingEngine()
    engine.add_limit_order(
        limit_order("bid-1", 100, core.OrderSide.BUY, price_ticks=99, quantity=10)
    )

    cancel = engine.cancel_order("XYZ", "bid-1")
    missing = engine.cancel_order("XYZ", "bid-1")

    assert cancel.status == core.EngineStatus.ACCEPTED
    assert missing.status == core.EngineStatus.NOT_FOUND
    assert engine.find_order("XYZ", "bid-1") is None


def test_apply_event_replay() -> None:
    engine = core.MatchingEngine()

    add_result = engine.apply_event(
        core.Event.add_limit(100, "XYZ", "ask-1", core.OrderSide.SELL, 101, 10)
    )
    market_result = engine.apply_event(
        core.Event.market(101, "XYZ", "buy-1", core.OrderSide.BUY, 4)
    )

    assert add_result.status == core.EngineStatus.ACCEPTED
    assert market_result.status == core.EngineStatus.ACCEPTED
    assert len(market_result.trades) == 1
    assert market_result.trades[0].quantity == 4
