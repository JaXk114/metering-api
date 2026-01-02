from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.schemas.consumption import HouseholdConsumption
from app.db.models import Household, Consumption
from app.db.session import SessionLocal
from app.services.statistics import get_household_statistics
from app.services.anomalies import detect_household_anomalies
from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging
from app.db.deps import get_db
from datetime import date




app = FastAPI(title="Metering Consumption API")

Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metering-api")


@app.get("/health")
def health_check():
    return {"status": "ok"}
 

@app.post("/ingest")
def ingest_consumption(payload: HouseholdConsumption):
    db = SessionLocal()
    try:
        household = (
            db.query(Household)
            .filter(Household.household_id == payload.household_id)
            .first()
        )

        if not household:
            household = Household(
                household_id=payload.household_id,
                meter_point_id=str(payload.meter_point_id)
            )
            db.add(household)
            db.flush()

        for item in payload.consumption:
            db.add(
                Consumption(
                    household_id=household.id,
                    consumption_type=item.consumption_type,
                    consumption_value=item.consumption_value,
                    consumption_date=item.consumption_date,
                )
            )

        db.commit()

        return {
            "household_id": payload.household_id,
            "meter_point_id": payload.meter_point_id,
            "items_received": len(payload.consumption),
            "status": "stored"
        }
    finally:
        db.close()




@app.get("/statistics/household/{household_id}")
def household_statistics(
    household_id: str,
    db: Session = Depends(get_db),
):
    stats = get_household_statistics(db, household_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Household not found")
    return stats



@app.get("/anomalies/household/{household_id}")
def household_anomalies(
    household_id: str,
    db: Session = Depends(get_db),
):
    anomalies = detect_household_anomalies(db, household_id)
    if anomalies is None:
        raise HTTPException(status_code=404, detail="Household not found")
    return {
        "household_id": household_id,
        "anomalies": anomalies
    }

@app.get("/consumption")
def list_consumption(
    household_id: str | None = Query(default=None),
    meter_point_id: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Paginated listing of consumption items with optional filters.
    """
    q = (
        db.query(Consumption, Household)
        .join(Household, Consumption.household_id == Household.id)
    )

    if household_id:
        q = q.filter(Household.household_id == household_id)

    if meter_point_id:
        q = q.filter(Household.meter_point_id == str(meter_point_id))

    if start_date:
        q = q.filter(Consumption.consumption_date >= start_date)

    if end_date:
        q = q.filter(Consumption.consumption_date <= end_date)

    total = q.count()

    rows = (
        q.order_by(Consumption.consumption_date.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [
        {
            "household_id": h.household_id,
            "meter_point_id": h.meter_point_id,
            "consumption_type": c.consumption_type,
            "consumption_value": c.consumption_value,
            "consumption_date": c.consumption_date,
        }
        for (c, h) in rows
    ]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }
