from fastapi import FastAPI

app = FastAPI(
    title="HACKSPIRE: LUMINA API",
    description="Backend API for HACKSPIRE: LUMINA event platform",
    version="0.1.0",
)

@app.get("/")
def root():
    return {"status": "ok"}