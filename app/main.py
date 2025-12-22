from fastapi import FastAPI

from app.schemas.consumption import HouseholdConsumption

app = FastAPI(title="Metering Consumption API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/ingest")
def ingest_consumption(payload: HouseholdConsumption):
    """
    Ingest household consumption data.

    Validation is automatically enforced by Pydantic
    using the HouseholdConsumption schema.
    """
    return {
        "household_id": payload.household_id,
        "meter_point_id": payload.meter_point_id,
        "items_received": len(payload.consumption),
        "status": "accepted"
    }
