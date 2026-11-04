"""Unit tests for GetStreak Lambda handler using moto."""

import json
import boto3
from moto import mock_aws
import pytest

from src.get_streak import app as get_streak_app
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
    get_streak_app._dynamodb_resource = None


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
        get_streak_app._dynamodb_resource = dynamodb
        yield table


def test_missing_api_key(dynamodb_table):
    """Requests without x-api-key must be rejected with 401 Unauthorized."""
    event = {
        "headers": {},
        "pathParameters": {"user": "alice"},
    }
    response = get_streak_app.lambda_handler(event, None)
    assert response["statusCode"] == 401


def test_missing_user_param(dynamodb_table):
    """Missing or invalid user path param returns 400 Bad Request."""
    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "pathParameters": {"user": "invalid user!"},
    }
    response = get_streak_app.lambda_handler(event, None)
    assert response["statusCode"] == 400


def test_user_not_found(dynamodb_table):
    """User with no profile and no solves returns 404 Not Found."""
    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "pathParameters": {"user": "nonexistent"},
    }
    response = get_streak_app.lambda_handler(event, None)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert "not found" in body["error"]


def test_user_with_profile_but_no_solves(dynamodb_table):
    """Registered user who hasn't logged any solves yet returns streak_count = 0."""
    dynamodb_table.put_item(
        Item={"PK": "newbie", "SK": "PROFILE", "email": "new@example.com"}
    )

    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "pathParameters": {"user": "newbie"},
    }
    response = get_streak_app.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["user"] == "newbie"
    assert body["streak_count"] == 0
    assert body["status"] == "NO_SOLVES"


def test_user_solved_today(dynamodb_table):
    """User who solved today returns status ACTIVE_TODAY with current streak."""
    today_ist = get_ist_date_str()
    dynamodb_table.put_item(
        Item={
            "PK": "alice",
            "SK": today_ist,
            "problem": "Two Sum",
            "difficulty": "Easy",
            "streak_count": 6,
        }
    )

    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "pathParameters": {"user": "alice"},
    }
    response = get_streak_app.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["user"] == "alice"
    assert body["streak_count"] == 6
    assert body["status"] == "ACTIVE_TODAY"
    assert body["last_problem"] == "Two Sum"


def test_user_solved_yesterday_pending_today(dynamodb_table):
    """User who solved yesterday has active streak pending today's solve."""
    today_ist = get_ist_date_str()
    yesterday_ist = get_previous_date_str(today_ist)

    dynamodb_table.put_item(
        Item={
            "PK": "bob",
            "SK": yesterday_ist,
            "problem": "Climbing Stairs",
            "difficulty": "Easy",
            "streak_count": 4,
        }
    )

    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "pathParameters": {"user": "bob"},
    }
    response = get_streak_app.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["user"] == "bob"
    assert body["streak_count"] == 4
    assert body["status"] == "PENDING_TODAY"


def test_user_broken_streak_gap(dynamodb_table):
    """User whose last solve was 3 days ago returns BROKEN with streak_count = 0."""
    # Last solve was Nov 1, 2026
    dynamodb_table.put_item(
        Item={
            "PK": "charlie",
            "SK": "2026-11-01",
            "problem": "LRU Cache",
            "difficulty": "Medium",
            "streak_count": 10,
        }
    )

    event = {
        "headers": {"x-api-key": VALID_API_KEY},
        "pathParameters": {"user": "charlie"},
    }
    response = get_streak_app.lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["user"] == "charlie"
    assert body["streak_count"] == 0
    assert body["status"] == "BROKEN"
    assert body["last_solve_date"] == "2026-11-01"
