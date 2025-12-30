# app/services/bulk_ingest.py

import random
from app.models.db import get_db_connection

ACTIONS = [
    "login",
    "browse",
    "add_to_cart",
    "purchase",
    "logout",
    "cancel",
    "refund",
]


def ensure_raw_schema_and_table():
    """
    Ensure raw schema + user_actions table exist before insertion.
    Safe to call repeatedly.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Create schema if needed
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    # Create table if needed
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS raw.user_actions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        """
    )

    conn.commit()
    cur.close()
    conn.close()


def generate_events(num_users: int = 10, events_per_user: int = 20):
    """
    Create a simple synthetic stream of user actions.
    """
    events = []

    # Slight bias toward less extreme actions
    weights = [25, 25, 15, 10, 10, 8, 7]  # same length as ACTIONS

    for user_id in range(1, num_users + 1):
        for _ in range(events_per_user):
            action = random.choices(ACTIONS, weights=weights, k=1)[0]
            events.append((user_id, action))

    return events


def bulk_insert(events):
    """
    Insert many rows efficiently.
    """
    ensure_raw_schema_and_table()

    conn = get_db_connection()
    cur = conn.cursor()

    cur.executemany(
        "INSERT INTO raw.user_actions (user_id, action) VALUES (%s, %s)",
        events,
    )

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    events = generate_events(num_users=10, events_per_user=20)
    bulk_insert(events)
    print(f"Inserted {len(events)} synthetic events into raw.user_actions")
