from app.models.db import get_db_connection


def compute_fragility() -> float | None:
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE action IN ('purchase', 'logout'))::float
            / NULLIF(COUNT(*), 0)::float AS fragility_score
        FROM raw.user_actions;
        """
    )

    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return None

    # Handle both dict-style and tuple-style rows safely
    if isinstance(row, dict):
        score = row.get("fragility_score")
    else:
        # fall back to positional column 0
        score = row[0]

    return score


if __name__ == "__main__":
    score = compute_fragility()
    print("Fragility Score:", score)
