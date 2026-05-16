from app.config.database import get_db_connection

def create_task(title: str):
    with get_db_connection() as conn:
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

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2],
    }

def list_tasks():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, done
                FROM tasks
                ORDER BY id;
                """
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "title": row[1],
            "done": row[2],
        }
        for row in rows
    ]

def get_task_by_id(task_id: int):
    with get_db_connection() as conn:
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

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2],
    }


def update_task(task_id: int, title=None, done=None):
    current_task = get_task_by_id(task_id)

    if current_task is None:
        return None

    new_title = title if title is not None else current_task["title"]
    new_done = done if done is not None else current_task["done"]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tasks
                SET title = %s,
                    done = %s
                WHERE id = %s
                RETURNING id, title, done;
                """,
                (new_title, new_done, task_id),
            )
            row = cur.fetchone()
        conn.commit()

    return {
        "id": row[0],
        "title": row[1],
        "done": row[2],
    }


def delete_task(task_id: int):
    with get_db_connection() as conn:
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