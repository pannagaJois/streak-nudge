"""Integration tests verifying frontend and local dev server compatibility."""

import json
from http.server import HTTPServer
import threading
import urllib.request
import urllib.error
import pytest

from scripts.dev_server import StreakDevHandler, init_local_db


@pytest.fixture(scope="module")
def local_server():
    """Start local test server on an ephemeral port."""
    init_local_db()
    server = HTTPServer(("127.0.0.1", 0), StreakDevHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    import scripts.dev_server as ds
    if ds._mock_instance:
        ds._mock_instance.stop()
        ds._mock_instance = None


def test_frontend_static_files_served(local_server):
    """Verify that frontend static files are accessible via HTTP."""
    # Test index redirect
    req = urllib.request.Request(f"{local_server}/frontend/api.js")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "StreakApi" in content

    # Test home page
    req = urllib.request.Request(f"{local_server}/frontend/streaknudge_home/code.html")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "StreakNudge" in content


def test_local_api_streak_flow(local_server):
    """Verify end-to-end API communication through the server."""
    api_key = "streaknudge-secret-key-12345"

    # 1. Log solve
    payload = json.dumps({
        "user": "frontend_tester",
        "problem": "Invert Binary Tree",
        "difficulty": "Easy",
        "email": "test@example.com",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{local_server}/solves",
        data=payload,
        headers={"Content-Type": "application/json", "x-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        data = json.loads(resp.read().decode("utf-8"))
        assert data["streak_count"] == 1
        assert data["problem"] == "Invert Binary Tree"

    # 2. Get streak
    req2 = urllib.request.Request(
        f"{local_server}/streak/frontend_tester",
        headers={"x-api-key": api_key},
        method="GET",
    )
    with urllib.request.urlopen(req2) as resp2:
        assert resp2.status == 200
        data2 = json.loads(resp2.read().decode("utf-8"))
        assert data2["streak_count"] == 1
        assert data2["status"] == "ACTIVE_TODAY"
