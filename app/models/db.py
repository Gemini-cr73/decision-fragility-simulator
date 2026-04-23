# app/models/db.py

import os

import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    """
    Return a PostgreSQL connection using Railway's DATABASE_URL.
    Falls back to local DATABASE_URL if running outside Railway.
    """
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    return psycopg2.connect(
        database_url,
        cursor_factory=RealDictCursor,
    )
