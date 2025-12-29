from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import Household, Consumption

def get_household_statistics(
    db: Session,
    household_id: str
):
    household = (
        db.query(Household)
        .filter(Household.household_id == household_id)
        .first()
    )

    if not household:
        return None

    total = (
        db.query(func.sum(Consumption.consumption_value))
        .filter(Consumption.household_id == household.id)
        .scalar()
    )

    mean = (
        db.query(func.avg(Consumption.consumption_value))
        .filter(Consumption.household_id == household.id)
        .scalar()
    )

    peak = (
        db.query(Consumption.consumption_date, Consumption.consumption_value)
        .filter(Consumption.household_id == household.id)
        .order_by(Consumption.consumption_value.desc())
        .first()
    )

    return {
        "household_id": household.household_id,
        "total_consumption": total,
        "mean_consumption": mean,
        "peak_day": peak.consumption_date if peak else None,
        "peak_value": peak.consumption_value if peak else None,
    }
