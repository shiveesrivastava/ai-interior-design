from fastapi import FastAPI
from routes.generate import router as generate_router

app = FastAPI(
    title="Backend",
    description="API for AI-powered interior design generation",
    version="0.1.0"
)

#Include the generate router
app.include_router(generate_router, prefix="/generate", tags=["Generate"])

@app.get("/")
def root():
    return {"status": "ok", "message": "RoomAI backend is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}