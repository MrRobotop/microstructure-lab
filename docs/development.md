# Development

This guide describes the local development workflow.

## Environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Checks

```bash
make lint
make typecheck
make docs-check
make test-cpp
make test
make demo-smoke
```

## C++ Build

```bash
make build-cpp
make test-cpp
```

The Python package builds the C++ extension through `scikit-build-core`, CMake, and
pybind11.

## Docker

```bash
docker build -t microstructure-lab .
docker run --rm microstructure-lab microstructure-lab --help
```

## Repository Hygiene

The following are intentionally ignored:

- local virtual environments
- Python caches
- CMake and wheel build outputs
- generated run artifacts
- local prompt and agent instruction files

