import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def event_frequency_bar(df: pd.DataFrame):
    """Bar chart: frequency of each event type."""
    if "EVENT" not in df.columns:
        return go.Figure()

    freq = df["EVENT"].value_counts().reset_index()
    freq.columns = ["EVENT", "COUNT"]

    fig = px.bar(
        freq,
        x="EVENT",
        y="COUNT",
        title="Frequency of Events",
        text_auto=True,
    )

    fig.update_layout(xaxis_title="Event", yaxis_title="Count")
    return fig


def duration_distribution(df: pd.DataFrame):
    """Histogram of all event durations."""
    if "EVENT_DURATION" not in df.columns:
        return go.Figure()

    fig = px.histogram(
        df,
        x="EVENT_DURATION",
        nbins=50,
        title="Distribution of Event Durations (minutes)",
    )

    fig.update_layout(xaxis_title="Duration (min)", yaxis_title="Count")
    return fig


def duration_boxplot(df: pd.DataFrame):
    """Boxplot of duration per event."""
    if "EVENT" not in df.columns or "EVENT_DURATION" not in df.columns:
        return go.Figure()

    fig = px.box(
        df,
        x="EVENT",
        y="EVENT_DURATION",
        title="Activity Duration Variability (Boxplot)",
    )

    fig.update_layout(xaxis_title="Event", yaxis_title="Duration (min)")
    return fig


def event_timeseries(df: pd.DataFrame):
    """Count events per day to show workload trends."""
    if "START TIME" not in df.columns:
        return go.Figure()

    ts = df.groupby(df["START TIME"].dt.date).size().reset_index(name="COUNT")

    fig = px.line(
        ts,
        x="START TIME",
        y="COUNT",
        title="Time Series of Event Arrivals",
    )

    fig.update_layout(xaxis_title="Date", yaxis_title="Events")
    return fig
