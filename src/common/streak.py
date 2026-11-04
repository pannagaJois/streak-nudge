"""Streak calculation logic and IST date utilities.

Cloud Computing Concepts Demonstrated:
1. Pure Business Logic Separation:
   Separating domain logic from cloud infrastructure (Lambda/DynamoDB) enables
   fast, deterministic unit testing without spinning up cloud resources or mocks.

2. UTC vs. Regional Timezones in Cloud Runtimes:
   AWS Lambda execution environments run with UTC system clocks (TZ=UTC).
   A common real-world pitfall is calculating calendar dates directly from UTC,
   which shifts at midnight UTC instead of midnight in the user's timezone.
   Here we explicitly normalize all timestamps to Indian Standard Time (IST, UTC+5:30).

3. Idempotency & Duplicate Handling:
   In distributed serverless systems, retries or duplicate user submissions can occur.
   If a user logs multiple solves on the same calendar day, the streak calculation
   is idempotent: the streak count does not artificially increment twice.
"""

from datetime import datetime, date, timedelta, timezone
from typing import Optional, Dict, Any

# Indian Standard Time (IST) is UTC+05:30 with no daylight saving shifts.
IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def get_ist_now() -> datetime:
    """Return the current datetime localized to Indian Standard Time (IST)."""
    return datetime.now(timezone.utc).astimezone(IST)


def get_ist_date_str(dt: Optional[datetime] = None) -> str:
    """Return 'YYYY-MM-DD' string for the given datetime in IST (defaults to now)."""
    if dt is None:
        dt = get_ist_now()
    elif dt.tzinfo is None:
        # If naive datetime passed, assume UTC and convert to IST
        dt = dt.replace(tzinfo=timezone.utc).astimezone(IST)
    else:
        dt = dt.astimezone(IST)
    return dt.strftime("%Y-%m-%d")


def get_previous_date_str(date_str: str) -> str:
    """Given a 'YYYY-MM-DD' date string, return the 'YYYY-MM-DD' string for the day before."""
    d = datetime.strptime(date_str, "%Y-%m-%d").date()
    prev = d - timedelta(days=1)
    return prev.strftime("%Y-%m-%d")


def calculate_streak_for_solve(
    today_date_str: str,
    existing_today_solve: Optional[Dict[str, Any]] = None,
    yesterday_solve: Optional[Dict[str, Any]] = None,
) -> int:
    """Calculate the streak count when a user logs a solve today.

    Rules:
    - Same-day re-log: Streak count remains unchanged (prevents double counting).
    - Consecutive day: If user solved yesterday, new streak = yesterday_streak + 1.
    - First solve or gap (>1 day): Resets streak to 1.

    Args:
        today_date_str: Today's date string in 'YYYY-MM-DD' format (IST).
        existing_today_solve: Existing DynamoDB solve item for today, if any.
        yesterday_solve: Existing DynamoDB solve item for yesterday, if any.

    Returns:
        The updated streak count (integer >= 1).
    """
    # Case 1: Multiple solves on the same IST day
    # Cloud Concept: Idempotency - repeated requests on the same day do not inflate streak.
    if existing_today_solve is not None:
        return int(existing_today_solve.get("streak_count", 1))

    # Case 2: Consecutive solve (yesterday's solve exists)
    if yesterday_solve is not None:
        prev_streak = int(yesterday_solve.get("streak_count", 0))
        return prev_streak + 1

    # Case 3: First-ever solve or gap (previous solve was before yesterday)
    return 1


def evaluate_active_streak(
    today_date_str: str,
    latest_solve_date_str: Optional[str],
    latest_streak_count: int = 0,
) -> int:
    """Evaluate whether a user's current streak is still active or has broken.

    Streak Rubric Rule:
    - Streak = consecutive IST days with at least one solve, ending today or yesterday.
    - If user solved today: streak is active.
    - If user solved yesterday: streak is still alive (pending today's solve).
    - If user last solved 2 or more days ago (or never): streak is broken -> 0.

    Args:
        today_date_str: Current date in IST ('YYYY-MM-DD').
        latest_solve_date_str: Date of the user's most recent solve ('YYYY-MM-DD'), or None.
        latest_streak_count: Stored streak_count from the most recent solve.

    Returns:
        The active streak count (integer >= 0).
    """
    if not latest_solve_date_str or latest_streak_count <= 0:
        return 0

    yesterday_date_str = get_previous_date_str(today_date_str)

    if latest_solve_date_str in (today_date_str, yesterday_date_str):
        return int(latest_streak_count)

    # Gap of 2+ days -> streak expired
    return 0
