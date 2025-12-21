from fastapi import FastAPI
from app.schemas.consumption import HouseholdConsumption




app = FastAPI(title="Metering Consumption API")

@app.get("/health")
def health_check():
    return {"status": "ok"}
