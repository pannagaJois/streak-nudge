"""Nudge Lambda Handler.

Cloud Computing Concepts Demonstrated:
1. Event-Driven Scheduling with EventBridge & Cron:
   - AWS EventBridge acts as a serverless cron orchestrator emitting a scheduled event
     at 15:30 UTC (which maps precisely to 21:00 / 9:00 PM Indian Standard Time).
   - Invokes this Lambda function in an entirely asynchronous, serverless manner.

2. Pub/Sub Messaging Pattern with Amazon SNS:
   - Decouples notification delivery from business logic.
   - Amazon Simple Notification Service (SNS) handles fan-out to email subscribers,
     automatic retries, and protocol abstraction.

3. Least-Privilege IAM & Resource Scoping:
   - Permissions are restricted to:
     * DynamoDB Scan (for PROFILE items), GetItem, and Query on the specific table ARN.
     * SNS Publish strictly on the specific Topic ARN (no wildcards).

4. Idempotent Streak Inspection:
   - Only alerts users whose IST solve record for today is missing.
"""

import json
import os
from typing import Any, Dict, List
import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

from src.common.streak import (
    get_ist_date_str,
    evaluate_active_streak,
    get_previous_date_str,
)

DYNAMODB_TABLE_NAME = os.environ.get("TABLE_NAME", "streaknudge-dev")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")

_dynamodb_resource = None
_sns_client = None


def get_dynamo_table():
    """Lazy initialize and reuse DynamoDB resource across warm invocations."""
    global _dynamodb_resource
    if _dynamodb_resource is None:
        _dynamodb_resource = boto3.resource("dynamodb")
    table_name = os.environ.get("TABLE_NAME", "streaknudge-dev")
    return _dynamodb_resource.Table(table_name)


def get_sns_client():
    """Lazy initialize and reuse SNS client across warm invocations."""
    global _sns_client
    if _sns_client is None:
        _sns_client = boto3.client("sns")
    return _sns_client


def send_nudge_email(user: str, email: str, streak_count: int, today_ist: str, topic_arn: str) -> bool:
    """Publish a personalized reminder email to the SNS topic."""
    if not topic_arn:
        print(f"SNS_TOPIC_ARN not configured; skipping email for {user}")
        return False

    sns = get_sns_client()
    subject = f"[StreakNudge] Keep your {streak_count}-day DSA streak alive! 🚀"
    
    streak_msg = (
        f"You currently have an active streak of {streak_count} day(s)!"
        if streak_count > 0
        else "Start a brand-new DSA streak today!"
    )

    message = (
        f"Hi {user},\n\n"
        f"This is your daily 9:00 PM IST reminder from StreakNudge.\n\n"
        f"We noticed you haven't logged any solved DSA or NeetCode problem for today ({today_ist}) yet.\n"
        f"{streak_msg}\n\n"
        f"You still have 3 hours before midnight IST! Log your solve via the StreakNudge API to keep your streak going.\n\n"
        f"Solve details can be posted to: POST /solves\n\n"
        f"Happy coding,\n"
        f"The StreakNudge Bot"
    )

    try:
        sns.publish(
            TopicArn=topic_arn,
            Subject=subject[:100],  # SNS Subject limit is 100 characters
            Message=message,
        )
        print(f"Successfully published nudge for user '{user}' to SNS topic {topic_arn}")
        return True
    except ClientError as e:
        print(f"Failed to publish SNS nudge for user '{user}': {e}")
        return False


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda entry point for daily 9:00 PM IST streak nudge."""
    table = get_dynamo_table()
    topic_arn = os.environ.get("SNS_TOPIC_ARN", "")
    today_ist = get_ist_date_str()
    yesterday_ist = get_previous_date_str(today_ist)

    print(f"Starting StreakNudge job for IST date: {today_ist}")

    nudged_users: List[str] = []
    scanned_profiles = 0

    try:
        # 1. Scan DynamoDB for all user PROFILE records
        # SK='PROFILE' items hold user preferences (email, timezone)
        response = table.scan(FilterExpression=Attr("SK").eq("PROFILE"))
        profiles = response.get("Items", [])
        scanned_profiles = len(profiles)

        for profile in profiles:
            user = profile.get("PK")
            email = profile.get("email", "")
            if not user:
                continue

            # 2. Check if user already logged a solve today in IST (1 RCU)
            today_res = table.get_item(Key={"PK": user, "SK": today_ist})
            if "Item" in today_res:
                print(f"User '{user}' has already solved a problem today ({today_ist}). No nudge needed.")
                continue

            # 3. User has NOT solved today!
            # Query their most recent solve to report their current streak count (1 RCU)
            solves_res = table.query(
                KeyConditionExpression=Key("PK").eq(user) & Key("SK").begins_with("20"),
                ScanIndexForward=False,
                Limit=1,
            )
            recent_items = solves_res.get("Items", [])
            if recent_items:
                last_date = recent_items[0]["SK"]
                stored_streak = int(recent_items[0].get("streak_count", 0))
                # Evaluate if streak is alive from yesterday
                active_streak = evaluate_active_streak(today_ist, last_date, stored_streak)
            else:
                active_streak = 0

            # 4. Trigger Pub/Sub Nudge via Amazon SNS
            sent = send_nudge_email(
                user=user,
                email=email,
                streak_count=active_streak,
                today_ist=today_ist,
                topic_arn=topic_arn,
            )
            if sent:
                nudged_users.append(user)

        summary = {
            "status": "SUCCESS",
            "today_ist": today_ist,
            "profiles_scanned": scanned_profiles,
            "nudges_sent": len(nudged_users),
            "nudged_users": nudged_users,
        }
        print(f"StreakNudge complete: {json.dumps(summary)}")
        return summary

    except ClientError as e:
        print(f"DynamoDB ClientError in Nudge Lambda: {e}")
        return {"status": "ERROR", "error": str(e)}
