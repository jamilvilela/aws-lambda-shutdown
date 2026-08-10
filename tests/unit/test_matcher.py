"""Tests for schedule matcher."""

from datetime import datetime

from src.config.models import Schedule
from src.schedule.matcher import matches


def test_matches_specific_day_and_time(monday_0300):
    schedule = Schedule(daysOfWeek=["MON"], times=["03:00"])
    assert matches(schedule, monday_0300)


def test_does_not_match_wrong_day(monday_0300, tuesday_0300):
    schedule = Schedule(daysOfWeek=["MON"], times=["03:00"])
    assert matches(schedule, monday_0300)
    assert not matches(schedule, tuesday_0300)


def test_does_not_match_wrong_time(monday_0300, monday_2200):
    schedule = Schedule(daysOfWeek=["MON"], times=["03:00"])
    assert matches(schedule, monday_0300)
    assert not matches(schedule, monday_2200)


def test_matches_any_time_in_list(monday_0300, monday_2200):
    schedule = Schedule(daysOfWeek=["MON"], times=["03:00", "22:00"])
    assert matches(schedule, monday_0300)
    assert matches(schedule, monday_2200)


def test_matches_multiple_days():
    schedule = Schedule(daysOfWeek=["MON", "WED", "FRI"], times=["03:00"])
    mon = datetime(2024, 1, 1, 3, 0)  # Monday
    wed = datetime(2024, 1, 3, 3, 0)  # Wednesday
    fri = datetime(2024, 1, 5, 3, 0)  # Friday
    tue = datetime(2024, 1, 2, 3, 0)  # Tuesday
    assert matches(schedule, mon)
    assert matches(schedule, wed)
    assert matches(schedule, fri)
    assert not matches(schedule, tue)