# app/analytics/report.py

from typing import List, Tuple, Optional
from datetime import datetime

from app.models.db import get_db_connection
from app.analytics.fragility import compute_fragility


def ensure_analytics_schema() -> None:
    """
    Ensure the analytics schema and reports table exist.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("CREATE SCHEMA IF NOT EXISTS analytics;")

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS analytics.reports (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            total_events INTEGER NOT NULL,
            fragility_score NUMERIC(5,4) NOT NULL,
            fragility_label TEXT NOT NULL,
            details TEXT NOT NULL
        );
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def get_action_counts() -> List[Tuple[str, int]]:
    """
    Returns aggregated counts grouped by action.
    May return tuples or dicts, depending on cursor configuration.
    """
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
    return rows


def classify_fragility(score: Optional[float]) -> str:
    """
    Map a numeric fragility score into a qualitative label.

    score may be None when there is no data yet.
    """
    if score is None:
        return "NO DATA"

    if score < 0.20:
        return "LOW"
    elif score < 0.50:
        return "MEDIUM"
    else:
        return "HIGH"


def save_report_to_history(
    total_events: int,
    score: Optional[float],
    label: str,
    details: str,
) -> None:
    """
    Persist a stored report entry into analytics.reports.

    The database column fragility_score is NOT NULL, so if score is None
    we store 0.0 but keep the label as "NO DATA" in case of empty data.
    """
    ensure_analytics_schema()

    # Ensure we always have a numeric value for the DB insert
    score_to_store: float = float(score) if score is not None else 0.0

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO analytics.reports
            (total_events, fragility_score, fragility_label, details)
        VALUES (%s, %s, %s, %s);
        """,
        (total_events, score_to_store, label, details),
    )

    conn.commit()
    cur.close()
    conn.close()


def get_report_history(
    limit: int = 200,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[tuple]:
    """
    Return historical report runs from analytics.reports.

    Each row is:
        (id, created_at, total_events, fragility_score, fragility_label, details)

    Optional start/end allow date-range filtering.
    """
    ensure_analytics_schema()

    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT id,
               created_at,
               total_events,
               fragility_score,
               fragility_label,
               details
        FROM analytics.reports
        WHERE (%(start)s IS NULL OR created_at >= %(start)s)
          AND (%(end)s   IS NULL OR created_at <= %(end)s)
        ORDER BY created_at DESC
        LIMIT %(limit)s;
    """

    cur.execute(
        query,
        {
            "start": start,
            "end": end,
            "limit": limit,
        },
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def list_report_history(limit: int = 20) -> List[tuple]:
    """
    Backwards-compatible wrapper around get_report_history.
    """
    return get_report_history(limit=limit)


def build_report() -> str:
    """
    Sequential supervisor:
    - Count actions
    - Score fragility
    - Classify
    - Build text
    - Store report
    - Return for CLI / calling code
    """
    action_rows = get_action_counts()

    # Safest possible total_events calculation
    total_events = 0
    for row in action_rows:
        try:
            # Row might be tuple or dict
            if isinstance(row, dict):
                count = row.get("count", 0)
            else:
                # assume (action, count)
                _, count = row

            total_events += int(count)
        except Exception:
            # Ignore malformed rows rather than crashing
            pass

    # Use current compute_fragility() implementation (no args)
    score: Optional[float] = compute_fragility()
    label = classify_fragility(score)

    # Build text output
    lines: List[str] = []
    lines.append("=== Decision Fragility Report ===")
    lines.append("")
    lines.append(f"Total events observed : {total_events}")

    # Score display that is robust to None
    if score is None:
        lines.append("Fragility score       : N/A (no events to analyze)")
    else:
        lines.append(f"Fragility score       : {score:.4f}")

    lines.append(f"Classification        : {label}")
    lines.append("")
    lines.append("Per-action event counts:")

    if not action_rows:
        lines.append("  (no events found in raw.user_actions)")
    else:
        for row in action_rows:
            try:
                if isinstance(row, dict):
                    action = row.get("action", "?")
                    count = row.get("count", "?")
                else:
                    action, count = row
                lines.append(f"  - {action}: {count}")
            except Exception:
                # Skip any bad row rather than failing the whole report
                pass

    lines.append("")
    lines.append("Interpretation:")

    if label == "NO DATA":
        lines.append(
            "  Not enough events yet to compute a fragility score. "
            "Ingest more user actions and re-run the analysis."
        )
    elif label == "LOW":
        lines.append("  Stable behavior — minimal switching/undo patterns.")
    elif label == "MEDIUM":
        lines.append("  Moderate switching — some backtracking and revision.")
    else:
        lines.append("  Frequent switching — high fragility and instability.")

    report_text = "\n".join(lines)

    # Persist record into analytics.reports
    save_report_to_history(total_events, score, label, report_text)

    return report_text
