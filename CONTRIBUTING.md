# Contributing

Microstructure-Lab prioritizes deterministic behavior, explicit limitations, and tested
market microstructure logic.

## Local Checks

Before opening a pull request, run:

```bash
make lint
make typecheck
make docs-check
make test-cpp
make test
make demo-smoke
```

## Standards

- Keep matching behavior in C++.
- Do not duplicate the matching engine in Python.
- Use integer ticks for engine prices.
- Add direct tests for order book behavior.
- Label synthetic data clearly.
- Do not present synthetic results as real trading evidence.
- Record fill rate, unfilled quantity, and costs for execution strategy work.

## Generated Files

Generated run artifacts belong under `artifacts/` and are ignored by Git except for
directory placeholders. Do not commit local prompt files, caches, build outputs, or demo
artifacts.

