"""Python access point for the C++ matching engine.

This module is intentionally thin: matching behavior lives in C++ and is exposed
through ``microstructure_lab._core``.
"""

from __future__ import annotations


def load_core():
    """Import the C++ extension or raise an actionable setup error."""
    try:
        from microstructure_lab import _core
    except ImportError as exc:
        msg = (
            "The microstructure_lab._core extension is not available. "
            "Install the project with `python -m pip install -e .` after installing "
            "CMake and a C++17 compiler."
        )
        raise RuntimeError(msg) from exc
    return _core


_core = load_core()

OrderSide = _core.OrderSide
OrderType = _core.OrderType
OrderStatus = _core.OrderStatus
EventType = _core.EventType
EngineStatus = _core.EngineStatus
Order = _core.Order
Trade = _core.Trade
Snapshot = _core.Snapshot
Event = _core.Event
EngineResult = _core.EngineResult
MatchingEngine = _core.MatchingEngine

__all__ = [
    "EngineResult",
    "EngineStatus",
    "Event",
    "EventType",
    "MatchingEngine",
    "Order",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "Snapshot",
    "Trade",
    "load_core",
]
