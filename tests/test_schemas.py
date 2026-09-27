import pytest
from pydantic import ValidationError

from src.schemas import AnalysisPlan, ChartType, FilterOperator, Operation, SortDirection


def test_valid_analysis_plan_is_accepted():
    plan = AnalysisPlan(
        operation="sum",
        metric="sales",
        group_by=["region"],
        filters=[{"column": "sales", "operator": "greater_than", "value": 0}],
        sort={"column": "sales", "direction": "descending"},
        limit=10,
        chart="bar",
        reason="Show total sales by region.",
    )

    assert plan.operation == Operation.SUM
    assert plan.metric == "sales"
    assert plan.group_by == ["region"]
    assert plan.filters[0].column == "sales"
    assert plan.filters[0].operator == FilterOperator.GREATER_THAN
    assert plan.filters[0].value == 0
    assert plan.sort.column == "sales"
    assert plan.sort.direction == SortDirection.DESCENDING
    assert plan.limit == 10
    assert plan.chart == ChartType.BAR
    assert plan.reason == "Show total sales by region."


def test_invalid_operation_is_rejected():
    with pytest.raises(ValidationError, match="operation"):
        AnalysisPlan(operation="median", chart="bar")


def test_invalid_chart_type_is_rejected():
    with pytest.raises(ValidationError, match="chart"):
        AnalysisPlan(operation="count", chart="pie")


@pytest.mark.parametrize("limit", [0, -1])
def test_non_positive_limit_is_rejected(limit):
    with pytest.raises(ValidationError, match="limit"):
        AnalysisPlan(operation="count", chart="none", limit=limit)
