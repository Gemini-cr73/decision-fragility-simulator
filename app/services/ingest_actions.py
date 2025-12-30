from app.models.db import get_db_connection


def ensure_raw_schema_and_table():
    """
    Creates the raw schema and user_actions table if they do not already exist.
    Safe to call before any insert.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # Create schema if missing
    cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    # Create table if missing
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


def insert_action(user_id, action):
    """
    Inserts one (user_id, action) record into raw.user_actions.
    Runs schema/table creation check first.
    """
    ensure_raw_schema_and_table()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO raw.user_actions (user_id, action)
        VALUES (%s, %s);
        """,
        (user_id, action)
    )

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    # simple test insert
    insert_action(3, "logout")
    print("Inserted test record into raw.user_actions!")
