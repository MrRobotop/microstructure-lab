# Limitations

Microstructure-Lab is a professional engineering and research demo, not a live trading
system.

## Data

All public demos use deterministic synthetic data. The project does not include paid
market data, proprietary feeds, venue-specific message formats, or historical order book
captures.

Synthetic results must not be presented as real trading performance.

## Matching Engine

The C++ engine implements price-time-priority behavior for a simplified book. It does not
yet model:

- exchange-specific order types
- hidden, pegged, midpoint, or discretionary orders
- queue position uncertainty from real feed latency
- auction states
- trading halts
- self-trade prevention
- venue-specific rejects

## Execution Simulation

Execution strategies currently operate on synthetic replay and submit child market orders.
The simulator records partial fills and unfilled quantity, but it does not yet model:

- broker routing logic
- real venue fees and rebates
- real queue priority estimates
- child limit order placement and cancellation tactics
- stochastic latency distributions tied to a venue feed

## Analytics

Transaction cost metrics are explicit about missing inputs. Metrics such as VWAP slippage,
spread cost, and opportunity cost are unavailable unless the required benchmarks are
provided or derivable from stored artifacts.

Strategy comparison reports should be read as controlled scenario analysis, not live
performance attribution.

## Performance

The benchmark command reports local timing observations. It includes Python-to-C++ binding
overhead and synthetic event conversion. It is useful for regression tracking, but it is
not a claim about exchange-grade throughput.

## Portfolio Claims

This project demonstrates:

- C++ systems-oriented matching engine implementation
- Python research orchestration
- execution simulation discipline
- transaction cost analytics
- reproducible CLI workflows
- Docker and CI readiness

It does not claim production trading readiness or real alpha generation.

