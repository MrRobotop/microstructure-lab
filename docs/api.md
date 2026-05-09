# FastAPI Service

Phase 10 adds a read-only API for stored Microstructure-Lab artifacts.

## Run

```bash
microstructure-lab api serve
```

Optional:

```bash
microstructure-lab api serve --host 127.0.0.1 --port 8000
```

## Endpoints

```text
GET /health
GET /runs
GET /runs/{run_id}
GET /runs/{run_id}/metrics
GET /leaderboard
```

## Boundary

The API reads run manifests, summaries, result artifacts, and reports from the artifact
store. It does not recompute simulations by default and does not require real market data.

## Limitations

The run index is a local JSON file. This is appropriate for the project demo but is not a
concurrent production metadata store.
