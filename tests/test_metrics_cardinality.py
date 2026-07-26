from fastapi.testclient import TestClient

from app.main import app
from app.metrics import HTTP_REQUEST_TOTAL


def _recorded_paths() -> set[str]:
    return {
        sample.labels["path"]
        for metric in HTTP_REQUEST_TOTAL.collect()
        for sample in metric.samples
    }


def test_unmatched_requests_share_a_single_label():
    client = TestClient(app)
    scanned = ("/admin.php", "/.env", "/wp-login.php")

    for path in scanned:
        assert client.get(path).status_code == 404

    paths = _recorded_paths()
    assert "unmatched" in paths
    assert not paths & set(scanned)


def test_matched_requests_keep_their_route_template():
    client = TestClient(app)
    client.get("/healthz")

    assert "/healthz" in _recorded_paths()
