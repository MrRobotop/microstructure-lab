# Performance and Benchmarks

Phase 15 adds a conservative matching engine benchmark command.

## Command

```bash
microstructure-lab benchmark engine --events 100000 --scenario normal
```

Optional JSON output:

```bash
microstructure-lab benchmark engine \
  --events 100000 \
  --scenario normal \
  --seed 42 \
  --output artifacts/reports/engine_benchmark.json
```

## What It Measures

The benchmark generates a deterministic synthetic event stream, applies the events through
the C++ matching engine via the Python binding, and reports:

- applied events
- generated trades
- elapsed seconds
- events per second
- Python version
- platform string
- engine version

## Limitations

The benchmark is a local observation only. It includes Python-to-C++ binding overhead,
synthetic event conversion, and C++ matching work. It is useful for regression tracking in
this repository, but it is not a portable claim about exchange-grade throughput.

The benchmark uses synthetic data only and does not require paid market data.
