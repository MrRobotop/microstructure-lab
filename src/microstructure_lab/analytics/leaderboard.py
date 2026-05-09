"""Strategy leaderboard helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LeaderboardRow:
    strategy: str
    fill_rate: float
    average_fill_price_ticks: float | None
    implementation_shortfall_bps: float | None
    unfilled_quantity: int


def rank_strategies(rows: list[LeaderboardRow]) -> list[LeaderboardRow]:
    """Rank without reducing strategy quality to one metric only."""
    return sorted(
        rows,
        key=lambda row: (
            -row.fill_rate,
            row.implementation_shortfall_bps is None,
            row.implementation_shortfall_bps or 0,
            row.unfilled_quantity,
        ),
    )
