from __future__ import annotations

from pathlib import Path

REQUIRED_DOCS = [
    "architecture.md",
    "development.md",
    "market_microstructure.md",
    "execution_algorithms.md",
    "analytics.md",
    "performance.md",
    "limitations.md",
    "recruiter_summary.md",
]

README_COMMANDS = [
    "make install",
    "make test",
    "make lint",
    "make typecheck",
    "make build-cpp",
    "make test-cpp",
    "make demo",
    "microstructure-lab --help",
    "microstructure-lab simulate generate --scenario normal --seed 42",
    "microstructure-lab book replay --events data/synthetic/events.csv",
    "microstructure-lab execute run --strategy twap",
    "microstructure-lab execute compare --strategies twap,vwap,pov,iceberg,adaptive",
    "microstructure-lab analytics report --run artifacts/runs/comparison",
    "microstructure-lab benchmark engine --events 100000 --scenario normal",
    "microstructure-lab api serve",
    "microstructure-lab dashboard run",
]


def test_required_documentation_files_exist() -> None:
    for filename in REQUIRED_DOCS:
        path = Path("docs") / filename
        assert path.exists(), filename
        assert path.read_text().strip(), filename


def test_readme_lists_required_docs() -> None:
    readme = Path("README.md").read_text()

    for filename in REQUIRED_DOCS:
        assert f"docs/{filename}" in readme


def test_readme_lists_key_commands() -> None:
    readme = Path("README.md").read_text()

    for command in README_COMMANDS:
        assert command in readme


def test_project_attribution_is_present() -> None:
    readme = Path("README.md").read_text()
    pyproject = Path("pyproject.toml").read_text()
    recruiter_summary = Path("docs/recruiter_summary.md").read_text()

    assert "Rishabh Patil" in readme
    assert "MrRobotop" in readme
    assert "Rishabh Patil" in pyproject
    assert "https://github.com/MrRobotop/microstructure-lab" in pyproject
    assert "Rishabh Patil" in recruiter_summary


def test_repository_hygiene_files_exist() -> None:
    license_text = Path("LICENSE").read_text()
    contributing = Path("CONTRIBUTING.md").read_text()
    readme = Path("README.md").read_text()

    assert "MIT License" in license_text
    assert "Copyright (c) 2026 Rishabh Patil" in license_text
    assert "make docs-check" in contributing
    assert "[LICENSE](LICENSE)" in readme
