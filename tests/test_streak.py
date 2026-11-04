"""Unit tests for src/common/streak.py

Covers:
- First-ever solve logic (streak = 1)
- Consecutive days solve logic (streak increments)
- Same-day duplicate solve logic (streak count preserved, no double count)
- Gap / missed day logic (streak resets to 1)
- Active streak evaluation (ending today or yesterday is valid; 2+ days gap is 0)
- IST date conversions and boundary crossings (e.g. UTC vs IST, month & leap year boundaries)
"""

from datetime import datetime, timezone
import pytest
from src.common.streak import (
    get_ist_date_str,
    get_previous_date_str,
    calculate_streak_for_solve,
    evaluate_active_streak,
    IST,
)


def test_ist_date_conversion_utc_boundary():
    """Verify UTC 19:00 on Nov 4 is Nov 5 in IST (+5:30)."""
    utc_time = datetime(2026, 11, 4, 19, 0, 0, tzinfo=timezone.utc)
    # 19:00 UTC + 5:30 = 00:30 on Nov 5 in IST
    assert get_ist_date_str(utc_time) == "2026-11-05"


def test_ist_date_conversion_same_day():
    """Verify UTC 10:00 on Nov 4 is Nov 4 in IST (15:30 IST)."""
    utc_time = datetime(2026, 11, 4, 10, 0, 0, tzinfo=timezone.utc)
    assert get_ist_date_str(utc_time) == "2026-11-04"


def test_previous_date_calculation():
    """Verify day-before calculation across month and leap-year boundaries."""
    assert get_previous_date_str("2026-11-05") == "2026-11-04"
    assert get_previous_date_str("2026-03-01") == "2026-02-28"  # Non-leap year
    assert get_previous_date_str("2024-03-01") == "2024-02-29"  # Leap year 2024
    assert get_previous_date_str("2026-01-01") == "2025-12-31"  # Year boundary


def test_first_ever_solve():
    """First-ever solve should establish a streak of 1."""
    streak = calculate_streak_for_solve(
        today_date_str="2026-11-05",
        existing_today_solve=None,
        yesterday_solve=None,
    )
    assert streak == 1


def test_consecutive_day_solve():
    """Solving on consecutive days should increment the streak by 1."""
    yesterday_item = {
        "user": "alice",
        "date": "2026-11-04",
        "streak_count": 5,
        "problem": "Two Sum",
        "difficulty": "Easy",
    }
    streak = calculate_streak_for_solve(
        today_date_str="2026-11-05",
        existing_today_solve=None,
        yesterday_solve=yesterday_item,
    )
    assert streak == 6


def test_same_day_relog_no_double_count():
    """Logging multiple solves on the same day must preserve existing streak count."""
    existing_today = {
        "user": "alice",
        "date": "2026-11-05",
        "streak_count": 4,
        "problem": "Valid Anagram",
        "difficulty": "Easy",
    }
    # Even if yesterday existed, existing_today takes precedence
    yesterday_item = {
        "user": "alice",
        "date": "2026-11-04",
        "streak_count": 3,
    }
    streak = calculate_streak_for_solve(
        today_date_str="2026-11-05",
        existing_today_solve=existing_today,
        yesterday_solve=yesterday_item,
    )
    assert streak == 4, "Same day solve must not increment streak"


def test_gap_resets_streak_to_one():
    """A gap (no solve yesterday) resets streak to 1, regardless of older history."""
    # Yesterday solve is None, simulating a gap
    streak = calculate_streak_for_solve(
        today_date_str="2026-11-05",
        existing_today_solve=None,
        yesterday_solve=None,
    )
    assert streak == 1


def test_evaluate_active_streak_solved_today():
    """If user solved today, streak is active with current streak count."""
    active_streak = evaluate_active_streak(
        today_date_str="2026-11-05",
        latest_solve_date_str="2026-11-05",
        latest_streak_count=7,
    )
    assert active_streak == 7


def test_evaluate_active_streak_solved_yesterday():
    """If user solved yesterday, streak is still active pending today's log."""
    active_streak = evaluate_active_streak(
        today_date_str="2026-11-05",
        latest_solve_date_str="2026-11-04",
        latest_streak_count=7,
    )
    assert active_streak == 7


def test_evaluate_active_streak_broken_by_gap():
    """If last solve was 2 or more days ago, streak has broken and returns 0."""
    active_streak = evaluate_active_streak(
        today_date_str="2026-11-05",
        latest_solve_date_str="2026-11-03",  # 2 days ago
        latest_streak_count=10,
    )
    assert active_streak == 0


def test_evaluate_active_streak_no_solves():
    """If user has no solves recorded, active streak is 0."""
    assert evaluate_active_streak("2026-11-05", None, 0) == 0
    assert evaluate_active_streak("2026-11-05", "", 0) == 0
