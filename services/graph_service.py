import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ==========================================================
# INTERNAL CLEANING HELPERS
# ==========================================================

def _clean_durations(df):
    """Remove negative and extreme outlier durations."""
    if "EVENT_DURATION" not in df.columns:
        return df

    cleaned = df[df["EVENT_DURATION"].notna()]
    cleaned = cleaned[cleaned["EVENT_DURATION"] >= 0]

    # Remove extreme 1% outliers
    upper = cleaned["EVENT_DURATION"].quantile(0.99)
    cleaned = cleaned[cleaned["EVENT_DURATION"] <= upper]

    return cleaned


def _clean_timestamps(df):
    """Remove extreme timestamp outliers."""
    if "START TIME" not in df.columns:
        return df

    cleaned = df.dropna(subset=["START TIME"])

    # Clip timestamps to 1st–99th percentile
    low = cleaned["START TIME"].quantile(0.01)
    high = cleaned["START TIME"].quantile(0.99)

    return cleaned[(cleaned["START TIME"] >= low) & (cleaned["START TIME"] <= high)]


# ==========================================================
# 1. EVENT FREQUENCY BAR CHART (RESTORED ORIGINAL)
# ==========================================================
def event_frequency_bar(df: pd.DataFrame):
    """
    Bar chart of event frequencies.
    Restored to original behavior: show ALL events.
    """

    if df.empty or "EVENT" not in df.columns:
        return go.Figure()

    counts = df["EVENT"].value_counts().reset_index()
    counts.columns = ["EVENT", "COUNT"]

    fig = px.bar(
        counts,
        x="EVENT",
        y="COUNT",
        text="COUNT",
        title="Event Frequency (Most Common Activities)",
        color="COUNT",
        color_continuous_scale="Blues",
    )

    fig.update_traces(textposition="outside")
    fig.update_layout(
        xaxis_tickangle=-35,
        margin=dict(l=20, r=20, t=50, b=150),   # ⬅ More room for labels
        height=550,                             # ⬅ Increased height
    )

    return fig


# ==========================================================
# 2. EVENT DURATION DISTRIBUTION (HISTOGRAM)
# ==========================================================
def duration_distribution(df: pd.DataFrame):
    if df.empty or "EVENT_DURATION" not in df.columns:
        return go.Figure()

    cleaned = _clean_durations(df)

    fig = px.histogram(
        cleaned,
        x="EVENT_DURATION",
        nbins=40,
        title="Distribution of Event Durations (Minutes)",
        color_discrete_sequence=["#4C78A8"],
    )

    fig.update_layout(
        xaxis_title="Duration (Minutes)",
        yaxis_title="Count",
        margin=dict(l=20, r=20, t=50, b=50),
        height=450,
    )

    return fig


# ==========================================================
# 3. BOX PLOT OF DURATIONS PER EVENT (RESTORED ORIGINAL)
# ==========================================================
def duration_boxplot(df: pd.DataFrame):
    """
    Cleaner, readable boxplot:
    - Shows only the Top 12 most frequent events
    - Removes noisy rarely-occurring activities
    """

    if df.empty or "EVENT" not in df.columns or "EVENT_DURATION" not in df.columns:
        return go.Figure()

    cleaned = _clean_durations(df)

    # --- NEW: limit to Top 12 most frequent events ---
    top_events = (
        cleaned["EVENT"]
        .value_counts()
        .nlargest(12)
        .index
    )

    cleaned = cleaned[cleaned["EVENT"].isin(top_events)]

    fig = px.box(
        cleaned,
        x="EVENT",
        y="EVENT_DURATION",
        color="EVENT",
        title="Activity Duration Variation (Top 12 Events)",
    )

    fig.update_layout(
        xaxis_tickangle=-35,
        yaxis_title="Duration (Minutes)",
        legend_title="Event",
        margin=dict(l=40, r=20, t=50, b=150),
        height=600,
    )

    return fig


# ==========================================================
# 4. TIME SERIES OF EVENT VOLUME (with outlier-stamp fix)
# ==========================================================
def event_timeseries(df: pd.DataFrame):
    if df.empty or "START TIME" not in df.columns:
        return go.Figure()

    cleaned = _clean_timestamps(df)
    if cleaned.empty:
        return go.Figure()

    ts = cleaned.resample("D", on="START TIME").size().reset_index()
    ts.columns = ["DATE", "COUNT"]

    fig = px.line(
        ts,
        x="DATE",
        y="COUNT",
        markers=True,
        title="Daily Event Volume Over Time",
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Event Count",
        margin=dict(l=20, r=20, t=50, b=50),
        height=450,
    )

    return fig


# ==========================================================
# MASTER FUNCTION
# ==========================================================
def generate_all_graphs(df: pd.DataFrame):
    return (
        event_frequency_bar(df),
        duration_distribution(df),
        duration_boxplot(df),
        event_timeseries(df),
    )
