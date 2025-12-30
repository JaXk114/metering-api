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
