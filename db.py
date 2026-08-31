import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """
    Shared MySQL connection helper.

    This is imported by both assignmentendpoints.py and statusendpoints.py.
    It didn't exist yet on the Backend branch (Nathalie's file references it
    but never committed it), so both blueprints were relying on a module
    that would fail on import.

    Env vars match Victor's config.py naming so the two branches can be
    reconciled later without renaming anything.
    """
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "reflex_db"),
        port=int(os.getenv("DB_PORT", "3306")),
    )
