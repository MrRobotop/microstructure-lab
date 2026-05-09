"""Conservative matching engine benchmark utilities."""

from __future__ import annotations

import json
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter_ns

from microstructure_lab import __version__
from microstructure_lab.orderbook import core
from microstructure_lab.schemas.events import MarketEvent
from microstructure_lab.simulation.replay import _to_core_event
from microstructure_lab.simulation.synthetic import generate_events


@dataclass(frozen=True)
class EngineBenchmarkResult:
    """One local benchmark observation.

    This is a timing observation for the current machine and Python process, not a
    portable performance claim.
    """

    synthetic: bool
    scenario: str
    seed: int
    requested_events: int
    applied_events: int
    trades: int
    elapsed_seconds: float
    events_per_second: float
    engine_version: str
    python_version: str
    platform: str
    limitations: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def benchmark_engine(
    *,
    event_count: int,
    scenario: str,
    seed: int = 42,
    warmup_events: int = 1_000,
) -> EngineBenchmarkResult:
    """Benchmark C++ engine event application on deterministic synthetic flow."""
    if event_count <= 0:
        msg = "event_count must be positive"
        raise ValueError(msg)
    if warmup_events < 0:
        msg = "warmup_events must be non-negative"
        raise ValueError(msg)

    events = generate_events(scenario=scenario, seed=seed, event_count=event_count)
    if warmup_events:
        warmup_count = min(warmup_events, event_count)
        _apply_events(events[:warmup_count])

    started_ns = perf_counter_ns()
    trades = _apply_events(events)
    elapsed_seconds = (perf_counter_ns() - started_ns) / 1_000_000_000
    events_per_second = event_count / elapsed_seconds if elapsed_seconds > 0 else 0.0

    return EngineBenchmarkResult(
        synthetic=True,
        scenario=scenario,
        seed=seed,
        requested_events=event_count,
        applied_events=event_count,
        trades=trades,
        elapsed_seconds=elapsed_seconds,
        events_per_second=events_per_second,
        engine_version=(
            f"microstructure-lab {__version__}; "
            f"core {core.load_core().engine_model_version()}"
        ),
        python_version=sys.version.split()[0],
        platform=platform.platform(),
        limitations=[
            "Synthetic deterministic event stream.",
            "Measures Python-to-C++ event application overhead plus C++ matching work.",
            "Single-process local observation; do not compare across machines as a claim.",
            "No paid or real market data is used.",
        ],
    )


def write_benchmark_json(result: EngineBenchmarkResult, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2))
    return output


def _apply_events(events: list[MarketEvent]) -> int:
    engine = core.MatchingEngine()
    trades = 0
    for event in events:
        result = engine.apply_event(_to_core_event(event))
        if result.status == core.EngineStatus.REJECTED:
            msg = f"event {event.sequence} rejected by C++ engine: {result.message}"
            raise RuntimeError(msg)
        trades += len(result.trades)
    return trades

