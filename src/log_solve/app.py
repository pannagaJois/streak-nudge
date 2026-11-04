"""LogSolve Lambda Handler.

Cloud Computing Concepts Demonstrated:
1. Serverless Execution Lifecycle & Warm Starts:
   - AWS Lambda initializes code outside the handler (global scope) once per container.
   - Boto3 DynamoDB resource and table references are instantiated globally to reuse
     TCP/TLS connections across warm invocations, drastically reducing latency.

2. Security & Input Validation:
   - Validates authentication token (x-api-key header) to prevent unauthorized writes.
   - Sanitizes and validates JSON body types, bounds, and required fields before executing
     any database queries, mitigating injection and bad-data denial-of-service.

3. Idempotent & Cost-Optimized DynamoDB Writes:
   - Direct O(1) GetItem requests retrieve today's and yesterday's records with exactly
     1 RCU each, staying well within Free Tier limits.
   - Writes the new record with PutItem (1 WCU).
"""

import json
import os
import re
from typing import Any, Dict, Optional, Tuple
import boto3
from botocore.exceptions import ClientError

from src.common.streak import (
    get_ist_date_str,
    get_previous_date_str,
    calculate_streak_for_solve,
    get_ist_now,
)

_dynamodb_resource = None


def get_table():
    """Lazy initialize and reuse DynamoDB resource across invocations."""
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
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(body),
    }


def authenticate_request(headers: Optional[Dict[str, str]]) -> bool:
    """Validate x-api-key header (case-insensitive) against expected key."""
    expected_key = os.environ.get("API_KEY", "streaknudge-secret-key-12345")
    if not headers or not expected_key:
        return False
    # Headers in API Gateway v2 can be lowercase or mixed case
    api_key = headers.get("x-api-key") or headers.get("X-Api-Key")
    return api_key == expected_key


def validate_payload(data: Any) -> Tuple[bool, Optional[str]]:
    """Validate incoming POST payload schema.

    Expected:
      - user: string, alphanumeric with '-' or '_', 1-50 chars
      - problem: string, 1-150 chars
      - difficulty: 'Easy', 'Medium', or 'Hard'
      - email: optional string, basic email regex
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object"

    user = data.get("user")
    if not user or not isinstance(user, str) or not re.match(r"^[a-zA-Z0-9_\-]{1,50}$", user):
        return False, "Field 'user' is required and must be 1-50 alphanumeric characters (or '-' / '_')"

    problem = data.get("problem")
    if not problem or not isinstance(problem, str) or len(problem.strip()) == 0 or len(problem) > 150:
        return False, "Field 'problem' is required and must be between 1 and 150 characters"

    difficulty = data.get("difficulty")
    if difficulty not in ("Easy", "Medium", "Hard"):
        return False, "Field 'difficulty' must be one of: 'Easy', 'Medium', 'Hard'"

    email = data.get("email")
    if email is not None:
        if not isinstance(email, str) or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return False, "Field 'email' must be a valid email address if provided"

    return True, None


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entry point for logging a solved DSA problem."""
    # 1. API-Key Header Authentication
    headers = event.get("headers") or {}
    if not authenticate_request(headers):
        return build_response(401, {"error": "Unauthorized: Invalid or missing 'x-api-key' header"})

    # 2. Parse Request Body
    raw_body = event.get("body")
    if not raw_body:
        return build_response(400, {"error": "Missing request body"})

    try:
        data = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
    except (json.JSONDecodeError, TypeError):
        return build_response(400, {"error": "Malformed JSON in request body"})

    # 3. Validate Inputs
    is_valid, error_msg = validate_payload(data)
    if not is_valid:
        return build_response(400, {"error": error_msg})

    user = data["user"].strip()
    problem = data["problem"].strip()
    difficulty = data["difficulty"]
    email = data.get("email", "").strip()

    # 4. Compute IST Calendar Dates
    today_ist = get_ist_date_str()
    yesterday_ist = get_previous_date_str(today_ist)
    timestamp_iso = get_ist_now().isoformat()

    table = get_table()

    try:
        # 5. Fetch Today's and Yesterday's solves (2 targeted O(1) GetItem calls = 2 RCU)
        today_item_res = table.get_item(Key={"PK": user, "SK": today_ist})
        existing_today = today_item_res.get("Item")

        yesterday_item_res = table.get_item(Key={"PK": user, "SK": yesterday_ist})
        yesterday_item = yesterday_item_res.get("Item")

        # 6. Calculate Streak via pure domain logic
        new_streak = calculate_streak_for_solve(
            today_date_str=today_ist,
            existing_today_solve=existing_today,
            yesterday_solve=yesterday_item,
        )

        # 7. Write Solve Record to DynamoDB (1 WCU)
        solve_item = {
            "PK": user,
            "SK": today_ist,
            "problem": problem,
            "difficulty": difficulty,
            "streak_count": new_streak,
            "updated_at": timestamp_iso,
        }
        table.put_item(Item=solve_item)

        # 8. Upsert User PROFILE item if email provided or if profile doesn't exist
        # This guarantees the Nudge Lambda has user contact info and timezone
        profile_res = table.get_item(Key={"PK": user, "SK": "PROFILE"})
        if "Item" not in profile_res or email:
            profile_email = email or (profile_res.get("Item", {}).get("email", ""))
            table.put_item(
                Item={
                    "PK": user,
                    "SK": "PROFILE",
                    "email": profile_email,
                    "timezone": "Asia/Kolkata",
                    "last_active": timestamp_iso,
                }
            )

        return build_response(
            201,
            {
                "message": "DSA solve successfully logged!",
                "user": user,
                "date": today_ist,
                "problem": problem,
                "difficulty": difficulty,
                "streak_count": new_streak,
                "is_same_day_repeat": existing_today is not None,
            },
        )

    except ClientError as e:
        # In cloud systems, always log detailed exception internally but avoid leaking
        # internal database stack traces to API clients
        print(f"DynamoDB ClientError: {e}")
        return build_response(500, {"error": "Internal database error"})
