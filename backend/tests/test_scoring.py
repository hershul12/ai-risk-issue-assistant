from datetime import date, timedelta

import pytest

from app.scoring import calculate_score, get_priority, is_overdue


def test_calculate_score():
    assert calculate_score(4, 5) == 20


@pytest.mark.parametrize(
    "score, priority",
    [(1, "Low"), (5, "Low"), (6, "Medium"), (12, "Medium"),
     (13, "High"), (19, "High"), (20, "Critical"), (25, "Critical")],
)
def test_priority_bands(score, priority):
    assert get_priority(score) == priority


def test_is_overdue():
    yesterday = date.today() - timedelta(days=1)
    assert is_overdue(yesterday, "Open") is True
    assert is_overdue(yesterday, "Closed") is False
    assert is_overdue(date.today() + timedelta(days=1), "Open") is False
