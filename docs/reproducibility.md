# Run Manifests

Phase 9 records reproducibility metadata for artifact-producing runs.

## Manifest File

Each run directory writes:

```text
manifest.json
```

The manifest includes:

- `run_id`
- `created_at`
- `command`
- `git_commit` when available
- `scenario`
- `seed`
- `strategy`
- `parent_order`
- `engine_version`
- `config_hash`
- `input_hash`
- `output_paths`
- `status`
- `metrics`
- `limitations`
- `error` for failed runs

## Run Index

Runs are also registered in:

```text
artifacts/runs/index.json
```

This gives later API and dashboard phases a direct artifact index. Tests use an isolated
index path through `MICROSTRUCTURE_LAB_RUN_INDEX`.

## CLI

```bash
microstructure-lab runs list
microstructure-lab runs show --run-id <id>
```

Failed execution, replay, and comparison attempts record failed manifests where an output
directory is available.
