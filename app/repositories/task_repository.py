from contextlib import contextmanager
from typing import Optional
import logging

from app.config.database import Database, database
from app.metrics import DB_QUERY_LATENCY_SECONDS
from app.observability import trace_db_operation


logger = logging.getLogger(__name__)


class TaskRepository:

    def __init__(self, db: Database) -> None:
        self.db = db

    @contextmanager
    def _query(self, operation: str, write: bool):
        """
        로그 / trace / latency metric / 연결 선택을 한곳에 모은다.
        write=True는 Primary로 가고 성공 시 commit, write=False는 Replica 읽기 전용.
        """
        role, target = ("write", "primary") if write else ("read", "replica")
        logger.info("event=db_query target=%s operation=%s", target, operation)

        with trace_db_operation(operation, role, target), DB_QUERY_LATENCY_SECONDS.labels(
            operation=operation,
            target=target,
        ).time():
            connect = (
                self.db.get_write_db_connection if write else self.db.get_read_db_connection
            )
            with connect() as conn:
                with conn.cursor() as cur:
                    yield cur

                if write:
                    conn.commit()

    def create_task(self, title: str) -> dict:
        with self._query("create_task", write=True) as cur:
            cur.execute(
                """
                INSERT INTO tasks (title)
                VALUES (%s)
                RETURNING id, title, done;
                """,
                (title,),
            )
            row = cur.fetchone()

        return self._row_to_task(row)

    def list_tasks(self) -> list[dict]:
        with self._query("list_tasks", write=False) as cur:
            cur.execute(
                """
                SELECT id, title, done
                FROM tasks
                ORDER BY id;
                """
            )
            rows = cur.fetchall()

        return [self._row_to_task(row) for row in rows]

    def get_task_by_id(self, task_id: int) -> Optional[dict]:
        with self._query("get_task_by_id", write=False) as cur:
            cur.execute(
                """
                SELECT id, title, done
                FROM tasks
                WHERE id = %s;
                """,
                (task_id,),
            )
            row = cur.fetchone()

        return None if row is None else self._row_to_task(row)

    def update_task(
        self,
        task_id: int,
        title: str | None = None,
        done: bool | None = None,
    ) -> Optional[dict]:
        with self._query("update_task", write=True) as cur:
            cur.execute(
                """
                UPDATE tasks
                SET title = COALESCE(%s, title),
                    done = COALESCE(%s, done)
                WHERE id = %s
                RETURNING id, title, done;
                """,
                (title, done, task_id),
            )
            row = cur.fetchone()

        return None if row is None else self._row_to_task(row)

    def delete_task(self, task_id: int) -> bool:
        with self._query("delete_task", write=True) as cur:
            cur.execute(
                """
                DELETE FROM tasks
                WHERE id = %s
                RETURNING id;
                """,
                (task_id,),
            )
            row = cur.fetchone()

        return row is not None

    @staticmethod
    def _row_to_task(row) -> dict:
        return {
            "id": row[0],
            "title": row[1],
            "done": row[2],
        }


task_repository = TaskRepository(database)
