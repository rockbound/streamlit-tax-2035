from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

STREAMLIT_DIR = Path(__file__).resolve().parent
STREAMLIT_VALUES_PATH = (STREAMLIT_DIR / "values.csv").resolve()
TITLE = "Rockbound Capital Tax-Efficient 2035 Portfolio"
PALETTE = [
    "#D9B38D",  # Gold
    "#5D6D7E",  # Gray
    "#4781A7",  # Blue
    "#687D71",  # Pale Green
    "#589A5D",  # Light Green
    "#746198",  # Purple
    "#B3AF38",  # Yellow
    "#B27D58",  # Orange
    "#A75051",  # Red
    "#1B4A3A",  # Dark Green
    "#1A2A44",  # DarkNavy
]


def load_and_prepare_values(path: Path) -> pd.DataFrame:
    assert path.exists(), f"Values CSV not found at {path}"
    df = pd.read_csv(path)
    assert "date" in df.columns, f"Expected a 'date' column in {path}. Got: {df.columns.tolist()}"
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(by="date")
    return df


@st.cache_data(ttl="1d")
def load_data(local_path: Path) -> pd.DataFrame:
    assert local_path.exists(), f"Values CSV not found at {local_path}"
    return load_and_prepare_values(local_path)


def date_bounds(df: pd.DataFrame) -> tuple[datetime, datetime]:
    assert not df.empty, "No data loaded for slider bounds."
    min_date = df["date"].min()
    max_date = df["date"].max()
    assert min_date <= max_date, f"Invalid date range: min_date={min_date}, max_date={max_date}"
    return min_date.to_pydatetime(), max_date.to_pydatetime()


def render_metrics_and_chart(source_df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame | None:
    if source_df.empty:
        st.warning("No data available for the selected dataset.")
        return

    date_col = source_df.columns[0]
    value_cols = source_df.columns[1:]
    assert len(value_cols) > 0, f"Expected at least one value column. Got: {value_cols}"

    mask = (source_df[date_col] >= start_date) & (source_df[date_col] <= end_date)
    filtered_df = source_df.loc[mask]

    if filtered_df.empty:
        st.warning("No data available in this date range.")
        return

    st.markdown("### Performance in Selected Range")
    cols = st.columns(len(value_cols))

    for idx, col_name in enumerate(value_cols):
        start_val = filtered_df.iloc[0][col_name]
        end_val = filtered_df.iloc[-1][col_name]
        pct_change = ((end_val - start_val) / start_val) if start_val != 0 else 0.0
        sign = "+" if pct_change >= 0 else ""
        with cols[idx]:
            st.metric(
                label=col_name,
                value=f"${end_val:,.0f}",
                delta=f"{sign}{pct_change:.2%}",
            )

    fig = px.line(
        filtered_df,
        x=date_col,
        y=value_cols,
        title=f"Trends from {start_date.strftime('%b %d')} to {end_date.strftime('%b %d')}",
        template="plotly_white",
        color_discrete_sequence=PALETTE,
    )

    fig.update_layout(
        hovermode="x unified",
        legend_title_text="Portfolio",
        legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5),
    )
    fig.update_traces(hovertemplate="$%{y:,.0f}<extra></extra>")
    fig.update_xaxes(title_text="")
    fig.update_yaxes(tickformat="$,.0f", title_text="Portfolio Value")
    st.plotly_chart(fig, use_container_width=True)

    return filtered_df


def main() -> None:
    st.set_page_config(page_title=TITLE, layout="wide")
    st.title(TITLE)

    base_df = load_data(STREAMLIT_VALUES_PATH)

    min_date, max_date = date_bounds(base_df)
    # default_start = max_date - timedelta(days=365)
    default_start = datetime(2025, 1, 1)
    st.session_state.setdefault("date_range", (max(default_start, min_date), max_date))

    start_date, end_date = st.session_state["date_range"]

    filtered_df = render_metrics_and_chart(base_df, start_date, end_date)

    # st.subheader("Filter by Date")
    st.slider(
        "Select Date Range:",
        min_value=min_date,
        max_value=max_date,
        format="MM/DD/YY",
        key="date_range",
    )

    if filtered_df is not None:
        with st.expander("View Source Data"):
            st.dataframe(filtered_df)


if __name__ == "__main__":
    main()
