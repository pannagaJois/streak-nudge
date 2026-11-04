"""Unit tests for Nudge Lambda handler using moto."""

import boto3
from moto import mock_aws
import pytest

from src.nudge import app as nudge_app
from src.common.streak import get_ist_date_str, get_previous_date_str

TABLE_NAME = "streaknudge-test"


@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Set environment variables for tests."""
    monkeypatch.setenv("AWS_DEFAULT_REGION", "ap-south-1")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("TABLE_NAME", TABLE_NAME)
    nudge_app._dynamodb_resource = None
    nudge_app._sns_client = None


@pytest.fixture
def aws_resources():
    """Create mocked DynamoDB table and SNS Topic."""
    with mock_aws():
        region = "ap-south-1"
        dynamodb = boto3.resource("dynamodb", region_name=region)
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

        sns = boto3.client("sns", region_name=region)
        topic_res = sns.create_topic(Name="streaknudge-test-topic")
        topic_arn = topic_res["TopicArn"]

        # Subscribe a dummy email
        sns.subscribe(TopicArn=topic_arn, Protocol="email", Endpoint="student@example.com")

        nudge_app._dynamodb_resource = dynamodb
        nudge_app._sns_client = sns

        yield table, sns, topic_arn


def test_user_already_solved_today_no_nudge(aws_resources, monkeypatch):
    """If user logged a solve today, Nudge Lambda should not send an email."""
    table, sns, topic_arn = aws_resources
    monkeypatch.setenv("SNS_TOPIC_ARN", topic_arn)

    today_ist = get_ist_date_str()

    # User profile
    table.put_item(Item={"PK": "alice", "SK": "PROFILE", "email": "alice@example.com"})
    # User solve today
    table.put_item(
        Item={
            "PK": "alice",
            "SK": today_ist,
            "problem": "Two Sum",
            "difficulty": "Easy",
            "streak_count": 5,
        }
    )

    result = nudge_app.lambda_handler({}, None)
    assert result["status"] == "SUCCESS"
    assert result["profiles_scanned"] == 1
    assert result["nudges_sent"] == 0
    assert result["nudged_users"] == []


def test_user_not_solved_today_gets_nudged(aws_resources, monkeypatch):
    """If user hasn't solved today, Nudge Lambda sends a nudge with active streak."""
    table, sns, topic_arn = aws_resources
    monkeypatch.setenv("SNS_TOPIC_ARN", topic_arn)

    today_ist = get_ist_date_str()
    yesterday_ist = get_previous_date_str(today_ist)

    # Bob's profile
    table.put_item(Item={"PK": "bob", "SK": "PROFILE", "email": "bob@example.com"})
    # Bob solved yesterday with streak 4 (no solve today)
    table.put_item(
        Item={
            "PK": "bob",
            "SK": yesterday_ist,
            "problem": "Climbing Stairs",
            "difficulty": "Easy",
            "streak_count": 4,
        }
    )

    result = nudge_app.lambda_handler({}, None)
    assert result["status"] == "SUCCESS"
    assert result["profiles_scanned"] == 1
    assert result["nudges_sent"] == 1
    assert result["nudged_users"] == ["bob"]


def test_multiple_users_selective_nudging(aws_resources, monkeypatch):
    """Multiple users: only users with missing today solves are nudged."""
    table, sns, topic_arn = aws_resources
    monkeypatch.setenv("SNS_TOPIC_ARN", topic_arn)

    today_ist = get_ist_date_str()

    # Alice: solved today
    table.put_item(Item={"PK": "alice", "SK": "PROFILE", "email": "alice@example.com"})
    table.put_item(Item={"PK": "alice", "SK": today_ist, "problem": "P1", "streak_count": 2})

    # Bob: hasn't solved today
    table.put_item(Item={"PK": "bob", "SK": "PROFILE", "email": "bob@example.com"})

    # Charlie: hasn't solved today
    table.put_item(Item={"PK": "charlie", "SK": "PROFILE", "email": "charlie@example.com"})

    result = nudge_app.lambda_handler({}, None)
    assert result["status"] == "SUCCESS"
    assert result["profiles_scanned"] == 3
    assert result["nudges_sent"] == 2
    assert set(result["nudged_users"]) == {"bob", "charlie"}


def test_missing_sns_topic_arn_graceful(aws_resources, monkeypatch):
    """Missing SNS_TOPIC_ARN should log and handle gracefully without crashing."""
    table, sns, _ = aws_resources
    monkeypatch.setenv("SNS_TOPIC_ARN", "")

    table.put_item(Item={"PK": "dave", "SK": "PROFILE", "email": "dave@example.com"})

    result = nudge_app.lambda_handler({}, None)
    assert result["status"] == "SUCCESS"
    assert result["nudges_sent"] == 0
