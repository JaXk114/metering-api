from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import date
import logging

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.deps import get_db
from app.db.models import Household, Consumption

from app.schemas.consumption import HouseholdConsumption
from app.services.statistics import get_household_statistics
from app.services.anomalies import detect_household_anomalies



app = FastAPI(title="Metering Consumption API")
#Create all tables
Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metering-api")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


#simple health check endpoint
@app.get("/health")
def health_check():
    return {"status": "ok"}
 

# Endpoint to ingest consumption data
@app.post("/ingest")
def ingest_consumption(
    payload: HouseholdConsumption,
    db: Session = Depends(get_db),
):
    # Look up household by business identifier
    household = (
        db.query(Household)
        .filter(Household.household_id == payload.household_id)
        .first()
    )

    # Create household if new
    if not household:
        household = Household(
            household_id=payload.household_id,
            meter_point_id=str(payload.meter_point_id),
        )
        db.add(household)
        db.flush()  # ensures household.id is available

    # Store all consumption items
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
        "status": "stored",
    }


# Endpoint to get household statistics
@app.get("/statistics/household/{household_id}")
def household_statistics(
    household_id: str,
    db: Session = Depends(get_db),
):
    stats = get_household_statistics(db, household_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Household not found")
    return stats


# Endpoint to detect anomalies for a household
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


# Endpoint to list consumption with pagination and filters
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


# Endpoint to list all household IDs for UI selection
@app.get("/households")
def list_households(db: Session = Depends(get_db)):
    """
    Return all household IDs for UI selection.
    """
    households = db.query(Household.household_id).all()
    return [h[0] for h in households]
