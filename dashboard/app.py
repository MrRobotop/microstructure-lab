"""Streamlit dashboard for stored Microstructure-Lab artifacts."""

from __future__ import annotations

from typing import Any

from microstructure_lab.runs.artifacts import (
    leaderboard_rows,
    result_metrics_for_run,
    run_summaries,
)


def build_overview_cards(runs: list[dict[str, Any]]) -> dict[str, int]:
    completed = sum(1 for run in runs if run["status"] == "completed")
    failed = sum(1 for run in runs if run["status"] == "failed")
    return {"runs": len(runs), "completed": completed, "failed": failed}


def select_default_run_id(runs: list[dict[str, Any]]) -> str | None:
    if not runs:
        return None
    return runs[-1]["run_id"]


def metrics_for_display(run_id: str | None) -> dict[str, Any]:
    if run_id is None:
        return {}
    return result_metrics_for_run(run_id) or {}


def render_dashboard() -> None:
    import streamlit as st

    st.set_page_config(page_title="Microstructure-Lab", layout="wide")
    st.title("Microstructure-Lab")
    st.caption("Synthetic market microstructure and execution simulation artifacts.")

    runs = run_summaries()
    cards = build_overview_cards(runs)
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Runs", cards["runs"])
    col_b.metric("Completed", cards["completed"])
    col_c.metric("Failed", cards["failed"])

    tab_runs, tab_leaderboard, tab_metrics, tab_limitations = st.tabs(
        ["Runs", "Leaderboard", "Metrics", "Limitations"]
    )

    with tab_runs:
        if not runs:
            st.info("No indexed runs found. Run a synthetic comparison or execution first.")
        else:
            st.dataframe(runs, use_container_width=True)

    with tab_leaderboard:
        leaderboard = leaderboard_rows()
        if leaderboard:
            st.dataframe(leaderboard, use_container_width=True)
        else:
            st.info("No leaderboard rows available.")

    with tab_metrics:
        run_id = st.selectbox(
            "Run",
            options=[run["run_id"] for run in runs],
            index=max(0, len(runs) - 1) if runs else None,
            placeholder="Select a run",
        )
        metrics = metrics_for_display(run_id)
        if metrics:
            st.json(metrics)
        else:
            st.info("No execution metrics artifact is available for this run.")

    with tab_limitations:
        st.markdown(
            """
- All current data is synthetic and intended for deterministic demos.
- Dashboard views read stored artifacts and do not recompute simulations.
- Strategy results are not evidence of live trading performance.
- The local run index is a JSON artifact store, not a production metadata service.
"""
        )


if __name__ == "__main__":
    render_dashboard()
