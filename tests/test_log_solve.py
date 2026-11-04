"""Unit tests for LogSolve Lambda handler using moto."""

import json
import boto3
from moto import mock_aws
import pytest

from src.log_solve import app as log_solve_app
from src.common.streak import get_ist_date_str, get_previous_date_str

TABLE_NAME = "streaknudge-test"
VALID_API_KEY = "streaknudge-secret-key-12345"


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Set environment variables for tests."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("TABLE_NAME", TABLE_NAME)
    monkeypatch.setenv("API_KEY", VALID_API_KEY)
    log_solve_app._dynamodb_resource = None


@pytest.fixture
def dynamodb_table():
    """Create mocked DynamoDB table."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
        table = dynamodb.create_table(
            TableName=TABLE_NAME,
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
        log_solve_app._dynamodb_resource = dynamodb
        yield table


def test_missing_api_key(dynamodb_table):
    """Requests without x-api-key must be rejected with 401 Unauthorized."""
    event = {
        "headers": {},
        "body": json.dumps({"user": "alice", "problem": "Two Sum", "difficulty": "Easy"}),
    }
    response = log_solve_app.lambda_handler(event, None)
    assert response["statusCode"] == 401
    body = json.loads(response["body"])
    assert "Unauthorized" in body["error"]


def test_invalid_api_key(dynamodb_table):
    """Requests with wrong x-api-key must be rejected with 401 Unauthorized."""
    event = {
        "headers": {"x-api-key": "wrong-key"},
        "body": json.dumps({"user": "alice", "problem": "Two Sum", "difficulty": "Easy"}),
    }
    response = log_solve_app.lambda_handler(event, None)
    assert response["statusCode"] == 401


def test_missing_body(dynamodb_table):
    """Empty body returns 400 Bad Request."""
    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "body": "",
    }
    response = log_solve_app.lambda_handler(event, None)
    assert response["statusCode"] == 400


def test_malformed_json(dynamodb_table):
    """Invalid JSON syntax returns 400 Bad Request."""
    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "body": "{invalid-json",
    }
    response = log_solve_app.lambda_handler(event, None)
    assert response["statusCode"] == 400


def test_invalid_payload_fields(dynamodb_table):
    """Validates missing required fields or invalid difficulty."""
    # Invalid difficulty
    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "body": json.dumps({"user": "alice", "problem": "Two Sum", "difficulty": "Extreme"}),
    }
    response = log_solve_app.lambda_handler(event, None)
    assert response["statusCode"] == 400
    assert "difficulty" in json.loads(response["body"])["error"]

    # Invalid user name
    event["body"] = json.dumps({"user": "bad user name!", "problem": "Two Sum", "difficulty": "Easy"})
    response = log_solve_app.lambda_handler(event, None)
    assert response["statusCode"] == 400


def test_first_ever_solve_success(dynamodb_table):
    """First-ever solve should return 201 Created and streak_count = 1."""
    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "body": json.dumps({
            "user": "alice",
            "problem": "Two Sum",
            "difficulty": "Easy",
            "email": "alice@example.com",
        }),
    }
    response = log_solve_app.lambda_handler(event, None)
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["streak_count"] == 1
    assert body["user"] == "alice"
    assert body["is_same_day_repeat"] is False

    # Verify item in DynamoDB
    today_ist = get_ist_date_str()
    item = dynamodb_table.get_item(Key={"PK": "alice", "SK": today_ist})["Item"]
    assert item["problem"] == "Two Sum"
    assert item["streak_count"] == 1

    # Verify profile was also written
    profile = dynamodb_table.get_item(Key={"PK": "alice", "SK": "PROFILE"})["Item"]
    assert profile["email"] == "alice@example.com"


def test_consecutive_day_solve_increments_streak(dynamodb_table):
    """If yesterday had streak 3, today's solve must increment streak to 4."""
    today_ist = get_ist_date_str()
    yesterday_ist = get_previous_date_str(today_ist)

    # Seed yesterday's record
    dynamodb_table.put_item(
        Item={
            "PK": "bob",
            "SK": yesterday_ist,
            "problem": "Subarray Sum Equals K",
            "difficulty": "Medium",
            "streak_count": 3,
        }
    )

    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "body": json.dumps({"user": "bob", "problem": "3Sum", "difficulty": "Medium"}),
    }
    response = log_solve_app.lambda_handler(event, None)
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["streak_count"] == 4
    assert body["is_same_day_repeat"] is False


def test_same_day_repeat_solve_idempotent(dynamodb_table):
    """Logging another solve on the same day must not increment streak."""
    today_ist = get_ist_date_str()

    # Seed today's first solve with streak 5
    dynamodb_table.put_item(
        Item={
            "PK": "carol",
            "SK": today_ist,
            "problem": "Invert Binary Tree",
            "difficulty": "Easy",
            "streak_count": 5,
        }
    )

    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "body": json.dumps({"user": "carol", "problem": "Binary Tree Level Order Traversal", "difficulty": "Medium"}),
    }
    response = log_solve_app.lambda_handler(event, None)
    assert response["statusCode"] == 201
    body = json.loads(response["body"])
    assert body["streak_count"] == 5
    assert body["is_same_day_repeat"] is True
