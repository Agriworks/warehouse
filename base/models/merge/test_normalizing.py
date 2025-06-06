from datetime import date, datetime
import pytest
from models.merge.normalizing import (
    extract_month,
    group_by_month,
    aggregate_monthly,
    merge_monthly,
    merge_daily,
    MergeRequest,
)
from fastapi import HTTPException


def test_extract_month():
    assert extract_month(date(2023, 1, 15)) == "2023-01"
    assert extract_month(date(2024, 12, 1)) == "2024-12"


def test_group_by_month():
    rows = [
        {"date_col": date(2023, 1, 10), "value": 1},
        {"date_col": "2023-01-20T00:00:00", "value": 2},
        {"date_col": date(2023, 2, 5), "value": 3},
    ]
    expected = {
        "2023-01": [
            {"date_col": date(2023, 1, 10), "value": 1},
            {"date_col": "2023-01-20T00:00:00", "value": 2},
        ],
        "2023-02": [{"date_col": date(2023, 2, 5), "value": 3}],
    }
    assert group_by_month(rows, "date_col") == expected

    assert group_by_month([], "date_col") == {}


def test_aggregate_monthly():
    grouped = {
        "2023-01": [
            {"value1": 10, "value2": 100, "category": "A"},
            {"value1": 20, "value2": 200, "category": "B"},
        ],
        "2023-02": [{"value1": 30, "value2": 300, "category": "C"}],
    }
    value_cols = ["value1", "value2"]

    # Test sum
    expected_sum = {
        "2023-01": {"value1_sum": 30, "value2_sum": 300},
        "2023-02": {"value1_sum": 30, "value2_sum": 300},
    }
    assert aggregate_monthly(grouped, value_cols, "sum") == expected_sum

    # Test avg
    expected_avg = {
        "2023-01": {"value1_avg": 15.0, "value2_avg": 150.0},
        "2023-02": {"value1_avg": 30.0, "value2_avg": 300.0},
    }
    assert aggregate_monthly(grouped, value_cols, "avg") == expected_avg

    # Test max
    expected_max = {
        "2023-01": {"value1_max": 20, "value2_max": 200},
        "2023-02": {"value1_max": 30, "value2_max": 300},
    }
    assert aggregate_monthly(grouped, value_cols, "max") == expected_max

    # Test min
    expected_min = {
        "2023-01": {"value1_min": 10, "value2_min": 100},
        "2023-02": {"value1_min": 30, "value2_min": 300},
    }
    assert aggregate_monthly(grouped, value_cols, "min") == expected_min

    # Test with missing column
    grouped_missing = {
        "2023-01": [{"value1": 10}, {"value2": 200}],
    }
    expected_sum_missing = {"2023-01": {"value1_sum": 10, "value2_sum": 200}}
    assert aggregate_monthly(grouped_missing, value_cols, "sum") == expected_sum_missing

    # Test empty grouped
    assert aggregate_monthly({}, value_cols, "sum") == {}


@pytest.fixture
def sample_data_A():
    return [
        {"date": date(2023, 1, 10), "metric_a": 100, "id": 1},
        {"date": date(2023, 1, 20), "metric_a": 150, "id": 2},
        {"date": date(2023, 2, 5), "metric_a": 200, "id": 3},
        {"date": date(2023, 3, 1), "metric_a": 200, "id": 4},  # No match in B
    ]


@pytest.fixture
def sample_data_B():
    return [
        {"month": "2023-01", "metric_b": 50, "target": "T1"},
        {"month": "2023-02", "metric_b": 75, "target": "T2"},
        {"month": "2023-04", "metric_b": 90, "target": "T3"},  # No match in A
    ]


def test_merge_monthly_inner_join(sample_data_A, sample_data_B):
    result = merge_monthly(
        sample_data_A, sample_data_B, "date", "month", "sum", "inner"
    )
    assert len(result) == 2
    assert result[0]["month"] == "2023-01"
    assert result[0]["metric_a_sum"] == 250
    assert result[0]["metric_b"] == 50
    assert result[1]["month"] == "2023-02"
    assert result[1]["metric_a_sum"] == 200
    assert result[1]["metric_b"] == 75


def test_merge_monthly_left_join(sample_data_A, sample_data_B):
    result = merge_monthly(sample_data_A, sample_data_B, "date", "month", "avg", "left")
    assert len(result) == 3
    assert result[0]["month"] == "2023-01"
    assert result[0]["metric_a_avg"] == 125
    assert result[0].get("metric_b") == 50
    assert result[2]["month"] == "2023-03"
    assert result[2]["metric_a_avg"] == 200
    assert "metric_b" not in result[2]  # or result[2].get("metric_b") is None


def test_merge_monthly_right_join(sample_data_A, sample_data_B):
    result = merge_monthly(
        sample_data_A, sample_data_B, "date", "month", "max", "right"
    )
    assert len(result) == 3
    assert result[0]["month"] == "2023-01"
    assert result[0].get("metric_a_max") == 150
    assert result[0]["metric_b"] == 50
    assert result[2]["month"] == "2023-04"
    assert "metric_a_max" not in result[2]  # or result[2].get("metric_a_max") is None
    assert result[2]["metric_b"] == 90


def test_merge_monthly_outer_join(sample_data_A, sample_data_B):
    result = merge_monthly(
        sample_data_A, sample_data_B, "date", "month", "min", "outer"
    )
    assert len(result) == 4
    # Check one from A only, one from B only, one common
    months_in_result = {r["month"] for r in result}
    assert "2023-01" in months_in_result
    assert "2023-03" in months_in_result  # A only
    assert "2023-04" in months_in_result  # B only


def test_merge_monthly_empty_A(sample_data_B):
    result = merge_monthly([], sample_data_B, "date", "month", "sum", "inner")
    assert result == []
    result_outer = merge_monthly([], sample_data_B, "date", "month", "sum", "outer")
    assert len(result_outer) == len(sample_data_B)
    assert result_outer[0]["month"] == "2023-01"
    assert "metric_a_sum" not in result_outer[0]


def test_merge_monthly_empty_B(sample_data_A):
    result = merge_monthly(sample_data_A, [], "date", "month", "sum", "inner")
    assert result == []
    result_outer = merge_monthly(sample_data_A, [], "date", "month", "sum", "outer")
    assert len(result_outer) == 3  # 3 unique months in A
    assert result_outer[0]["month"] == "2023-01"
    assert "metric_b" not in result_outer[0]


def test_merge_daily_inner_join(sample_data_A, sample_data_B):
    result = merge_daily(sample_data_A, sample_data_B, "date", "month", "inner")
    # Expect 3 rows from A that have matching months in B
    assert len(result) == 3
    assert result[0]["date"] == date(2023, 1, 10)
    assert result[0]["metric_a"] == 100
    assert result[0]["metric_b"] == 50
    assert result[2]["date"] == date(2023, 2, 5)
    assert result[2]["metric_b"] == 75


def test_merge_daily_left_join(sample_data_A, sample_data_B):
    result = merge_daily(sample_data_A, sample_data_B, "date", "month", "left")
    assert len(result) == 4  # All rows from A
    assert result[3]["date"] == date(2023, 3, 1)
    assert "metric_b" not in result[3]


def test_merge_daily_right_join(sample_data_A, sample_data_B):
    # This will create many rows as it expands B to daily
    result = merge_daily(sample_data_A, sample_data_B, "date", "month", "right")
    # Expected days: Jan (31) + Feb (28) + Apr (30) = 89
    # Check if all days from B's months are present, and A's data is merged where applicable
    assert len(result) == (31 + 28 + 30)  # Days in Jan, Feb, Apr 2023

    # Check a day from A that has a match
    day_2023_01_10 = next(r for r in result if r["date"] == date(2023, 1, 10))
    assert day_2023_01_10["metric_a"] == 100
    assert day_2023_01_10["metric_b"] == 50

    # Check a day from B that has no match in A
    day_2023_04_15 = next(r for r in result if r["date"] == date(2023, 4, 15))
    assert "metric_a" not in day_2023_04_15
    assert day_2023_04_15["metric_b"] == 90


def test_merge_request_validation():
    # Valid
    MergeRequest(
        left_db="db",
        left_collection="coll",
        right_db="db",
        right_collection="coll",
        left_time_col="d",
        right_time_col="m",
        target_resolution="monthly",
        aggregation="sum",
    )
    with pytest.raises(ValueError):
        MergeRequest(
            left_db="db",
            left_collection="coll",
            right_db="db",
            right_collection="coll",
            left_time_col="d",
            right_time_col="m",
            target_resolution="monthly",
        )

    # Invalid aggregation
    with pytest.raises(ValueError):
        MergeRequest(
            left_db="db",
            left_collection="coll",
            right_db="db",
            right_collection="coll",
            left_time_col="d",
            right_time_col="m",
            target_resolution="monthly",
            aggregation="invalid_agg",
        )

    # Invalid target_resolution
    with pytest.raises(ValueError):
        MergeRequest(
            left_db="db",
            left_collection="coll",
            right_db="db",
            right_collection="coll",
            left_time_col="d",
            right_time_col="m",
            target_resolution="yearly",
            aggregation="sum",
        )
