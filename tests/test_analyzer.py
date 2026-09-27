import pandas as pd
import pytest

from src.analyzer import analyze_dataframe
from src.schemas import AnalysisPlan


@pytest.fixture
def df():
    return pd.DataFrame({"region": ["East", "West", "East"], "sales": [10, 20, 30]})


@pytest.mark.parametrize("operation, expected", [
    ("count", 3), ("sum", 60), ("average", 20), ("minimum", 10), ("maximum", 30),
])
def test_ungrouped_operations(df, operation, expected):
    original = df.copy(deep=True)
    plan = AnalysisPlan(operation=operation, metric="sales", chart="none")
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"].iloc[0, 0] == expected
    assert "group_size" not in result["data"].columns
    assert result["source_rows"] == 3
    assert result["steps"]
    pd.testing.assert_frame_equal(df, original)


@pytest.mark.parametrize("operation, expected", [
    ("count", [2, 1]), ("sum", [40, 20]), ("average", [20, 20]),
    ("minimum", [10, 20]), ("maximum", [30, 20]),
])
def test_grouped_operations(df, operation, expected):
    plan = AnalysisPlan(operation=operation, metric="sales", group_by=["region"], chart="none")
    result = analyze_dataframe(df, plan)
    column = "count" if operation == "count" else "sales"
    assert result["success"]
    assert result["data"]["region"].tolist() == ["East", "West"]
    assert result["data"][column].tolist() == expected
    assert result["data"]["group_size"].tolist() == [2, 1]


@pytest.mark.parametrize("operator, value, expected", [
    ("equals", 20, 1), ("not_equals", 20, 2), ("greater_than", 20, 1),
    ("greater_than_or_equal", 20, 2), ("less_than", 20, 1),
    ("less_than_or_equal", 20, 2),
])
def test_numeric_filters(df, operator, value, expected):
    original = df.copy(deep=True)
    plan = AnalysisPlan(operation="count", chart="none", filters=[
        {"column": "sales", "operator": operator, "value": value},
    ])
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["source_rows"] == expected
    assert result["data"]["count"][0] == expected
    pd.testing.assert_frame_equal(df, original)


def test_contains_is_literal_and_filters_combine():
    df = pd.DataFrame({"name": ["a.b", "axb", None, "a.b"], "sales": [1, 2, 3, 4]})
    plan = AnalysisPlan(operation="count", chart="none", filters=[
        {"column": "name", "operator": "contains", "value": "."},
        {"column": "sales", "operator": "greater_than", "value": 2},
    ])
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["source_rows"] == 1


@pytest.mark.parametrize("direction, expected", [("ascending", "West"), ("descending", "East")])
def test_sort_then_limit(df, direction, expected):
    plan = AnalysisPlan(
        operation="sum", metric="sales", group_by=["region"], chart="none",
        sort={"column": "sales", "direction": direction}, limit=1,
    )
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"]["region"].tolist() == [expected]
    assert result["data"]["group_size"].tolist() == [2 if expected == "East" else 1]
    assert result["source_rows"] == 3


def test_empty_filter_result(df):
    plan = AnalysisPlan(operation="sum", metric="sales", chart="none", filters=[
        {"column": "sales", "operator": "greater_than", "value": 100},
    ])
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"].empty
    assert result["source_rows"] == 0
    assert "No rows" in result["message"]


def test_multiple_group_columns_and_null_metrics():
    df = pd.DataFrame({"region": ["East", "East", None], "kind": ["A", "A", "B"],
                       "sales": [None, 10, 20]})
    plan = AnalysisPlan(operation="count", group_by=["region", "kind"], chart="none")
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"]["count"].tolist() == [2, 1]
    assert result["data"]["group_size"].tolist() == [2, 1]


def test_count_result_name_does_not_collide():
    df = pd.DataFrame({"count": ["A", "A", "B"]})
    plan = AnalysisPlan(operation="count", group_by=["count"], chart="none")
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"]["count_result"].tolist() == [2, 1]


@pytest.mark.parametrize("operation, metric", [("unsupported", None), ("sum", "missing")])
def test_execution_fails_safely(df, operation, metric):
    plan = AnalysisPlan(operation=operation, metric=metric, chart="none")
    result = analyze_dataframe(df, plan)
    assert not result["success"]
    assert result["data"].empty
    assert result["message"]
    assert set(result) == {"success", "data", "source_rows", "steps", "message"}


def test_equality_filter_on_text(df):
    plan = AnalysisPlan(operation="sum", metric="sales", chart="none", filters=[
        {"column": "region", "operator": "equals", "value": "East"},
    ])
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"]["sales"][0] == 40
    assert result["source_rows"] == 2


def test_contains_filter(df):
    plan = AnalysisPlan(operation="count", chart="none", filters=[
        {"column": "region", "operator": "contains", "value": "Eas"},
    ])
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"]["count"][0] == 2


@pytest.mark.parametrize("direction, expected", [
    ("ascending", ["East", "West"]), ("descending", ["West", "East"]),
])
def test_sort_by_group_column(df, direction, expected):
    plan = AnalysisPlan(
        operation="sum", metric="sales", group_by=["region"], chart="none",
        sort={"column": "region", "direction": direction},
    )
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"]["region"].tolist() == expected


def test_full_analysis_does_not_modify_original(df):
    original = df.copy(deep=True)
    plan = AnalysisPlan(
        operation="sum", metric="sales", group_by=["region"], chart="none",
        filters=[{"column": "sales", "operator": "greater_than", "value": 10}],
        sort={"column": "sales", "direction": "descending"}, limit=1,
    )
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"].to_dict("records") == [
        {"region": "East", "sales": 30, "group_size": 1}
    ]
    assert result["source_rows"] == 2
    pd.testing.assert_frame_equal(df, original)


@pytest.mark.parametrize("operator, expected", [("equals", 1), ("not_equals", 2)])
def test_filter_for_null_values(operator, expected):
    df = pd.DataFrame({"sales": [10, None, 30]})
    plan = AnalysisPlan(operation="count", chart="none", filters=[
        {"column": "sales", "operator": operator, "value": None},
    ])
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"]["count"][0] == expected


@pytest.mark.parametrize("operation, expected", [("count", 3), ("sum", 40), ("average", 20)])
def test_missing_metric_values(operation, expected):
    df = pd.DataFrame({"sales": [10, None, 30]})
    plan = AnalysisPlan(operation=operation, metric="sales", chart="none")
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"].iloc[0, 0] == expected
    assert result["source_rows"] == 3


def test_empty_source_dataframe(df):
    plan = AnalysisPlan(operation="count", chart="none")
    result = analyze_dataframe(df.iloc[:0], plan)
    assert result["success"]
    assert result["source_rows"] == 0
    assert result["data"].empty
    assert "No rows" in result["message"]


def test_group_size_includes_rows_with_missing_metrics():
    df = pd.DataFrame({"region": ["East", "East", "West"], "sales": [None, 10, 20]})
    plan = AnalysisPlan(
        operation="average", metric="sales", group_by=["region"], chart="none",
    )
    result = analyze_dataframe(df, plan)
    assert result["success"]
    assert result["data"].to_dict("records") == [
        {"region": "East", "sales": 10, "group_size": 2},
        {"region": "West", "sales": 20, "group_size": 1},
    ]
