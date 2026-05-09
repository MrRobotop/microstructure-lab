# Transaction Cost Analytics

Phase 7 computes transaction cost metrics from execution artifacts. Analytics consume
stored `result.json`, `child_orders.csv`, and `fills.csv` outputs instead of rerunning the
simulation.

## Metrics

- Arrival price.
- Average fill price.
- Realized quantity.
- Fill rate.
- Unfilled quantity.
- Implementation shortfall in ticks and basis points.
- VWAP slippage.
- Spread cost estimate.
- Time to completion.
- Participation rate.
- Opportunity cost.
- Adverse selection proxy where a terminal mid is supplied.

## Missing Benchmarks

If arrival price, benchmark VWAP, spread, or terminal mid are not supplied, dependent
metrics are marked `unavailable`. The project does not invent missing benchmarks.

## Limitations

The current analytics are deterministic and unit-explicit, but they are not calibrated to
real trading costs. Synthetic reports are engineering artifacts, not evidence of live
execution performance.
