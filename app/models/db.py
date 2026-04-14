# app/models/db.py

import os
from urllib.parse import urlparse, parse_qs

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load .env from the project root
load_dotenv()


def get_db_connection():
    """
    Return a PostgreSQL connection using the Neon connection string
    stored in NEON_PG_URL.
    """
    url = os.getenv("NEON_PG_URL")
    if not url:
        raise RuntimeError("NEON_PG_URL is not set in your .env file")

    parsed = urlparse(url)

    host = parsed.hostname
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/")  # "/neondb" -> "neondb"
    user = parsed.username
    password = parsed.password

    # Read sslmode from query string (?sslmode=require&...)
    qs = parse_qs(parsed.query)
    sslmode = qs.get("sslmode", ["require"])[0]

    # Helpful error if something is missing
    if not all([host, dbname, user, password]):
        raise RuntimeError(
            "Incomplete DB settings parsed from NEON_PG_URL:\n"
            f"  host={host}\n"
            f"  dbname={dbname}\n"
            f"  user={user}\n"
            f"  password={'SET' if password else 'MISSING'}"
        )

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode=sslmode,
        cursor_factory=RealDictCursor,
    )

