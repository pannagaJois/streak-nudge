"""Unit tests for DynamoDB Single-Table schema interactions using moto.

Cloud Concepts Tested:
1. Single-Table Overloading: Storing different entity types (Profile vs Daily Solve)
   under the same Partition Key (PK=user) distinguished by Sort Key (SK).
2. DynamoDB Query vs GetItem:
   - GetItem provides constant O(1) time and predictable 1 RCU consumption.
   - Query retrieves latest records sorted by SK without scanning the full table.
3. DynamoDB Scan with FilterExpression:
   - Used sparingly by Nudge Lambda to discover all registered users (SK='PROFILE').
"""

import boto3
from moto import mock_aws
import pytest

TABLE_NAME = "streaknudge-test"


@pytest.fixture
def dynamodb_table():
    """Create a mocked DynamoDB single-table conforming to template.yaml."""
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
        yield table


def test_put_and_get_user_profile(dynamodb_table):
    """Test creating and retrieving a user PROFILE entity."""
    dynamodb_table.put_item(
        Item={
            "PK": "alice",
            "SK": "PROFILE",
            "email": "alice@example.com",
            "timezone": "Asia/Kolkata",
            "created_at": "2026-11-01T10:00:00+05:30",
        }
    )

    response = dynamodb_table.get_item(Key={"PK": "alice", "SK": "PROFILE"})
    assert "Item" in response
    item = response["Item"]
    assert item["PK"] == "alice"
    assert item["SK"] == "PROFILE"
    assert item["email"] == "alice@example.com"
    assert item["timezone"] == "Asia/Kolkata"


def test_put_and_get_daily_solve(dynamodb_table):
    """Test creating and retrieving a daily solve item."""
    dynamodb_table.put_item(
        Item={
            "PK": "alice",
            "SK": "2026-11-05",
            "problem": "Two Sum",
            "difficulty": "Easy",
            "streak_count": 1,
            "updated_at": "2026-11-05T20:30:00+05:30",
        }
    )

    response = dynamodb_table.get_item(Key={"PK": "alice", "SK": "2026-11-05"})
    assert "Item" in response
    item = response["Item"]
    assert item["PK"] == "alice"
    assert item["SK"] == "2026-11-05"
    assert item["problem"] == "Two Sum"
    assert item["difficulty"] == "Easy"
    assert item["streak_count"] == 1


def test_scan_profiles_for_nudge(dynamodb_table):
    """Test scanning exclusively for PROFILE items (used by Nudge Lambda)."""
    # Put profiles
    dynamodb_table.put_item(
        Item={"PK": "alice", "SK": "PROFILE", "email": "alice@example.com"}
    )
    dynamodb_table.put_item(
        Item={"PK": "bob", "SK": "PROFILE", "email": "bob@example.com"}
    )
    # Put solve items (which should NOT be treated as profiles)
    dynamodb_table.put_item(
        Item={"PK": "alice", "SK": "2026-11-05", "problem": "3Sum", "streak_count": 2}
    )

    # Scan with filter SK = 'PROFILE'
    from boto3.dynamodb.conditions import Key, Attr

    response = dynamodb_table.scan(
        FilterExpression=Attr("SK").eq("PROFILE")
    )
    items = response.get("Items", [])
    assert len(items) == 2
    users = {item["PK"] for item in items}
    assert users == {"alice", "bob"}


def test_query_user_solves_descending(dynamodb_table):
    """Test querying solves for a user in descending chronological order."""
    dynamodb_table.put_item(
        Item={"PK": "alice", "SK": "PROFILE", "email": "alice@example.com"}
    )
    dynamodb_table.put_item(
        Item={"PK": "alice", "SK": "2026-11-03", "problem": "P1", "streak_count": 1}
    )
    dynamodb_table.put_item(
        Item={"PK": "alice", "SK": "2026-11-04", "problem": "P2", "streak_count": 2}
    )
    dynamodb_table.put_item(
        Item={"PK": "alice", "SK": "2026-11-05", "problem": "P3", "streak_count": 3}
    )

    from boto3.dynamodb.conditions import Key

    # Query with SK < "PROFILE" or SK between dates in reverse
    # Note: "2026-11-05" < "PROFILE" in ASCII ("2" < "P")
    response = dynamodb_table.query(
        KeyConditionExpression=Key("PK").eq("alice") & Key("SK").begins_with("2026-"),
        ScanIndexForward=False,  # Descending: latest date first
        Limit=1,
    )
    items = response.get("Items", [])
    assert len(items) == 1
    assert items[0]["SK"] == "2026-11-05"
    assert items[0]["streak_count"] == 3
