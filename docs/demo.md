# Deterministic Demo

Phase 12 adds an end-to-end synthetic demo.

## Command

```bash
make demo
```

The command runs:

1. Synthetic event generation with scenario `normal` and seed `42`.
2. Order book replay through the C++ matching engine.
3. TWAP and POV execution strategy comparison.
4. Transaction cost metric computation.
5. Markdown comparison report generation.
6. Run manifest registration for dashboard/API discovery.

## Outputs

```text
artifacts/runs/demo/
  events.csv
  manifest.json
  summary.json
  comparison_report.md
  book_replay/
    manifest.json
    trades.csv
    snapshots.csv
  twap/
    child_orders.csv
    fills.csv
    result.json
  pov/
    child_orders.csv
    fills.csv
    result.json
```

The CLI prints the report path:

```text
Demo report: artifacts/runs/demo/comparison_report.md
```

All demo data is synthetic and intended for deterministic engineering review only.
