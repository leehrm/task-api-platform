from contextlib import contextmanager

from app.repositories.task_repository import TaskRepository


class _FakeCursor:
    def __init__(self) -> None:
        self.executed: list[tuple] = []
        self.fetchone_results: list[tuple | None] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return (1, "title", False)

    def fetchall(self):
        return [(1, "title", False)]


class _FakeConnection:
    def __init__(self) -> None:
        self.cursor_ = _FakeCursor()
        self.commits = 0

    def cursor(self):
        return self.cursor_

    def commit(self):
        self.commits += 1


class _FakeDatabase:
    def __init__(self) -> None:
        self.primary = _FakeConnection()
        self.replica = _FakeConnection()

    @contextmanager
    def get_write_db_connection(self):
        yield self.primary

    @contextmanager
    def get_read_db_connection(self):
        yield self.replica


def _repo():
    db = _FakeDatabase()
    return TaskRepository(db), db


def test_writes_use_primary_and_commit():
    for call in (
        lambda r: r.create_task("x"),
        lambda r: r.update_task(1, title="x"),
        lambda r: r.delete_task(1),
    ):
        repo, db = _repo()
        call(repo)

        assert db.primary.cursor_.executed, "primary에 쿼리가 가지 않았다"
        assert db.primary.commits == 1
        assert not db.replica.cursor_.executed


def test_reads_use_replica_and_never_commit():
    for call in (
        lambda r: r.list_tasks(),
        lambda r: r.get_task_by_id(1),
    ):
        repo, db = _repo()
        call(repo)

        assert db.replica.cursor_.executed, "replica에 쿼리가 가지 않았다"
        assert db.replica.commits == 0
        assert not db.primary.cursor_.executed


def test_update_reports_only_new_completion():
    for previous_done, expected in ((False, True), (True, False)):
        repo, db = _repo()
        db.primary.cursor_.fetchone_results = [
            (previous_done,),
            (1, "title", True),
        ]

        _, became_done = repo.update_task(1, done=True)

        assert became_done is expected


def test_failed_write_does_not_commit():
    repo, db = _repo()
    db.primary.cursor_.execute = _raise

    raised = False
    try:
        repo.create_task("x")
    except RuntimeError:
        raised = True

    assert raised, "쿼리 실패가 호출자에게 전파되지 않았다"
    assert db.primary.commits == 0


def _raise(*args, **kwargs):
    raise RuntimeError("query failed")
