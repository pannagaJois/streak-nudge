"""GetStreak Lambda Handler.

Cloud Computing Concepts Demonstrated:
1. RESTful Query Patterns with DynamoDB:
   - Route: GET /streak/{user}
   - Uses DynamoDB Query with Sort Key condition and ScanIndexForward=False (descending)
     to fetch only the single most recent solve record in O(1) time.
   - Strictly avoids full table scans, keeping latency low and RCU consumption at 1.

2. API Security & Input Validation:
   - Enforces x-api-key authentication.
   - Sanitizes path parameter {user} against path-traversal / malformed input.

3. Accurate Real-Time Domain Evaluation:
   - Uses IST calendar dates to determine if the streak is active today,
     still alive from yesterday (pending today's solve), or broken by a gap.
"""

import json
import os
import re
from typing import Any, Dict, Optional
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from src.common.streak import (
    get_ist_date_str,
    evaluate_active_streak,
    get_previous_date_str,
)

_dynamodb_resource = None


def get_table():
    """Lazy initialize and reuse DynamoDB resource."""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = boto3.resource("dynamodb")
    table_name = os.environ.get("TABLE_NAME", "streaknudge-dev")
    return _dynamodb_resource.Table(table_name)


def build_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Format an API Gateway HTTP API v2 proxy response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,x-api-key",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
        },
        "body": json.dumps(body),
    }


def authenticate_request(headers: Optional[Dict[str, str]]) -> bool:
    """Validate x-api-key header against expected secret."""
    expected_key = os.environ.get("API_KEY", "streaknudge-secret-key-12345")
    if not headers or not expected_key:
        return False
    api_key = headers.get("x-api-key") or headers.get("X-Api-Key")
    return api_key == expected_key


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entry point for retrieving a user's streak status."""
    # Handle CORS OPTIONS pre-flight from web browsers
    http_method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod") or ""
    if http_method.upper() == "OPTIONS":
        return build_response(200, {"message": "OK"})

    # 1. API-Key Header Authentication
    headers = event.get("headers") or {}
    if not authenticate_request(headers):
        return build_response(401, {"error": "Unauthorized: Invalid or missing 'x-api-key' header"})

    # 2. Extract and Validate Path Parameter {user}
    path_params = event.get("pathParameters") or {}
    user = path_params.get("user")

    if not user or not re.match(r"^[a-zA-Z0-9_\-]{1,50}$", user):
        return build_response(
            400,
            {"error": "Path parameter 'user' must be 1-50 alphanumeric characters (or '-' / '_')"},
        )

    user = user.strip()
    table = get_table()
    today_ist = get_ist_date_str()
    yesterday_ist = get_previous_date_str(today_ist)

    try:
        # 3. Check if User PROFILE exists (1 RCU)
        profile_res = table.get_item(Key={"PK": user, "SK": "PROFILE"})
        user_profile = profile_res.get("Item")

        # 4. Query DynamoDB for the latest solve record (1 RCU)
        # Dates are formatted 'YYYY-MM-DD' so alphabetical sort equals chronological sort.
        # ScanIndexForward=False returns the most recent record first. Limit=1 stops query immediately.
        solves_res = table.query(
            KeyConditionExpression=Key("PK").eq(user) & Key("SK").begins_with("20"),
            ScanIndexForward=False,
            Limit=1,
        )
        recent_items = solves_res.get("Items", [])

        # If user neither has a profile nor any solves, return 404
        if not user_profile and not recent_items:
            return build_response(404, {"error": f"User '{user}' not found"})

        latest_item = recent_items[0] if recent_items else None

        if latest_item:
            latest_date = latest_item["SK"]
            stored_streak = int(latest_item.get("streak_count", 0))
            last_problem = latest_item.get("problem", "")
            last_difficulty = latest_item.get("difficulty", "")
        else:
            latest_date = None
            stored_streak = 0
            last_problem = None
            last_difficulty = None

        # 5. Evaluate Active Streak Status
        current_streak = evaluate_active_streak(
            today_date_str=today_ist,
            latest_solve_date_str=latest_date,
            latest_streak_count=stored_streak,
        )

        # Classify user status for rich dashboard / client feedback
        if latest_date == today_ist:
            status = "ACTIVE_TODAY"
            message = f"Streak active! Solved today ({latest_date})."
        elif latest_date == yesterday_ist:
            status = "PENDING_TODAY"
            message = f"Streak alive! Solved yesterday ({latest_date}). Log today by 9 PM IST to keep it going!"
        elif latest_date is not None:
            status = "BROKEN"
            message = f"Streak broken. Last solve was on {latest_date}. Start fresh today!"
        else:
            status = "NO_SOLVES"
            message = "No solves recorded yet. Log your first solve today!"

        return build_response(
            200,
            {
                "user": user,
                "streak_count": current_streak,
                "status": status,
                "message": message,
                "today_ist": today_ist,
                "last_solve_date": latest_date,
                "last_problem": last_problem,
                "last_difficulty": last_difficulty,
            },
        )

    except ClientError as e:
        print(f"DynamoDB ClientError: {e}")
        return build_response(500, {"error": "Internal database error"})
