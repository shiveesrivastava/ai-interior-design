from fastapi import FastAPI
from routes.generate import router as generate_router
from services.ml_services import load_pipeline
from utils.logger import get_logger
import asyncio

logger = get_logger("main")

app = FastAPI(
    title="RoomAI Backend",
    description="API for AI-powered interior design generation",
    version="0.1.0",
)
active_requests = 0

app.include_router(generate_router, prefix="/generate", tags=["Generate"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the backend...")
    load_pipeline()
    logger.info("Startup complete")

@app.get("/")
def root():
    return {"status": "ok", "message": "RoomAI backend is running"}

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down. Waiting for active requests.")

    while active_requests > 0:
        print(f"Waiting. {active_requests} request(s) still running")
        await asyncio.sleep(1)

    print("All requests completed. Shutdown safe.")

app.include_router(generate_router)