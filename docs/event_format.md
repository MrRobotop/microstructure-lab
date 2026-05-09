# Synthetic Event Format

Microstructure-Lab Phase 5 uses CSV event files for deterministic synthetic replay.
These files are not real market data and must be labeled synthetic.

## Columns

```text
timestamp
sequence
event_type
symbol
order_id
side
price_ticks
quantity
scenario
seed
is_synthetic
```

## Event Types

- `add`: limit order add. Requires `side`, `price_ticks`, and `quantity`.
- `cancel`: cancel by `order_id`. Must not include `side`, `price_ticks`, or `quantity`.
- `modify`: cancel-replace by `order_id`. Requires `price_ticks` and `quantity`.
- `market`: market order. Requires `side` and `quantity`; must not include `price_ticks`.

## Units

- `price_ticks` is an integer tick price.
- `quantity` is integer shares/contracts/lots depending on the synthetic scenario.
- `timestamp` is an integer event-clock timestamp, not wall-clock time.
- `sequence` breaks ties when timestamps are equal.

## Synthetic Label

`is_synthetic` must be true. Replay rejects rows that are not explicitly synthetic.

The generator is intended for reproducible engineering demos and tests. It is not
calibrated to real exchange data.
