from fastapi import FastAPI

app = FastAPI(title="Metering Consumption API")

@app.get("/health")
def health_check():
    return {"status": "ok"}
