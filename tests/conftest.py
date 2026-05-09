from __future__ import annotations

import os
from pathlib import Path


def pytest_configure() -> None:
    index_path = Path(
        os.environ.get("PYTEST_CURRENT_TEST_INDEX", "/private/tmp/ml_pytest_runs.json")
    )
    os.environ["MICROSTRUCTURE_LAB_RUN_INDEX"] = str(index_path)
