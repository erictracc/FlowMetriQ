import numpy as np
import pandas as pd
from collections import defaultdict


# ============================================================
# 1. Extract baseline duration distributions from event log
# ============================================================

def extract_baseline_distributions(df):
    """
    Given processed event log df containing ACTIVITY + EVENT_DURATION.
    Returns:
        { activity: numpy array of durations }
    """
    return {
        act: group["EVENT_DURATION"].dropna().to_numpy()
        for act, group in df.groupby("ACTIVITY")
    }


# ============================================================
# 2. Compute activity statistics (baseline)
# ============================================================

def compute_activity_stats(df):
    """
    Returns list of dicts for DataTable:
      - activity
      - contribution (hours)
      - cases
      - median / mean / 90th percentile
    """

    stats = []

    for act, group in df.groupby("ACTIVITY"):
        durations = group["EVENT_DURATION"].dropna()
        if len(durations) == 0:
            continue

        # try CASE_ID first, fallback to CASE ID
        if "CASE_ID" in group:
            n_cases = group["CASE_ID"].nunique()
        elif "CASE ID" in group:
            n_cases = group["CASE ID"].nunique()
        else:
            n_cases = len(group)

        stats.append({
            "activity": act,
            "contribution": float(durations.sum() / 60),  # minutes → hours
            "cases": n_cases,
            "median": float(np.median(durations) / 60),
            "mean": float(np.mean(durations) / 60),
            "p90": float(np.percentile(durations, 90) / 60)
        })

    return stats


# ============================================================
# 3. Apply interventions
# ============================================================

def convert_time_to_minutes(timestr):
    """Convert 'HH:MM:SS' to minutes."""
    h, m, s = timestr.split(":")
    return int(h) * 60 + int(m) + int(s) / 60


def apply_intervention_to_activity(dist, intervention):
    """
    dist: numpy array of baseline durations (minutes)
    intervention: dict with:
        - type: SPEEDUP / SLOWDOWN / DETERMINISTIC
        - value: float or HH:MM:SS
    """
    if intervention is None:
        return dist

    inter_type = intervention.get("type")
    value = intervention.get("value")

    if inter_type == "DETERMINISTIC":
        fixed_min = convert_time_to_minutes(value)
        return np.full_like(dist, fixed_min, dtype=float)

    if inter_type == "SPEEDUP":
        factor = 1 - float(value)
        return dist * factor

    if inter_type == "SLOWDOWN":
        factor = 1 + float(value)
        return dist * factor

    return dist


def apply_interventions(distributions, intervention_map):
    """
    Returns modified distributions using intervention map.
    """
    modified = {}
    for act, dist in distributions.items():
        modified[act] = apply_intervention_to_activity(dist, intervention_map.get(act))
    return modified


# ============================================================
# 4. Markov Chain Transition Model (correct CASE_ID support)
# ============================================================

def build_markov_chain(df):
    """
    Build transition probabilities:
      P(next_activity | current_activity)
    Ensures CASE_ID is standardized.
    """

    df = df.copy()

    # Fix CASE_ID naming
    if "CASE ID" in df and "CASE_ID" not in df:
        df["CASE_ID"] = df["CASE ID"]

    transitions = defaultdict(lambda: defaultdict(int))

    # Sort by case → time
    df_sorted = df.sort_values(["CASE_ID", "START TIME"])

    for case_id, group in df_sorted.groupby("CASE_ID"):
        acts = group["ACTIVITY"].tolist()

        for i in range(len(acts) - 1):
            transitions[acts[i]][acts[i + 1]] += 1

    # Normalize
    chain = {}
    for act, nexts in transitions.items():
        total = sum(nexts.values())
        chain[act] = {n: c / total for n, c in nexts.items()}

    return chain


# ============================================================
# 5. Case generation from Markov chain
# ============================================================

def generate_path_from_markov(markov_chain, start_activity):
    """
    Generate a path by walking the Markov chain.
    Stops when no outgoing transitions.
    """
    path = [start_activity]
    cur = start_activity

    while cur in markov_chain and len(markov_chain[cur]) > 0:
        next_acts = list(markov_chain[cur].keys())
        probs = list(markov_chain[cur].values())
        chosen = np.random.choice(next_acts, p=probs)
        path.append(chosen)
        cur = chosen

    return path


# ============================================================
# 6. Determine REAL starting activity
# ============================================================

def find_real_start_activity(df):
    """Most common first activity across cases."""
    if "CASE ID" in df and "CASE_ID" not in df:
        df["CASE_ID"] = df["CASE ID"]

    df_sorted = df.sort_values(["CASE_ID", "START TIME"])
    first_steps = df_sorted.groupby("CASE_ID").first()["ACTIVITY"]
    return first_steps.mode()[0]


# ============================================================
# 7. Monte-Carlo Simulation Engine
# ============================================================

def simulate_case(markov_chain, modified_dists, start_activity):
    """
    Simulates one case:
        - Walk Markov chain
        - Sample durations
        - Accumulate timestamps
    """

    timeline = []
    t = 0

    path = generate_path_from_markov(markov_chain, start_activity)

    for act in path:
        if act not in modified_dists:
            continue

        duration = float(np.random.choice(modified_dists[act]))
        t += duration
        timeline.append({"activity": act, "time": t})

    return timeline


def run_simulation(markov_chain, modified_dists, df, n_cases=200, iterations=3):
    """
    Execute simulation and return list of iteration results.
    """

    # Get actual start activity from log
    start_activity = find_real_start_activity(df)

    results = []

    for _ in range(iterations):
        iteration_cases = []

        for _ in range(n_cases):
            case_timeline = simulate_case(markov_chain, modified_dists, start_activity)
            iteration_cases.append(case_timeline)

        results.append(iteration_cases)

    return results
