from datetime import date
from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class ConsumptionType(str, Enum):
    """
    Allowed consumption types as defined by the API contract.
    """
    Import = "Import"
    Export = "Export"


class ConsumptionItem(BaseModel):
    """
    Represents a single consumption entry for a given day.
    """
    consumption_type: ConsumptionType = Field(
        ...,
        description="Whether the consumption is Import or Export"
    )
    consumption_value: float = Field(
        ...,
        gt=0,
        description="Consumption value (must be greater than 0)"
    )
    consumption_date: date = Field(
        ...,
        description="Date of consumption in YYYY-MM-DD format"
    )


class HouseholdConsumption(BaseModel):
    """
    Represents the full payload for a household's meter readings.
    This matches the JSON schema provided in the task description.
    """
    household_id: str = Field(
        ...,
        min_length=10,
        max_length=10,
        pattern="^[A-Za-z0-9]+$",
        description="10-character alphanumeric household ID"
    )

    meter_point_id: int = Field(
        ...,
        ge=10**12,
        lt=10**13,
        description="13-digit meter point identifier"
    )
    consumption: List[ConsumptionItem] = Field(
        ...,
        min_length=1,
        description="List of consumption records"
    )
