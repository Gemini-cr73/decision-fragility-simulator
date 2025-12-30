# app/ui/streamlit_app.py

import sys
from pathlib import Path

# ------------------------------------------------------------------
# Make sure the project root (decision-fragility-simulator) is on sys.path
# so that `import app.*` works when Streamlit runs this file directly.
# ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]  # .../decision-fragility-simulator
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ------------------------------------------------------------------
# Standard imports
# ------------------------------------------------------------------
import random
from typing import Dict, List, Tuple
import io
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from app.models.db import get_db_connection
from app.analytics.report import build_report   # ⬅️ only build_report now
from app.services.bulk_ingest import (
    generate_events,
    bulk_insert,
    ensure_raw_schema_and_table,
)
from app.services.ingest_actions import insert_action


# ----------------------------
# Helpers (DB reads)
# ----------------------------
def fetch_action_counts() -> List[Tuple[str, int]]:
    """
    Return [(action, count), ...] from raw.user_actions.
    Ensures schema/table exist before querying.
    """
    # 🔐 Make sure the table exists on every read
    ensure_raw_schema_and_table()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT action, COUNT(*) AS count
        FROM raw.user_actions
        GROUP BY action
        ORDER BY action;
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    out: List[Tuple[str, int]] = []
    for r in rows:
        if isinstance(r, dict):
            out.append((r["action"], int(r["count"])))
        else:
            out.append((r[0], int(r[1])))
    return out


def fetch_total_events() -> int:
    """
    Return total number of rows in raw.user_actions.
    Ensures schema/table exist before querying.
    """
    # 🔐 Make sure the table exists on every read
    ensure_raw_schema_and_table()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM raw.user_actions;")
    row = cur.fetchone()
    cur.close()
    conn.close()

    if isinstance(row, dict):
        return int(row.get("count", list(row.values())[0]))
    return int(row[0])


def fetch_action_transitions(limit: int = 50) -> List[Tuple[str, str, int]]:
    """
    Compute action -> next_action transition counts across user sessions.

    Uses a window function over (user_id, id) so we follow insertion order
    without requiring a created_at column. Returns
    a list of (from_action, to_action, count), ordered by count DESC.
    """
    ensure_raw_schema_and_table()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        WITH ordered AS (
            SELECT
                user_id,
                action AS from_action,
                LEAD(action) OVER (
                    PARTITION BY user_id
                    ORDER BY id
                ) AS to_action
            FROM raw.user_actions
        )
        SELECT
            from_action,
            to_action,
            COUNT(*) AS count
        FROM ordered
        WHERE to_action IS NOT NULL
        GROUP BY from_action, to_action
        ORDER BY count DESC
        LIMIT %s;
        """,
        (limit,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    out: List[Tuple[str, str, int]] = []
    for r in rows:
        if isinstance(r, dict):
            out.append(
                (
                    str(r["from_action"]),
                    str(r["to_action"]),
                    int(r["count"]),
                )
            )
        else:
            out.append((str(r[0]), str(r[1]), int(r[2])))
    return out


def fetch_transition_sequences(
    from_action: str,
    to_action: str,
    max_examples: int = 20,
    window_before: int = 2,
    window_after: int = 2,
) -> List[Dict[str, object]]:
    """
    For a given transition (from_action -> to_action), return a small set of
    concrete user sequences that contain that transition.

    Each sequence is a short window of actions around the transition for
    a particular user_id.
    """
    ensure_raw_schema_and_table()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT user_id, id, action
        FROM raw.user_actions
        ORDER BY user_id, id;
        """
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # Normalize to a simple list of (user_id, id, action)
    events: List[Tuple[int, int, str]] = []
    for r in rows:
        if isinstance(r, dict):
            events.append(
                (
                    int(r["user_id"]),
                    int(r["id"]),
                    str(r["action"]),
                )
            )
        else:
            events.append(
                (
                    int(r[0]),  # user_id
                    int(r[1]),  # id
                    str(r[2]),  # action
                )
            )

    # Group by user_id
    events_by_user: Dict[int, List[Dict[str, object]]] = {}
    for user_id, ev_id, action in events:
        events_by_user.setdefault(user_id, []).append(
            {"id": ev_id, "action": action}
        )

    results: List[Dict[str, object]] = []
    example_index = 1

    # For each user sequence, find windows where the transition occurs
    for user_id, seq in events_by_user.items():
        actions = [e["action"] for e in seq]
        n = len(actions)
        for i in range(n - 1):
            if actions[i] == from_action and actions[i + 1] == to_action:
                start_idx = max(0, i - window_before)
                end_idx = min(n - 1, i + window_after)
                window = seq[start_idx : end_idx + 1]

                window_actions = [w["action"] for w in window]
                window_ids = [w["id"] for w in window]

                results.append(
                    {
                        "example_index": example_index,
                        "user_id": user_id,
                        "event_ids": ", ".join(str(eid) for eid in window_ids),
                        "sequence": " → ".join(window_actions),
                    }
                )
                example_index += 1

                if len(results) >= max_examples:
                    break
        if len(results) >= max_examples:
            break

    return results


def get_report_history(
    limit: int = 50,
    start: datetime | None = None,
    end: datetime | None = None,
):
    """
    Read recent rows from analytics.reports.

    Returns rows shaped like:
      (id, created_at, total_events, fragility_score, fragility_label, details)
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Ensure schema/table exist (safe to run repeatedly)
    cur.execute("CREATE SCHEMA IF NOT EXISTS analytics;")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analytics.reports (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            total_events INTEGER NOT NULL,
            fragility_score DOUBLE PRECISION NOT NULL,
            fragility_label TEXT NOT NULL,
            details TEXT NOT NULL
        );
        """
    )

    query = """
        SELECT id, created_at, total_events, fragility_score, fragility_label, details
        FROM analytics.reports
    """
    conditions = []
    params: List[object] = []

    if start is not None:
        conditions.append("created_at >= %s")
        params.append(start)
    if end is not None:
        conditions.append("created_at <= %s")
        params.append(end)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC LIMIT %s;"
    params.append(limit)

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def parse_report_text(report_text: str) -> Dict[str, str]:
    """
    Extract score + label from the report text.
    Works even if formatting changes slightly.
    """
    score = ""
    label = ""
    for line in report_text.splitlines():
        low = line.lower()
        if "fragility score" in low:
            score = line.split(":")[-1].strip()
        if "classification" in low or "fragility classification" in low:
            label = line.split(":")[-1].strip()
    return {"score": score, "label": label}


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(
    page_title="Decision-Fragility Simulator",
    layout="wide",
)

st.title("Decision-Fragility Simulator — Dashboard")
st.caption(
    "Live fragility metrics from PostgreSQL (ai_projects). "
    "Deterministic bulk-ingest option included."
)

# Sidebar controls
st.sidebar.header("Controls")

seed_enabled = st.sidebar.checkbox("Deterministic bulk ingest (seeded)", value=True)
seed_value = st.sidebar.number_input("Seed", min_value=0, max_value=999_999, value=73, step=1)

num_users = st.sidebar.number_input(
    "Bulk ingest: users", min_value=1, max_value=200, value=10, step=1
)
events_per_user = st.sidebar.number_input(
    "Bulk ingest: events/user", min_value=1, max_value=1000, value=20, step=5
)

history_limit = st.sidebar.number_input(
    "History rows", min_value=1, max_value=200, value=20, step=5
)

st.sidebar.divider()
st.sidebar.subheader("Single Event Insert")
single_user_id = st.sidebar.number_input(
    "user_id", min_value=1, max_value=1_000_000, value=3, step=1
)
single_action = st.sidebar.selectbox(
    "action",
    ["login", "browse", "add_to_cart", "purchase", "logout", "cancel", "refund"],
)

# Button row
colA, colB, colC, colD = st.columns(4)

with colA:
    if st.button("🔁 Refresh Metrics"):
        st.rerun()

with colB:
    if st.button("➕ Insert 1 Event"):
        ensure_raw_schema_and_table()
        insert_action(int(single_user_id), str(single_action))
        st.success(f"Inserted: user_id={single_user_id}, action={single_action}")
        st.rerun()

with colC:
    if st.button("📦 Bulk Ingest"):
        ensure_raw_schema_and_table()
        if seed_enabled:
            random.seed(int(seed_value))
        events = generate_events(
            num_users=int(num_users),
            events_per_user=int(events_per_user),
        )
        bulk_insert(events)
        st.success(f"Inserted {len(events)} events into raw.user_actions")
        st.rerun()

with colD:
    if st.button("▶ Run Analysis"):
        # build_report() already persists into analytics.reports
        report_text = build_report()
        parsed = parse_report_text(report_text)
        st.session_state["last_report"] = report_text
        st.session_state["last_score"] = parsed.get("score", "")
        st.session_state["last_label"] = parsed.get("label", "")
        st.success("Analysis completed and stored in analytics.reports.")
        st.rerun()

# Main layout: KPIs + charts
k1, k2, k3 = st.columns(3)

total_events = fetch_total_events()
action_counts = fetch_action_counts()

last_score = st.session_state.get("last_score", "")
last_label = st.session_state.get("last_label", "")

with k1:
    st.metric("Total Events (raw.user_actions)", f"{total_events}")

with k2:
    st.metric("Last Fragility Score", last_score if last_score else "—")

with k3:
    st.metric("Last Classification", last_label if last_label else "—")

st.divider()

left, right = st.columns([1, 1])

with left:
    st.subheader("Per-Action Counts (Bar Chart)")
    if action_counts:
        # Use Streamlit's native bar_chart so we don't rely on static image paths.
        df_counts = pd.DataFrame(action_counts, columns=["action", "count"])
        df_counts = df_counts.set_index("action")
        st.bar_chart(df_counts)
    else:
        st.info("No events found yet. Use Bulk Ingest or Insert 1 Event.")

with right:
    st.subheader("Latest Report (Text)")
    report_text = st.session_state.get("last_report", "")
    if report_text:
        st.text(report_text)
    else:
        st.info("Click **Run Analysis** to generate and display the latest report.")

st.divider()

# ------------------------------------------------------------------
# Stage-5 + Stage-6 + Stage-7:
# History, Export, Trends, Comparison & Detail View
# ------------------------------------------------------------------
st.subheader("History & Trends (analytics.reports)")

# Optional date-range filter
date_range = st.date_input(
    "Filter by created_at date (optional)",
    value=(),
    help="Select a start and end date to filter history. Leave empty to see recent runs.",
)

start_dt = None
end_dt = None
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_dt = datetime.combine(date_range[0], datetime.min.time())
    end_dt = datetime.combine(date_range[1], datetime.max.time())

try:
    rows = get_report_history(
        limit=int(history_limit),
        start=start_dt,
        end=end_dt,
    )
except Exception as e:
    st.error(f"Could not load history from analytics.reports: {e}")
    rows = []

if not rows:
    st.info("No history found yet. Click **Run Analysis** to store a first run.")
else:
    # Normalize rows into a list of dicts, including details
    norm = []
    for r in rows:
        if isinstance(r, dict):
            norm.append(
                {
                    "id": r.get("id"),
                    "created_at": r.get("created_at"),
                    "total_events": r.get("total_events"),
                    "fragility_score": float(r.get("fragility_score"))
                    if r.get("fragility_score") is not None
                    else None,
                    "fragility_label": r.get("fragility_label"),
                    "details": r.get("details"),
                }
            )
        else:
            # Expected tuple: (id, created_at, total_events, fragility_score, fragility_label, details)
            id_, created_at, total_events_, score_, label_, details_ = r
            norm.append(
                {
                    "id": id_,
                    "created_at": created_at,
                    "total_events": total_events_,
                    "fragility_score": float(score_),
                    "fragility_label": label_,
                    "details": details_,
                }
            )

    df_history = pd.DataFrame(norm)

    # Ensure created_at is datetime for sorting & charts
    if "created_at" in df_history.columns:
        df_history["created_at"] = pd.to_datetime(df_history["created_at"])

    df_sorted = df_history.sort_values("created_at")

    # Show a clean table WITHOUT the long details column
    display_cols = ["id", "created_at", "total_events", "fragility_score", "fragility_label"]
    df_display = df_sorted[display_cols]

    st.markdown("**Recent runs**")
    st.dataframe(df_display, use_container_width=True)

    # CSV export (includes details)
    csv_buffer = io.StringIO()
    df_history.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Download full history as CSV",
        data=csv_buffer.getvalue(),
        file_name="decision_fragility_reports_history.csv",
        mime="text/csv",
    )

    # Time-series charts (all runs in range)
    if not df_sorted.empty:
        st.markdown("### Fragility score over time")
        st.line_chart(
            df_sorted.set_index("created_at")[["fragility_score"]]
        )

        st.markdown("### Total events per analysis run")
        st.bar_chart(
            df_sorted.set_index("created_at")[["total_events"]]
        )

    # ------------------------------------------------------------------
    # Stage-7: Multi-Run Comparison
    # ------------------------------------------------------------------
    st.markdown("### Compare runs")

    # Build nice labels for dropdowns, re-used for compare + detail
    option_labels = {
        f"#{int(row.id)} — {row.created_at.strftime('%Y-%m-%d %H:%M:%S')} — {row.fragility_label}": int(row.id)
        for _, row in df_sorted.iterrows()
    }

    compare_selection = st.multiselect(
        "Select two or more runs to compare",
        options=list(option_labels.keys()),
        default=list(option_labels.keys())[:2] if len(option_labels) >= 2 else [],
    )

    if len(compare_selection) >= 2:
        selected_ids_multi = [option_labels[label] for label in compare_selection]
        df_compare = df_sorted[df_sorted["id"].isin(selected_ids_multi)].copy()

        # Stable ordering (by created_at)
        df_compare = df_compare.sort_values("created_at")

        # Human-readable run label
        df_compare["run_label"] = df_compare.apply(
            lambda r: f"#{int(r['id'])} ({r['fragility_label']})",
            axis=1,
        )

        st.markdown("**Comparison table**")
        st.dataframe(
            df_compare[
                ["run_label", "created_at", "total_events", "fragility_score", "fragility_label"]
            ],
            use_container_width=True,
        )

        c_a, c_b = st.columns(2)

        with c_a:
            st.markdown("**Fragility score by run**")
            st.bar_chart(
                df_compare.set_index("run_label")[["fragility_score"]]
            )

        with c_b:
            st.markdown("**Total events by run**")
            st.bar_chart(
                df_compare.set_index("run_label")[["total_events"]]
            )

        st.caption(
            "Use this section to compare baseline vs scenario runs "
            "(e.g., different seeds, user mixes, or experiment conditions)."
        )
    else:
        st.info("Select at least two runs above to see comparison charts.")

    # ------------------------------------------------------------------
    # Stage-6: Run detail (single run)
    # ------------------------------------------------------------------
    st.markdown("### Run detail")

    if option_labels:
        selected_label = st.selectbox(
            "Select a run to inspect",
            options=list(option_labels.keys()),
        )

        if selected_label:
            selected_id = option_labels[selected_label]
            row = df_history[df_history["id"] == selected_id].iloc[0]

            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Run ID", int(row["id"]))
            with c2:
                st.metric("Total events", int(row["total_events"]))
            with c3:
                st.metric("Fragility score", f"{row['fragility_score']:.4f}")

            st.markdown(f"**Classification:** {row['fragility_label']}")
            st.markdown(f"**Created at:** {row['created_at']}")

            st.markdown("**Stored report text**")
            if row.get("details"):
                st.text(row["details"])
            else:
                st.info("No stored details text for this run.")
    else:
        st.info("No runs available for detailed view yet.")

# ----------------------------------------------------------------------
# Stage-8 + Stage-9: Behavioral transitions & Sequence Explorer
# ----------------------------------------------------------------------
st.divider()
st.subheader("Behavioral transitions (experimental)")

transitions = fetch_action_transitions(limit=50)

if not transitions:
    st.info(
        "Not enough data to compute transitions yet. "
        "Try running Bulk Ingest and Run Analysis first."
    )
else:
    df_trans = pd.DataFrame(
        transitions, columns=["from_action", "to_action", "count"]
    )

    st.markdown("**Top action-to-action transitions**")
    st.dataframe(df_trans, use_container_width=True)

    # Build a transition matrix (from_action as rows, to_action as columns)
    pivot = (
        df_trans.pivot(index="from_action", columns="to_action", values="count")
        .fillna(0)
        .astype(int)
    )

    st.markdown("**Transition matrix (heatmap)**")

    fig = plt.figure()
    plt.imshow(pivot.values, aspect="auto")
    plt.colorbar(label="Transition count")
    plt.xticks(
        range(len(pivot.columns)),
        pivot.columns,
        rotation=45,
        ha="right",
    )
    plt.yticks(range(len(pivot.index)), pivot.index)
    plt.tight_layout()
    st.pyplot(fig)

    st.caption(
        "This matrix shows how often each action is immediately followed by another. "
        "Use it to spot loops, dead ends, and high-fragility paths."
    )

    # --------------------------------------------------------------
    # Stage-9: Sequence explorer for a selected transition
    # --------------------------------------------------------------
    st.markdown("### Sequence explorer for selected transition")

    # Create human-friendly labels like "browse → login (19)"
    option_map: Dict[str, Tuple[str, str]] = {}
    for _, row in df_trans.iterrows():
        label = f"{row['from_action']} → {row['to_action']} ({row['count']})"
        option_map[label] = (str(row["from_action"]), str(row["to_action"]))

    if option_map:
        selected_transition_label = st.selectbox(
            "Pick a transition to inspect user journeys",
            options=list(option_map.keys()),
        )

        if selected_transition_label:
            from_action, to_action = option_map[selected_transition_label]

            sequences = fetch_transition_sequences(
                from_action=from_action,
                to_action=to_action,
                max_examples=20,
                window_before=2,
                window_after=2,
            )

            if not sequences:
                st.info(
                    "No concrete sequences found for this transition. "
                    "This can happen if the underlying data changed since the "
                    "transition table was computed."
                )
            else:
                df_seq = pd.DataFrame(sequences)
                st.markdown(
                    f"Showing up to {len(df_seq)} example sequences where "
                    f"`{from_action} → {to_action}` occurs."
                )
                st.dataframe(
                    df_seq[["example_index", "user_id", "sequence"]],
                    use_container_width=True,
                )

                st.caption(
                    "Each row is a short window of actions around the selected "
                    "transition for a specific user_id."
                )
    else:
        st.info("No transitions available yet for sequence exploration.")

st.caption(
    "Dashboard UI: deterministic bulk ingest uses a fixed random seed when enabled. "
    "History section lets you export runs, track trends, compare scenarios, inspect any past report, "
    "and analyze behavioral transitions and concrete user journeys between actions."
)
