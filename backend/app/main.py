from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import batch, voice, live

app = FastAPI(
    title="MeetingToVikunja API",
    version="2.0.0",
    description="Backend API for processing meeting notes and syncing to Vikunja."
)

# CORS Configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(batch.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
app.include_router(live.router, prefix="/api/v1/voice", tags=["Voice (Live)"])
# app.include_router(vikunja.router, prefix="/api/v1", tags=["Vikunja"]) # Placeholder/Commented out for Phase 1

@app.get("/health")
async def health_check():
    return {"status": "ok"}
