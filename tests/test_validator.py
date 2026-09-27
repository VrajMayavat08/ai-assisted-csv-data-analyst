import pandas as pd
import pytest

from src.schemas import AnalysisPlan
from src.validator import validate_plan


@pytest.fixture
def df():
    return pd.DataFrame({"sales": [10, 20], "region": ["East", "West"]})


@pytest.mark.parametrize("operation", ["sum", "average", "minimum", "maximum", "count"])
def test_valid_plan(df, operation):
    plan = AnalysisPlan(
        operation=operation, metric="sales", group_by=["region"], chart="bar",
        filters=[{"column": "sales", "operator": "greater_than", "value": 0}],
        sort={"column": "sales", "direction": "descending"},
    )
    assert validate_plan(plan, df) == {"is_valid": True, "errors": []}


@pytest.mark.parametrize("operation", ["sum", "average", "minimum", "maximum"])
def test_metric_is_required(df, operation):
    result = validate_plan(AnalysisPlan(operation=operation, chart="none"), df)
    assert not result["is_valid"]
    assert "requires a metric" in result["errors"][0]


@pytest.mark.parametrize("operation", ["sum", "average"])
def test_numeric_metric_is_required(df, operation):
    plan = AnalysisPlan(operation=operation, metric="region", chart="none")
    result = validate_plan(plan, df)
    assert not result["is_valid"]
    assert "requires a numeric metric" in result["errors"][0]
    assert "region" in result["errors"][0]


def test_missing_columns_produce_readable_errors(df):
    plan = AnalysisPlan(
        operation="count", metric="missing_metric", group_by=["missing_group"],
        filters=[{"column": "missing_filter", "operator": "equals", "value": 1}],
        sort={"column": "missing_sort", "direction": "ascending"}, chart="none",
    )
    result = validate_plan(plan, df)
    assert not result["is_valid"]
    assert len(result["errors"]) == 4
    assert "Metric column 'missing_metric' does not exist." in result["errors"]
    assert "Group-by column 'missing_group' does not exist." in result["errors"]
    assert "Filter column 'missing_filter' does not exist." in result["errors"]
    assert "Sort column 'missing_sort' does not exist." in result["errors"]


@pytest.mark.parametrize("column, valid", [("sales", True), ("region", False)])
@pytest.mark.parametrize("operator", [
    "greater_than", "greater_than_or_equal", "less_than", "less_than_or_equal"
])
def test_numeric_filters(df, column, valid, operator):
    plan = AnalysisPlan(
        operation="count", chart="none",
        filters=[{"column": column, "operator": operator, "value": 10}],
    )
    result = validate_plan(plan, df)
    assert result["is_valid"] == valid
    if not valid:
        assert "requires a numeric column" in result["errors"][0]


@pytest.mark.parametrize("values, valid", [
    (["East", None], True), ([1, 2], False), (["East", 2], False),
    ([None, None], False),
])
def test_contains_checks_object_column_values(values, valid):
    df = pd.DataFrame({"value": pd.Series(values, dtype=object)})
    plan = AnalysisPlan(
        operation="count", chart="none",
        filters=[{"column": "value", "operator": "contains", "value": "East"}],
    )
    result = validate_plan(plan, df)
    assert result["is_valid"] == valid
    if not valid:
        assert "requires a text column" in result["errors"][0]


@pytest.mark.parametrize("column, valid", [("sales", True), ("region", False)])
def test_sort_must_be_relevant(df, column, valid):
    plan = AnalysisPlan(
        operation="sum", metric="sales", chart="none",
        sort={"column": column, "direction": "ascending"},
    )
    assert validate_plan(plan, df)["is_valid"] == valid


def test_sort_by_group_column_is_valid(df):
    plan = AnalysisPlan(
        operation="count", group_by=["region"], chart="none",
        sort={"column": "region", "direction": "ascending"},
    )
    assert validate_plan(plan, df)["is_valid"]


def test_unsupported_plan_is_invalid(df):
    plan = AnalysisPlan(operation="unsupported", chart="none")
    result = validate_plan(plan, df)
    assert not result["is_valid"]
    assert "Unsupported" in result["errors"][0]
