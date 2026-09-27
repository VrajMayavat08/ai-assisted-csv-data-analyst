"""Execute structured analysis plans using explicit pandas operations."""

import pandas as pd

from src.schemas import AnalysisPlan, FilterOperator, Operation, SortDirection


def analyze_dataframe(df: pd.DataFrame, plan: AnalysisPlan):
    """Return success, data (a DataFrame), source_rows, steps, and message.

    Filters are combined with AND. Count counts rows, including null metrics.
    Source rows are counted after filtering and before aggregation or limiting.
    Aggregates use the metric name; counts use 'count'. If that name is a
    grouping column, '_result' is appended until the result name is distinct.
    Grouped results also include group_size, counting all source rows per group.
    """
    result = {
        "success": False,
        "data": pd.DataFrame(),
        "source_rows": 0,
        "steps": [],
        "message": "",
    }
    steps = result["steps"]

    try:
        if plan.operation not in (
            Operation.COUNT, Operation.SUM, Operation.AVERAGE,
            Operation.MINIMUM, Operation.MAXIMUM,
        ):
            result["message"] = "Unsupported plans cannot be executed."
            return result

        working_df = df.copy()
        steps.append("Copied the source DataFrame.")

        for condition in plan.filters:
            column = working_df[condition.column]
            value = condition.value
            if condition.operator == FilterOperator.EQUALS:
                mask = column.isna() if value is None else column == value
            elif condition.operator == FilterOperator.NOT_EQUALS:
                mask = column.notna() if value is None else column != value
            elif condition.operator == FilterOperator.GREATER_THAN:
                mask = column > value
            elif condition.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
                mask = column >= value
            elif condition.operator == FilterOperator.LESS_THAN:
                mask = column < value
            elif condition.operator == FilterOperator.LESS_THAN_OR_EQUAL:
                mask = column <= value
            elif condition.operator == FilterOperator.CONTAINS:
                # Treat the search value as literal text, not a regular expression.
                mask = column.astype("string").str.contains(str(value), regex=False, na=False)
            else:
                raise ValueError("Unsupported filter operator.")

            if value is not None:
                mask = mask & column.notna()
            working_df = working_df.loc[mask.fillna(False)].copy()
            steps.append(
                f"Applied {condition.operator.value} filter on '{condition.column}'; "
                f"{len(working_df)} rows remain."
            )

        result["source_rows"] = len(working_df)
        if working_df.empty:
            result["success"] = True
            result["message"] = "No rows are available after filtering."
            steps.append("Stopped because there are no rows to analyze.")
            return result

        if plan.operation != Operation.COUNT and plan.metric is None:
            raise ValueError("This operation requires a metric.")

        result_column = "count" if plan.operation == Operation.COUNT else plan.metric
        while result_column in plan.group_by:
            result_column += "_result"

        if plan.group_by:
            # Keep groups with missing keys; omit unused categorical groups.
            grouped = working_df.groupby(plan.group_by, dropna=False, observed=True, sort=False)
            if plan.operation == Operation.COUNT:
                calculated = grouped.size()
            elif plan.operation == Operation.SUM:
                calculated = grouped[plan.metric].sum(min_count=1)
            elif plan.operation == Operation.AVERAGE:
                calculated = grouped[plan.metric].mean()
            elif plan.operation == Operation.MINIMUM:
                calculated = grouped[plan.metric].min()
            elif plan.operation == Operation.MAXIMUM:
                calculated = grouped[plan.metric].max()
            data = calculated.reset_index(name=result_column)
            data["group_size"] = grouped.size().to_numpy()
            steps.append("Grouped by: " + ", ".join(plan.group_by) + ".")
        else:
            if plan.operation == Operation.COUNT:
                calculated = len(working_df)
            elif plan.operation == Operation.SUM:
                calculated = working_df[plan.metric].sum(min_count=1)
            elif plan.operation == Operation.AVERAGE:
                calculated = working_df[plan.metric].mean()
            elif plan.operation == Operation.MINIMUM:
                calculated = working_df[plan.metric].min()
            elif plan.operation == Operation.MAXIMUM:
                calculated = working_df[plan.metric].max()
            data = pd.DataFrame({result_column: [calculated]})
        steps.append(f"Calculated {plan.operation.value} as '{result_column}'.")

        if plan.sort is not None:
            sort_column = plan.sort.column
            if sort_column == plan.metric and sort_column not in plan.group_by:
                sort_column = result_column
            data = data.sort_values(
                sort_column,
                ascending=plan.sort.direction == SortDirection.ASCENDING,
                kind="stable",
            )
            steps.append(f"Sorted '{sort_column}' {plan.sort.direction.value}.")

        if plan.limit is not None:
            data = data.head(plan.limit)
            steps.append(f"Limited the result to {plan.limit} rows.")

        result["data"] = data.reset_index(drop=True)
        result["success"] = True
        result["message"] = "Analysis completed."
    except Exception as error:
        # Keep execution failures in the same result structure for the caller.
        result["message"] = f"Analysis could not be completed: {error}"

    return result
