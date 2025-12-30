# app/models/db.py

import os

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load variables from the .env file if present
load_dotenv()


def get_db_connection():
    """
    Return a PostgreSQL connection.

    Uses environment variables when available, otherwise defaults to a local
    PostgreSQL instance on database 'ai_projects'.
    """
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "NewStrongPassword123!"),
        dbname=os.getenv("POSTGRES_DB", "ai_projects"),
        cursor_factory=RealDictCursor,
    )
