# Docker and CI

Phase 14 includes Docker, GitHub Actions, and static Python type checking.

## Docker

Build:

```bash
docker build -t microstructure-lab .
```

Run CLI help:

```bash
docker run --rm microstructure-lab
```

Run with Compose:

```bash
docker compose up microstructure-lab
docker compose up api
docker compose up dashboard
```

The Compose file mounts local `artifacts/` and `data/` directories so generated demo
artifacts remain visible on the host.

## CI

GitHub Actions runs:

- install system build tools
- install Python package in editable mode
- `make lint`
- `make typecheck`
- `make test-cpp`
- `make test`
- `make demo-smoke`
- `docker build -t microstructure-lab:ci .`
- `docker run --rm microstructure-lab:ci microstructure-lab --help`

CI does not require paid market data or secrets.

## Type checking

The typed baseline checks the production source tree:

```bash
make typecheck
```

`mypy` currently covers `src/microstructure_lab`, `api`, and `dashboard`. Tests remain
covered by pytest and ruff.
