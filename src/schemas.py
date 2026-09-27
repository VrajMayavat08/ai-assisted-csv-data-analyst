"""Allowed structure for an analysis plan."""

from enum import Enum

from pydantic import BaseModel, Field


class Operation(str, Enum):
    COUNT = "count"
    SUM = "sum"
    AVERAGE = "average"
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    UNSUPPORTED = "unsupported"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    SCATTER = "scatter"
    NONE = "none"


class FilterOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    CONTAINS = "contains"


class SortDirection(str, Enum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


class FilterCondition(BaseModel):
    column: str
    operator: FilterOperator
    value: str | int | float | bool | None


class SortConfig(BaseModel):
    column: str
    direction: SortDirection


class AnalysisPlan(BaseModel):
    operation: Operation
    metric: str | None = None
    group_by: list[str] = Field(default_factory=list)
    filters: list[FilterCondition] = Field(default_factory=list)
    sort: SortConfig | None = None
    limit: int | None = Field(default=None, gt=0)
    chart: ChartType
    reason: str | None = None
