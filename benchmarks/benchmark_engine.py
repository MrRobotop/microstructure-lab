"""Command-line entry point for the matching engine benchmark.

Prefer the package CLI for normal use:

    microstructure-lab benchmark engine --events 100000 --scenario normal
"""

from __future__ import annotations

from microstructure_lab.cli import app

if __name__ == "__main__":
    app()
