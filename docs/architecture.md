# Architecture

Microstructure-Lab separates low-level market mechanics from research ergonomics.

## C++ Core

The C++ layer owns behavior where determinism, performance, and systems credibility
matter:

- order model
- trade model
- event model
- limit order book
- price-time-priority matching engine
- snapshot generation
- deterministic replay hooks
- performance benchmark hooks

Prices are represented as integer ticks internally. Floating-point prices are avoided in
the engine to prevent rounding ambiguity in matching logic.

## Python Platform

The Python layer owns workflows where usability and research iteration matter:

- CLI
- configuration
- synthetic event generation
- execution strategy orchestration
- transaction cost analytics
- reports
- run manifests
- API
- dashboard

Python must call the C++ engine through the `microstructure_lab._core` extension module.
It must not implement a second matching engine.

## Boundary

The intended call path is:

```text
CLI / simulation / execution
  -> Python wrapper
  -> pybind11 extension
  -> C++ MatchingEngine
```

The wrapper may translate schemas and errors, but matching behavior belongs in C++.

## Current Status

Phase 1 created the repository scaffold, Python package, CMake structure, minimal CLI,
and smoke tests.

Phase 2 adds foundational C++ domain models for orders, trades, events, and snapshots.

Phase 3 adds a C++ price-time-priority matching engine. `Book` owns one symbol's bid and
ask levels, active order lookup, matching, cancellation, and snapshots. `MatchingEngine`
routes events and symbol-level operations to books.

Phase 4 exposes the C++ core through pybind11 as `microstructure_lab._core` and provides
a thin Python import surface at `microstructure_lab.orderbook.core`. The Python layer
does not duplicate matching logic.

Phase 5 adds Pydantic event schemas, deterministic synthetic event generation, scenario
configuration, and replay orchestration. Replay converts validated Python event rows into
C++ `Event` objects and writes trade and snapshot artifacts from the C++ engine.

Phase 6 adds Python execution strategies and an execution simulator. Strategies emit
child market orders during replay; the C++ engine determines actual fills. Results record
child orders, fills, realized quantity, unfilled quantity, fill rate, and cost notional in
integer tick units.

Phase 7 adds artifact-first transaction cost analytics. Reports consume stored execution
artifacts, compute unit-explicit fill and cost metrics, and mark benchmark-dependent
metrics unavailable when inputs such as arrival price or VWAP are missing.

Phase 8 adds deterministic strategy comparison. A shared synthetic event stream is
generated once, every strategy is run against that same stream through the C++ engine, and
the comparison runner writes a leaderboard, JSON summary, and Markdown report.

Phase 9 adds run manifests and an indexed artifact store. Artifact-producing workflows
write `manifest.json` with command, hashes, inputs, outputs, status, metrics, limitations,
and failure details where applicable. The run index supports later API and dashboard
discovery without arbitrary directory scans.

Phase 10 adds a read-only FastAPI service over the indexed artifact store. The API reads
stored manifests, execution results, comparison summaries, and leaderboard data; it does
not recompute simulations by default.

Phase 11 adds a Streamlit dashboard using the same shared artifact reader as the API. It
shows indexed runs, leaderboards, execution metrics, and synthetic-data limitations
without recomputing simulations.

Phase 12 adds a deterministic end-to-end demo that generates synthetic events, replays the
book, runs TWAP and POV, computes comparison metrics, writes a Markdown report, and
registers artifacts for `runs list`, the API, and the dashboard.

Phase 14 hardens Docker and GitHub Actions. CI installs build tools, runs lint,
type checks the production Python source, builds/tests the C++ engine, runs Python
tests, executes a lightweight demo smoke workflow, and verifies that the Docker image
builds and exposes the CLI.

Phase 15 adds a conservative matching engine benchmark command. The benchmark reports
local timing observations for deterministic synthetic event application and documents
that results are not portable performance claims.

Phase 16 completes the recruiter-facing documentation set with market microstructure
notes, explicit limitations, and a concise project summary for technical reviewers.

Phase 17 adds a documentation check target that validates the required documentation set
and key README command snippets.

Phase 18 verifies repository readiness for an initial commit, including author metadata,
private prompt ignores, generated artifact ignores, and a dry-run commit candidate list.

Phase 19 adds publishing hygiene: MIT license text, contribution guidance, development
workflow documentation, and docs checks that guard those repository-level files.

## Synthetic Event Format

Synthetic event CSV files include:

```text
timestamp, sequence, event_type, symbol, order_id, side, price_ticks, quantity,
scenario, seed, is_synthetic
```

The `is_synthetic` field is mandatory and must be true. This keeps public demos explicit
about their data source.
