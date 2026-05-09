# Streamlit Dashboard

Phase 11 adds a Streamlit dashboard over stored Microstructure-Lab artifacts.

## Run

Install the dashboard extra if needed:

```bash
python -m pip install -e ".[dashboard]"
```

Then launch:

```bash
microstructure-lab dashboard run
```

Optional:

```bash
microstructure-lab dashboard run --port 8501
```

## Views

- Runs: indexed run manifests.
- Leaderboard: strategy comparison rows when available.
- Metrics: execution result metrics for a selected run.
- Limitations: synthetic data and artifact-store caveats.

## Boundary

The dashboard reads stored artifacts through the same shared artifact reader used by the
API. It does not recompute simulations and does not require real market data.
