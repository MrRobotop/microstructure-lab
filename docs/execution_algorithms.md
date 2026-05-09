# Execution Algorithms

Phase 6 adds a first execution simulation layer. Strategies emit child market orders
while synthetic event replay progresses through the C++ matching engine.

## Implemented Strategies

- `twap`: slices the parent order across the requested duration.
- `vwap`: uses an expected static volume schedule, distinct from hindsight realized VWAP.
- `pov`: participates as a capped fraction of observed synthetic market-order volume.
- `iceberg`: reveals a fixed display quantity until the parent order is complete or time ends.
- `adaptive`: increases participation when the visible spread is tight and reduces it when
  the spread is wide.

## Outputs

`microstructure-lab execute run` writes:

```text
child_orders.csv
fills.csv
result.json
```

The result records requested quantity, realized quantity, unfilled quantity, average fill
price in ticks, fill rate, and notional cost in tick units.

## Limitations

Strategies currently use market child orders only. There is no queue-position model,
latency model, hidden liquidity, venue-specific order type behavior, or calibrated market
impact. Synthetic execution results are engineering demos, not trading evidence.
