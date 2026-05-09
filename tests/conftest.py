from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolate_run_index(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("MICROSTRUCTURE_LAB_RUN_INDEX", str(tmp_path / "run_index.json"))
