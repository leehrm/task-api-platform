from typing import Optional

from app.config.database import Database, database


class TaskRepository:

    def __init__(self, db: Database) -> None:
        self.db = db

    def create_task(self, title: str) -> dict:
        print("event=db_query target=primary operation=create_task", flush=True)

        with self.db.get_write_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tasks (title)
                    VALUES (%s)
                    RETURNING id, title, done;
                    """,
                    (title,),
                )
                row = cur.fetchone()
            conn.commit()

        return self._row_to_task(row)

    def list_tasks(self) -> list[dict]:
        print("event=db_query target=replica operation=list_tasks", flush=True)

        with self.db.get_read_db_connection() as conn:
            with conn.cursor() as cur:
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
        print(
            f"event=db_query target=replica operation=get_task_by_id task_id={task_id}",
            flush=True,
        )

        with self.db.get_read_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, done
                    FROM tasks
                    WHERE id = %s;
                    """,
                    (task_id,),
                )
                row = cur.fetchone()

        if row is None:
            return None

        return self._row_to_task(row)

    def update_task(
        self,
        task_id: int,
        title: str | None = None,
        done: bool | None = None,
    ) -> Optional[dict]:
        print(
            f"event=db_query target=primary operation=update_task task_id={task_id}",
            flush=True,
        )

        with self.db.get_write_db_connection() as conn:
            with conn.cursor() as cur:
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
            conn.commit()

        if row is None:
            return None

        return self._row_to_task(row)

    def delete_task(self, task_id: int) -> bool:
        print(
            f"event=db_query target=primary operation=delete_task task_id={task_id}",
            flush=True,
        )

        with self.db.get_write_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM tasks
                    WHERE id = %s
                    RETURNING id;
                    """,
                    (task_id,),
                )
                row = cur.fetchone()
            conn.commit()

        return row is not None

    @staticmethod
    def _row_to_task(row) -> dict:
        return {
            "id": row[0],
            "title": row[1],
            "done": row[2],
        }


task_repository = TaskRepository(database)
