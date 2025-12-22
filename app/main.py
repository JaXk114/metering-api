from fastapi import FastAPI
from app.db.base import Base
from app.db.session import engine
from app.schemas.consumption import HouseholdConsumption
from app.db.models import Household, Consumption
from app.db.session import SessionLocal


app = FastAPI(title="Metering Consumption API")

Base.metadata.create_all(bind=engine)


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

