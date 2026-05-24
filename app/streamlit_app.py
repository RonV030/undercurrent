"""Streamlit dashboard displaying Google Trends mental health signals for Germany."""

import os

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DUCKDB_PATH = os.environ.get("DUCKDB_PATH", "undercurrent.duckdb")


@st.cache_data
def load_last_updated() -> str:
    """Return the most recent week_start date in the mart table as a formatted string.

    Used to show the user when the data was last refreshed without exposing
    the raw date object to the rendering layer.

    Returns:
        Date string formatted as DD/MM/YYYY, e.g. '20/05/2026'.
    """
    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    result = conn.execute(
        "SELECT MAX(week_start) FROM main.mart_mental_health_trends"
    ).fetchone()
    conn.close()
    if result and result[0]:
        return result[0].strftime("%d/%m/%Y")
    return "unknown"


@st.cache_data
def load_trends() -> pd.DataFrame:
    """Query the mart table from DuckDB and return a DataFrame.

    Opens the connection in read-only mode so Streamlit cannot write to or
    lock the database file while dbt may also need access.

    Returns:
        DataFrame with columns: week_start, keyword, interest_score.
    """
    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    df = conn.execute(
        "SELECT * FROM main.mart_mental_health_trends ORDER BY week_start"
    ).df()
    conn.close()
    return df


@st.cache_data
def load_correlation() -> pd.DataFrame:
    """Compute Pearson correlation between keyword columns from the staging view.

    Uses stg_google_trends rather than the mart because the staging view is
    already in wide format (one column per keyword), avoiding a pivot step.
    Partial weeks are excluded so an incomplete final week does not skew the result.

    Returns:
        Symmetric correlation matrix DataFrame, values between -1 and 1.
    """
    conn = duckdb.connect(DUCKDB_PATH, read_only=True)
    df = conn.execute(
        """
        SELECT depression, angst, burnout, therapie, psychologe
        FROM main.stg_google_trends
        WHERE NOT is_partial
        """
    ).df()
    conn.close()
    return df.corr()


def main() -> None:
    """Render the Streamlit dashboard."""
    st.set_page_config(
        page_title="Undercurrent — Mental Health Trends",
        layout="wide",
    )

    st.title("Mental Health Search Trends in Germany")
    st.caption(
        "Weekly Google Trends search interest (0-100, relative scale) "
        "for German mental health keywords. Source: Google Trends via pytrends."
    )
    st.caption(f"Data last updated: {load_last_updated()}")

    df = load_trends()

    # Sidebar filter — lets the user toggle individual keywords on and off.
    all_keywords = sorted(df["keyword"].unique())
    selected = st.multiselect(
        label="Keywords",
        options=all_keywords,
        default=all_keywords,
    )

    if not selected:
        st.warning("Select at least one keyword to display the chart.")
        return

    filtered = df[df["keyword"].isin(selected)]

    fig = px.line(
        filtered,
        x="week_start",
        y="interest_score",
        color="keyword",
        labels={
            "week_start": "Week",
            "interest_score": "Search Interest (0–100)",
            "keyword": "Keyword",
        },
        title="Mental Health Search Interest — Germany, Past 12 Months",
    )

    # Show all keyword values together when hovering over a date.
    fig.update_layout(hovermode="x unified")

    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.caption(
        "Values are relative, not absolute. Google scales each keyword so its "
        "peak week in the selected period equals 100. A value of 50 means half "
        "as many searches as the peak week, not 50 searches."
    )

    st.divider()
    st.subheader("Keyword Correlations")
    st.caption(
        "Pearson correlation between keyword search interest over the past 12 months. "
        "A value close to 1 means the two keywords rise and fall together in the same weeks. "
        "A value close to 0 means their movements are unrelated."
    )

    corr = load_correlation()

    # Keep side margins so the heatmap doesn't stretch into an unreadable rectangle.
    left, centre, right = st.columns([1, 6, 1])
    with centre:
        fig_corr = px.imshow(
            corr,
            text_auto=".2f",  # type: ignore[arg-type]
            color_continuous_scale="RdBu",
            zmin=-1,
            zmax=1,
            title="Pearson Correlation — Mental Health Keywords",
            aspect="auto",
        )
        fig_corr.update_layout(coloraxis_colorbar_title="r", height=520)
        st.plotly_chart(fig_corr, use_container_width=True)


if __name__ == "__main__":
    main()
