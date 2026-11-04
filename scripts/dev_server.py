#!/usr/bin/env python3
"""StreakNudge Local Full-Stack Development Server.

Combines:
1. Static web server for the frontend directory.
2. Serverless API emulation routing POST /solves and GET /streak/{user}
   directly to LogSolve and GetStreak Lambda handlers.
3. In-memory DynamoDB mock (via moto) when running offline, ensuring
   zero AWS credentials or cloud setup is needed for local development.

Usage:
  python3 scripts/dev_server.py [PORT]
"""

import json
import mimetypes
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

# Set default local test environment
os.environ.setdefault("TABLE_NAME", "streaknudge-local-dev")
os.environ.setdefault("API_KEY", "streaknudge-secret-key-12345")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-south-1")
os.environ.setdefault("AWS_REGION", "ap-south-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from moto import mock_aws
import boto3

from src.log_solve.app import lambda_handler as log_solve_handler
from src.get_streak.app import lambda_handler as get_streak_handler

_mock_instance = None


def init_local_db():
    """Start in-memory AWS mock and create DynamoDB table for local development."""
    global _mock_instance
    if _mock_instance is None:
        _mock_instance = mock_aws()
        _mock_instance.start()

    dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
    table_name = os.environ.get("TABLE_NAME", "streaknudge-local-dev")
    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        print(f"[*] Initialized in-memory DynamoDB table '{table_name}'")
    except Exception:
        pass


class StreakDevHandler(BaseHTTPRequestHandler):
    """Handles both static files and API Gateway Lambda proxy routes."""

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, x-api-key, X-Api-Key")

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        """Route POST requests (e.g. /solves)."""
        parsed = urlparse(self.path)

        if parsed.path.rstrip("/") == "/solves":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

            # Construct API Gateway v2 event
            event = {
                "requestContext": {
                    "http": {
                        "method": "POST",
                        "path": "/solves",
                    }
                },
                "headers": {k.lower(): v for k, v in self.headers.items()},
                "body": body,
            }

            res = log_solve_handler(event, None)
            self._send_lambda_response(res)
        else:
            self.send_error(404, "Endpoint not found")

    def do_HEAD(self):
        """Handle HEAD requests."""
        self.do_GET(head_only=True)

    def do_GET(self, head_only=False):
        """Route GET requests (e.g. /streak/{user} or static frontend files)."""
        parsed = urlparse(self.path)
        path = parsed.path

        # 1. API Route: GET /streak/{user}
        if path.startswith("/streak/"):
            user = unquote(path[len("/streak/"):].strip("/"))
            event = {
                "requestContext": {
                    "http": {
                        "method": "GET",
                        "path": path,
                    }
                },
                "headers": {k.lower(): v for k, v in self.headers.items()},
                "pathParameters": {"user": user},
            }

            res = get_streak_handler(event, None)
            self._send_lambda_response(res, head_only=head_only)
            return

        # 2. Static Frontend Files
        # Default root '/' redirects to '/frontend/streaknudge_home/code.html'
        if path in ("/", "/frontend", "/frontend/"):
            self.send_response(302)
            self.send_header("Location", "/frontend/streaknudge_home/code.html")
            self.end_headers()
            return

        # Serve requested file from project root
        file_path = os.path.normpath(os.path.join(ROOT_DIR, path.lstrip("/")))
        if not file_path.startswith(ROOT_DIR):
            self.send_error(403, "Forbidden")
            return

        if os.path.isdir(file_path):
            file_path = os.path.join(file_path, "code.html")

        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_response(200)
            mime_type, _ = mimetypes.guess_type(file_path)
            self.send_header("Content-Type", mime_type or "text/html")
            self._send_cors_headers()
            self.end_headers()

            if not head_only:
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
        else:
            self.send_error(404, f"File not found: {path}")

    def _send_lambda_response(self, res, head_only=False):
        """Translate Lambda handler response to HTTP response."""
        status_code = res.get("statusCode", 200)
        self.send_response(status_code)
        self._send_cors_headers()

        headers = res.get("headers", {})
        for k, v in headers.items():
            if not k.lower().startswith("access-control-"):
                self.send_header(k, v)
        self.end_headers()

        if not head_only:
            body = res.get("body", "")
            if isinstance(body, str):
                self.wfile.write(body.encode("utf-8"))
            elif isinstance(body, bytes):
                self.wfile.write(body)

    def log_message(self, format, *args):
        """Custom logger."""
        sys.stderr.write(f"[StreakDevServer] {args[0]} {args[1]} -> {args[2]}\n")


def run(port=3000):
    init_local_db()
    server = HTTPServer(("0.0.0.0", port), StreakDevHandler)
    print(f"\n{'='*60}")
    print(f" StreakNudge Full-Stack Local Server running!")
    print(f"{'='*60}")
    print(f" ▶ Dashboard UI : http://localhost:{port}/frontend/streaknudge_home/code.html")
    print(f" ▶ Log Solve UI : http://localhost:{port}/frontend/streaknudge_log_a_solve/code.html")
    print(f" ▶ History UI   : http://localhost:{port}/frontend/streaknudge_history/code.html")
    print(f" ▶ API Route    : POST http://localhost:{port}/solves")
    print(f" ▶ API Route    : GET  http://localhost:{port}/streak/{{user}}")
    print(f" ▶ API Key      : streaknudge-secret-key-12345")
    print(f"{'='*60}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping StreakNudge local server...")
        mock.stop()
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    run(port)
