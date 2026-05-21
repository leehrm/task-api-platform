import os
from contextlib import contextmanager
from typing import Generator

import psycopg2
from psycopg2.extensions import connection as PsycopgConnection


class Database:

    def get_connection(self) -> PsycopgConnection:
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            port=os.getenv("DB_PORT", "5432"),
            dbname=os.getenv("DB_NAME", "taskdb"),
            user=os.getenv("DB_USER", "taskuser"),
            password=os.getenv("DB_PASSWORD", "taskpass"),
            connect_timeout=3,
        )

    @contextmanager
    def get_db_connection(self) -> Generator[PsycopgConnection, None, None]:
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    def check_connection(self) -> None:
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()

    def init_db(self) -> None:
        with self.get_db_connection() as conn:
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

# database object
database = Database()