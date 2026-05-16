import os
from contextlib import contextmanager

import psycopg2


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "taskdb"),
        user=os.getenv("DB_USER", "taskuser"),
        password=os.getenv("DB_PASSWORD", "taskpass"),
        connect_timeout=3,
    )


@contextmanager
def get_db_connection():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def check_database_connection():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
            cur.fetchone()


def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                );
                """
            )
        conn.commit()