from fastapi import FastAPI
from routes import generate as generate_routes
from services.ml_services import load_pipeline
from utils.logger import get_logger
import asyncio

logger = get_logger("main")

app = FastAPI(
    title="RoomAI Backend",
    description="API for AI-powered interior design generation",
    version="0.1.0",
)

app.include_router(generate_routes.router, tags=["Generate"])

@app.middleware("http")
async def track_active_generation_requests(request, call_next):
    if request.method == "POST" and request.url.path == "/generate/":
        generate_routes.active_requests += 1
        try:
            response = await call_next(request)
            return response
        finally:
            generate_routes.active_requests -= 1

    return await call_next(request)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the backend.")
    load_pipeline()
    logger.info("Startup complete")

@app.get("/")
def root():
    return {"status": "ok", "message": "RoomAI backend is running"}

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down. Waiting for active requests.")

    while generate_routes.active_requests > 0:
        print(
            f"Waiting. {generate_routes.active_requests} "
            "request(s) still running"
        )
        await asyncio.sleep(1)

    print("All requests completed. Shutdown safe.")
