from sqlalchemy.orm import Session
import statistics

from app.db.models import Household, Consumption


def detect_household_anomalies(
    db: Session,
    household_id: str,
    z_threshold: float = 3.5
):
    """
    Detect anomalous consumption values for a household using
    a robust Median Absolute Deviation (MAD) approach.

    A value is considered anomalous if its modified Z-score
    exceeds the given threshold.
    """

    # 1. Find the household
    household = (
        db.query(Household)
        .filter(Household.household_id == household_id)
        .first()
    )

    if not household:
        return None

    # 2. Fetch all consumption rows for the household
    rows = (
        db.query(Consumption)
        .filter(Consumption.household_id == household.id)
        .all()
    )

    if len(rows) < 2:
        # Not enough data to establish a baseline
        return []

    values = [r.consumption_value for r in rows]

    # 3. Compute median
    median = statistics.median(values)

    # 4. Compute MAD (Median Absolute Deviation)
    abs_deviations = [abs(v - median) for v in values]
    mad = statistics.median(abs_deviations)

    if mad == 0:
        # All values identical → no anomalies possible
        return []

    anomalies = []

    # 5. Compute modified Z-score for each value
    for row in rows:
        modified_z_score = 0.6745 * (row.consumption_value - median) / mad

        if abs(modified_z_score) > z_threshold:
            anomalies.append({
                "date": row.consumption_date,
                "value": row.consumption_value,
                "score": round(modified_z_score, 2),
            })

    return anomalies
