.PHONY: install test lint typecheck docs-check format build-cpp test-cpp clean demo demo-smoke

PYTHON ?= python
BUILD_DIR ?= build/cmake

install:
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

typecheck:
	$(PYTHON) -m mypy

docs-check:
	$(PYTHON) -m pytest tests/test_docs.py

format:
	$(PYTHON) -m ruff format .

build-cpp:
	cmake -S . -B $(BUILD_DIR)
	cmake --build $(BUILD_DIR)

test-cpp: build-cpp
	ctest --test-dir $(BUILD_DIR) --output-on-failure

demo:
	$(PYTHON) -m microstructure_lab.cli demo

demo-smoke:
	$(PYTHON) -m microstructure_lab.cli demo --events 40 --quantity 100 --duration 30 --output artifacts/runs/demo-smoke

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
