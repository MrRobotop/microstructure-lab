# Strategy Comparison

Phase 8 compares execution strategies on one deterministic synthetic event stream.

## Command

```bash
microstructure-lab execute compare \
  --strategies twap,vwap,pov,iceberg,adaptive \
  --scenario normal \
  --seed 42 \
  --output artifacts/runs/comparison
```

## Outputs

```text
events.csv
summary.json
comparison_report.md
<strategy>/child_orders.csv
<strategy>/fills.csv
<strategy>/result.json
```

## Ranking

The leaderboard uses multiple metrics:

- fill rate
- implementation shortfall when available
- unfilled quantity

It does not rank strategies by a single metric only.

## Limitations

The comparison is deterministic and useful for engineering review, but it is synthetic.
It does not prove live execution quality, venue performance, or alpha survival.
