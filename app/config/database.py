import os
import logging
from contextlib import contextmanager
from typing import Generator, Literal

import psycopg2
from opentelemetry.instrumentation.utils import suppress_instrumentation
from psycopg2.extensions import connection as PsycopgConnection


DatabaseTarget = Literal["primary", "replica"]
logger = logging.getLogger(__name__)


class Database:

    def _get_common_connection_kwargs(self) -> dict:
        pod_name = os.getenv("POD_NAME") or os.getenv("HOSTNAME") or "unknown"
        application_name = (
            os.getenv("DB_APPLICATION_NAME")
            or f"task-api:{pod_name}"
        )

        return {
            "port": os.getenv("DB_PORT", "5432"),
            "dbname": os.getenv("DB_NAME", "taskdb"),
            "user": os.getenv("DB_USER", "taskuser"),
            "password": os.getenv("DB_PASSWORD", "taskpass"),
            "application_name": application_name,
            "connect_timeout": 3,
        }

    def get_write_connection(self) -> PsycopgConnection:
        """
        Write 전용 연결.
        POST/PATCH/DELETE/init_db는 반드시 Primary를 사용.
        """
        host = (
            os.getenv("DB_PRIMARY_HOST")
            or os.getenv("DB_HOST")
            or "db"
        )

        return psycopg2.connect(
            host=host,
            **self._get_common_connection_kwargs(),
        )

    def get_read_connection(self) -> PsycopgConnection:
        """
        Read 전용 연결.
        DB_READ_HOST가 있으면 Read Replica를 사용하고,
        없으면 Primary/DB_HOST로 fallback.
        """
        host = (
            os.getenv("DB_READ_HOST")
            or os.getenv("DB_PRIMARY_HOST")
            or os.getenv("DB_HOST")
            or "db"
        )

        return psycopg2.connect(
            host=host,
            **self._get_common_connection_kwargs(),
        )

    @contextmanager
    def get_write_db_connection(self) -> Generator[PsycopgConnection, None, None]:
        conn = self.get_write_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def get_read_db_connection(self) -> Generator[PsycopgConnection, None, None]:
        conn = self.get_read_connection()
        try:
            yield conn
        finally:
            conn.close()

    def check_connection(self) -> None:
        """
        readiness check는 기본적으로 Primary 연결을 확인.
        """
        with suppress_instrumentation():
            with self.get_write_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    cur.fetchone()

    def init_db(self) -> None:
        """
        테이블 생성은 write 작업이므로 반드시 Primary에서 실행.
        """
        logger.info("event=db_query target=primary operation=init_db")

        with self.get_write_db_connection() as conn:
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

    def shutdown(self) -> None:
        """
        현재 구현은 요청마다 DB connection을 열고 context manager에서 닫음.
        별도 pool은 없지만 shutdown 시점 관측을 위해 로그를 남김.
        """
        logger.info("event=db_shutdown connection_model=per_request")


database = Database()
