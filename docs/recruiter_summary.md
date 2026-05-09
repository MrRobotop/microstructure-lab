# Recruiter Summary

Microstructure-Lab is a market microstructure research and execution simulation platform
designed to show both trading-systems engineering and quantitative research judgment.

Author: Rishabh Patil ([MrRobotop](https://github.com/MrRobotop)).

## What It Demonstrates

- C++ price-time-priority matching engine
- Python research and simulation platform
- pybind11 bridge between systems code and Python workflows
- deterministic synthetic market data
- execution strategies including TWAP, VWAP, POV, Iceberg, and Adaptive POV
- transaction cost analytics with fill rate and unfilled quantity
- artifact-first reports and run manifests
- FastAPI artifact service
- Streamlit dashboard
- Docker and GitHub Actions CI

## Why C++ Is Used

C++ owns the matching engine because matching correctness, deterministic behavior, memory
ownership, and low-level implementation quality matter for trading infrastructure roles.
The engine uses integer ticks and direct tests for order-book behavior.

## Why Python Is Used

Python owns orchestration, synthetic data generation, execution strategies, analytics,
reports, API, and dashboard layers. This keeps research workflows ergonomic while the
matching engine remains in C++.

## Reproducible Demo

A reviewer can run:

```bash
make install
make demo
```

The demo generates synthetic events, replays the order book, runs TWAP and POV, computes
transaction cost metrics, writes a Markdown report, and stores artifacts under
`artifacts/runs/demo`.

No paid market data is required.

## Engineering Standards

The repository includes:

- direct C++ matching engine tests
- Python tests for bindings, synthetic data, execution, analytics, API, dashboard, demo,
  and benchmarks
- ruff linting
- mypy type checking
- CMake builds
- scikit-build-core packaging
- Docker build
- GitHub Actions CI

## Honest Scope

The project uses synthetic data and does not claim real trading profitability. It is built
to demonstrate architecture, correctness, reproducibility, and market microstructure
understanding.
