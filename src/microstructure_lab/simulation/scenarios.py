"""Synthetic market scenario configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScenarioConfig:
    name: str
    base_mid_ticks: int
    spread_ticks: int
    initial_depth: int
    price_jitter_ticks: int
    market_order_frequency: int
    cancel_frequency: int
    quantity_min: int
    quantity_max: int


SCENARIOS: dict[str, ScenarioConfig] = {
    "normal": ScenarioConfig("normal", 10_000, 4, 6, 2, 5, 7, 10, 80),
    "thin_liquidity": ScenarioConfig("thin_liquidity", 10_000, 8, 3, 4, 4, 5, 5, 35),
    "wide_spread": ScenarioConfig("wide_spread", 10_000, 16, 5, 3, 6, 8, 10, 60),
    "volatility_spike": ScenarioConfig("volatility_spike", 10_000, 6, 5, 10, 3, 6, 10, 90),
    "toxic_flow": ScenarioConfig("toxic_flow", 10_000, 6, 4, 5, 2, 7, 20, 120),
}


def get_scenario(name: str) -> ScenarioConfig:
    try:
        return SCENARIOS[name]
    except KeyError as exc:
        valid = ", ".join(sorted(SCENARIOS))
        msg = f"unknown scenario {name!r}; expected one of: {valid}"
        raise ValueError(msg) from exc
