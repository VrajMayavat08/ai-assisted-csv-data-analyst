"""Validate analysis plans against the available dataset columns."""

import pandas as pd
from pandas.api.types import is_numeric_dtype

from src.schemas import AnalysisPlan, FilterOperator, Operation


def validate_plan(plan: AnalysisPlan, df: pd.DataFrame):
    """Return an is_valid flag and readable errors without executing the plan.

    Sorting is allowed on existing metric or group_by columns. Text columns
    have a pandas string dtype or contain only strings among non-null values.
    """
    errors = []

    if plan.operation == Operation.UNSUPPORTED:
        errors.append("Unsupported plans cannot be executed.")

    metric_operations = (
        Operation.SUM, Operation.AVERAGE, Operation.MINIMUM, Operation.MAXIMUM
    )
    if plan.metric is None:
        if plan.operation in metric_operations:
            errors.append(f"Operation '{plan.operation.value}' requires a metric.")
    elif plan.metric not in df.columns:
        errors.append(f"Metric column '{plan.metric}' does not exist.")
    elif plan.operation in (Operation.SUM, Operation.AVERAGE):
        if not is_numeric_dtype(df[plan.metric]):
            errors.append(
                f"Operation '{plan.operation.value}' requires a numeric metric; "
                f"'{plan.metric}' is not numeric."
            )

    for column in plan.group_by:
        if column not in df.columns:
            errors.append(f"Group-by column '{column}' does not exist.")

    numeric_operators = (
        FilterOperator.GREATER_THAN,
        FilterOperator.GREATER_THAN_OR_EQUAL,
        FilterOperator.LESS_THAN,
        FilterOperator.LESS_THAN_OR_EQUAL,
    )
    for condition in plan.filters:
        if condition.column not in df.columns:
            errors.append(f"Filter column '{condition.column}' does not exist.")
            continue

        column = df[condition.column]
        if condition.operator in numeric_operators:
            if not is_numeric_dtype(column):
                errors.append(
                    f"Filter '{condition.operator.value}' requires a numeric column; "
                    f"'{condition.column}' is not numeric."
                )
        elif condition.operator == FilterOperator.CONTAINS:
            non_null_values = column.dropna()
            is_text = isinstance(column.dtype, pd.StringDtype) or (
                len(non_null_values) > 0
                and all(isinstance(value, str) for value in non_null_values)
            )
            if not is_text:
                errors.append(
                    f"Filter 'contains' requires a text column; "
                    f"'{condition.column}' is not text."
                )

    if plan.sort is not None:
        sort_column = plan.sort.column
        if sort_column not in df.columns:
            errors.append(f"Sort column '{sort_column}' does not exist.")
        elif sort_column != plan.metric and sort_column not in plan.group_by:
            errors.append(
                f"Sort column '{sort_column}' must be the metric or a group-by column."
            )

    return {"is_valid": not errors, "errors": errors}
