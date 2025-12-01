# services/prediction_service.py

import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.metrics import accuracy_score, mean_absolute_error

import plotly.express as px
import plotly.graph_objects as go


# ==========================================================
# Internal helpers
# ==========================================================

def _preprocess_for_prediction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Light preprocessing for prediction:
    - normalize CASE ID
    - parse START/END TIME
    - compute EVENT_DURATION
    """
    df = df.copy()

    if "CASE ID" in df.columns:
        df["CASE ID"] = df["CASE ID"].astype(str).str.strip()

    if "START TIME" in df.columns:
        df["START TIME"] = pd.to_datetime(df["START TIME"], errors="coerce")

    if "END TIME" in df.columns:
        df["END TIME"] = pd.to_datetime(df["END TIME"], errors="coerce")
    else:
        # If END TIME missing, approximate with START TIME
        df["END TIME"] = df["START TIME"]

    # Event duration in minutes
    if "START TIME" in df.columns and "END TIME" in df.columns:
        df["EVENT_DURATION"] = (
            df["END TIME"] - df["START TIME"]
        ).dt.total_seconds() / 60.0
    else:
        df["EVENT_DURATION"] = np.nan

    # Drop completely broken rows
    df = df.dropna(subset=["CASE ID", "EVENT", "START TIME", "END TIME"])

    return df


def _build_prefix_dataset(df: pd.DataFrame):
    """
    (Currently unused helper)
    Build a dataset at the prefix level (one row per prefix step).
    Each row represents the situation after an event, with target:
      - next event label (for next-activity prediction)
      - remaining time until case end (for remaining-time regression)
    """
    df = df.sort_values(["CASE ID", "START TIME"]).copy()

    X_rows = []
    y_next = []
    y_rem = []

    # For encoding event labels (used both as "last event" feature and "next event" target)
    le_events = LabelEncoder()
    all_events = df["EVENT"].astype(str).values
    le_events.fit(all_events)

    for case_id, g in df.groupby("CASE ID"):
        g = g.sort_values("START TIME")
        if len(g) < 2:
            # Need at least 2 events for transition + remaining time
            continue

        case_start = g["START TIME"].iloc[0]
        case_end = g["END TIME"].max()

        # Walk through prefixes, stop at second-last event
        for idx in range(len(g) - 1):
            current_row = g.iloc[idx]
            next_row = g.iloc[idx + 1]

            prefix_len = idx + 1
            elapsed = (current_row["END TIME"] - case_start).total_seconds() / 60.0
            last_event = str(current_row["EVENT"])

            # Remaining time from THIS point until end of case
            remaining = (case_end - current_row["END TIME"]).total_seconds() / 60.0
            if remaining < 0:
                continue  # skip weird timestamps

            X_rows.append(
                {
                    "prefix_len": float(prefix_len),
                    "elapsed_min": float(elapsed),
                    "last_event_label": last_event,
                }
            )
            y_next.append(str(next_row["EVENT"]))
            y_rem.append(float(remaining))

    if not X_rows:
        return None, None, None, None, None

    X = pd.DataFrame(X_rows)

    # Encode last_event_label as integer feature
    X["last_event_code"] = le_events.transform(X["last_event_label"])
    X = X[["prefix_len", "elapsed_min", "last_event_code"]]

    y_next = np.array(y_next)
    y_rem = np.array(y_rem, dtype=float)

    # Encode next_event labels for classifier target
    le_next = LabelEncoder()
    y_next_enc = le_next.fit_transform(y_next)

    return X, y_next_enc, y_rem, le_events, le_next


# ==========================================================
# Markov Chain helpers
# ==========================================================

def build_markov_chain(df: pd.DataFrame):
    """
    Build a first-order Markov Chain transition model on the given dataframe.
    Returns a dictionary:
        { prev_event: { next_event: probability } }
    """
    transitions = {}

    df = df.sort_values(["CASE ID", "START TIME"])
    for _, g in df.groupby("CASE ID"):
        events = list(g["EVENT"])
        for i in range(len(events) - 1):
            a, b = events[i], events[i + 1]
            transitions.setdefault(a, {})
            transitions[a].setdefault(b, 0)
            transitions[a][b] += 1

    # Convert counts → probabilities
    for a in transitions:
        total = sum(transitions[a].values())
        if total > 0:
            for b in transitions[a]:
                transitions[a][b] /= total

    return transitions


def predict_next_markov(chain, last_event, top_k=3):
    """
    Returns top-k next events based on Markov Chain probabilities.
    """
    if last_event not in chain:
        return []

    probs = chain[last_event]  # dict: event → prob

    sorted_events = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    sorted_events = sorted_events[:top_k]

    return [
        {"event": ev, "prob": float(p)}
        for ev, p in sorted_events
    ]


# ==========================================================
# Public API: model building + per-case prediction
# ==========================================================

def build_prediction_models(df, test_size=0.20, random_state=42):
    """
    Build next-activity and remaining-time models using ONLY training cases.
    Returns:
        {
          "rf_next": RandomForestClassifier,
          "gbr_rem": GradientBoostingRegressor,
          "le": LabelEncoder_for_last_event,
          "markov_chain": dict(prev_event -> {next_event: prob}),
          "train_cases": [...],
          "test_cases": [...],
          "next_acc": float,
          "rem_mae": float,
          "rem_mae_baseline": float,
        }
    """

    df = df.copy()
    df["CASE ID"] = df["CASE ID"].astype(str)

    # Ensure EVENT_DURATION exists (needed for remaining-time model)
    if "EVENT_DURATION" not in df.columns:
        if "START TIME" in df.columns and "END TIME" in df.columns:
            df["START TIME"] = pd.to_datetime(df["START TIME"], errors="coerce")
            df["END TIME"] = pd.to_datetime(df["END TIME"], errors="coerce")
            df["EVENT_DURATION"] = (
                df["END TIME"] - df["START TIME"]
            ).dt.total_seconds() / 60.0
        else:
            df["EVENT_DURATION"] = np.nan

    # ---- GROUP BY CASE ----
    cases = sorted(df["CASE ID"].unique())
    if len(cases) < 2:
        return None

    # ---- TRAIN/TEST SPLIT (by case) ----
    train_cases, test_cases = train_test_split(
        cases, test_size=test_size, random_state=random_state
    )

    df_train = df[df["CASE ID"].isin(train_cases)]
    df_test = df[df["CASE ID"].isin(test_cases)]

    if df_train.empty or df_test.empty:
        return None

    # ============================================
    # 1 — PREFIX DATA FOR NEXT EVENT MODEL (RF)
    # ============================================
    def build_prefix_rows(df_src):
        rows = []
        grouped = df_src.sort_values("START TIME").groupby("CASE ID")
        for case_id, g in grouped:
            events = list(g["EVENT"])
            times = list(g["START TIME"])

            for i in range(1, len(events)):
                prefix = events[:i]
                last = prefix[-1]
                next_act = events[i]

                elapsed = (times[i - 1] - times[0]).total_seconds() / 60.0

                rows.append(
                    {
                        "last_event": last,
                        "prefix_len": i,
                        "elapsed": elapsed,
                        "target": next_act,
                    }
                )
        return pd.DataFrame(rows)

    train_prefix = build_prefix_rows(df_train)
    test_prefix = build_prefix_rows(df_test)

    if train_prefix.empty or test_prefix.empty:
        return None

    # Encode activities
    le = LabelEncoder()
    train_prefix["last_event_enc"] = le.fit_transform(train_prefix["last_event"])
    test_prefix["last_event_enc"] = le.transform(test_prefix["last_event"])

    # Train RF next-activity model (train only)
    X_train = train_prefix[["last_event_enc", "prefix_len", "elapsed"]]
    y_train = train_prefix["target"]

    rf_next = RandomForestClassifier(n_estimators=120, random_state=42)
    rf_next.fit(X_train, y_train)

    # Evaluate on test cases ONLY
    X_test = test_prefix[["last_event_enc", "prefix_len", "elapsed"]]
    y_test = test_prefix["target"]
    next_acc = accuracy_score(y_test, rf_next.predict(X_test))

    # =================================================
    # 2 — REMAINING TIME PREDICTOR (GBR on train cases)
    # =================================================
    def compute_case_durations(df_src):
        grouped = df_src.groupby("CASE ID")
        return grouped["EVENT_DURATION"].sum()

    total_train = compute_case_durations(df_train)
    total_test = compute_case_durations(df_test)

    def build_remaining_rows(df_src, totals):
        rows = []
        grouped = df_src.sort_values("START TIME").groupby("CASE ID")
        for case_id, g in grouped:
            times = list(g["START TIME"])
            durs = list(g["EVENT_DURATION"])
            total_dur = totals.loc[case_id]

            elapsed = 0
            for i in range(len(times) - 1):
                elapsed += durs[i]
                rem = total_dur - elapsed
                rows.append(
                    {
                        "prefix_len": i + 1,
                        "elapsed": elapsed,
                        "remaining": max(rem, 0),
                    }
                )
        return pd.DataFrame(rows)

    train_rem = build_remaining_rows(df_train, total_train)
    test_rem = build_remaining_rows(df_test, total_test)

    if train_rem.empty or test_rem.empty:
        return None

    # Train GBR (train only)
    gbr = GradientBoostingRegressor(random_state=42)
    gbr.fit(train_rem[["prefix_len", "elapsed"]], train_rem["remaining"])

    # Evaluate on test cases ONLY
    rem_pred = gbr.predict(test_rem[["prefix_len", "elapsed"]])
    rem_mae = mean_absolute_error(test_rem["remaining"], rem_pred)

    # Baseline = always predict mean remaining of training set
    baseline = test_rem["remaining"].mean()
    rem_mae_baseline = mean_absolute_error(
        test_rem["remaining"], baseline * np.ones(len(test_rem))
    )

    # =================================================
    # 3 — MARKOV CHAIN (TRAIN CASES ONLY)
    # =================================================
    markov_chain = build_markov_chain(df_train)

    return {
        "rf_next": rf_next,
        "gbr_rem": gbr,
        "le": le,
        "markov_chain": markov_chain,
        "train_cases": train_cases,
        "test_cases": test_cases,
        "next_acc": next_acc,
        "rem_mae": rem_mae,
        "rem_mae_baseline": rem_mae_baseline,
    }


def predict_for_case(df: pd.DataFrame, models: dict, case_id: str, top_k: int = 3):
    """
    Predict next activity + remaining time for a given case using the trained models.
    Uses ONLY:
      - models["rf_next"]  (Random Forest next-activity)
      - models["gbr_rem"]  (Gradient Boosting remaining time)
      - models["le"]       (LabelEncoder for last_event)
    Returns dict:
      {
        "last_event": str or None,
        "next_events": [ {event, prob}, ... ],
        "remaining_pred": float or None,
        "remaining_true": float or None,
        "remaining_error": float or None
      }
    """

    if models is None:
        return {
            "last_event": None,
            "next_events": [],
            "remaining_pred": None,
            "remaining_true": None,
            "remaining_error": None,
        }

    # Extract models
    rf_next = models["rf_next"]
    gbr_rem = models["gbr_rem"]
    le = models["le"]

    df = df.copy()
    df["CASE ID"] = df["CASE ID"].astype(str)
    df = df.sort_values(["CASE ID", "START TIME"])

    # Extract the case trace
    case_df = df[df["CASE ID"] == str(case_id)]
    if case_df.empty:
        return {
            "last_event": None,
            "next_events": [],
            "remaining_pred": None,
            "remaining_true": None,
            "remaining_error": None,
        }

    case_df = case_df.sort_values("START TIME")

    # If case has no events at all (should not happen, but keep safe)
    if len(case_df) < 1:
        return {
            "last_event": None,
            "next_events": [],
            "remaining_pred": None,
            "remaining_true": None,
            "remaining_error": None,
        }

    # Use last event for prediction
    last_event = case_df["EVENT"].iloc[-1]
    prefix_len = len(case_df)
    case_start = case_df["START TIME"].iloc[0]
    current_end = case_df["END TIME"].iloc[-1]
    elapsed = (current_end - case_start).total_seconds() / 60.0

    # Encode last event
    try:
        last_code = le.transform([last_event])[0]
    except ValueError:
        # unseen class: fallback to 0
        last_code = 0

    X_curr = pd.DataFrame(
        [[last_code, prefix_len, elapsed]],
        columns=["last_event_enc", "prefix_len", "elapsed"],
    )

    # ---------------- NEXT EVENT PREDICTION (RF) ----------------
    if hasattr(rf_next, "predict_proba"):
        proba = rf_next.predict_proba(X_curr)[0]
        top_idx = proba.argsort()[::-1][:top_k]
        events = rf_next.classes_[top_idx]
        probs = proba[top_idx]

        next_events = [
            {"event": e, "prob": float(p)} for e, p in zip(events, probs)
        ]
    else:
        pred = rf_next.predict(X_curr)[0]
        next_events = [{"event": pred, "prob": 1.0}]

    # ---------------- REMAINING TIME PREDICTION ----------------
    remaining_pred = float(
        gbr_rem.predict(X_curr[["prefix_len", "elapsed"]])[0]
    )

    case_end = case_df["END TIME"].max()
    remaining_true = (case_end - current_end).total_seconds() / 60.0
    remaining_error = remaining_pred - remaining_true

    return {
        "last_event": str(last_event),
        "next_events": next_events,
        "remaining_pred": remaining_pred,
        "remaining_true": remaining_true,
        "remaining_error": remaining_error,
    }


# ==========================================================
# Visualization helper for probability distribution
# ==========================================================

def build_next_event_probability_figure(next_events):
    """
    Build a small bar chart showing the top-k next-event probabilities.
    next_events: list of dicts with keys {"event", "prob"}.
    """
    if not next_events:
        fig = go.Figure()
        fig.update_layout(
            title="Next-Activity Probability Distribution",
            height=300,
        )
        return fig

    labels = [x["event"] for x in next_events]
    probs = [x["prob"] for x in next_events]

    fig = px.bar(
        x=labels,
        y=probs,
        text=[f"{p*100:.1f}%" for p in probs],
        labels={"x": "Event", "y": "Probability"},
        title="Next-Activity Probability Distribution (Top Predictions)",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        yaxis=dict(range=[0, 1]),
        margin=dict(l=40, r=20, t=60, b=60),
    )
    return fig


# ==========================================================
# Optional: RF rollout simulator (not currently used in UI)
# ==========================================================

def simulate_future_events(df, models, case_id, steps=5):
    """
    Simulate the next N events using Random Forest rollout.
    (Uses rf_next + le from models; falls back to trivial Markov if RF is very uncertain.)
    """

    if "rf_next" not in models or "le" not in models:
        return []

    rf = models["rf_next"]
    enc = models["le"]

    df_local = df.copy()
    df_local["CASE ID"] = df_local["CASE ID"].astype(str)

    case_df = df_local[df_local["CASE ID"] == str(case_id)].sort_values("START TIME")

    if case_df.empty:
        return []

    prefix_events = list(case_df["EVENT"])
    simulated = []

    for _ in range(steps):
        if not prefix_events:
            break

        last_event = prefix_events[-1]

        try:
            last_code = enc.transform([last_event])[0]
        except ValueError:
            last_code = 0

        X = pd.DataFrame(
            [[last_code, len(prefix_events), 0.0]],
            columns=["last_event_enc", "prefix_len", "elapsed"],
        )

        # Predict probabilities
        if hasattr(rf, "predict_proba"):
            probs = rf.predict_proba(X)[0]
            top_idx = probs.argmax()
            top_prob = probs[top_idx]
            predicted_event = rf.classes_[top_idx]
        else:
            predicted_event = rf.predict(X)[0]
            top_prob = 1.0

        simulated.append(
            {"event": str(predicted_event), "prob": float(top_prob)}
        )

        prefix_events.append(predicted_event)

    return simulated
