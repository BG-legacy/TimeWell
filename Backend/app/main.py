from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import db
from app.routers import auth, users, goals, events, suggestions, habits, coach, voice_styles

app = FastAPI(
    title="TimeWell API",
    description="API for TimeWell application",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(goals.router)
app.include_router(events.router)
app.include_router(suggestions.router)
app.include_router(habits.router)
app.include_router(coach.router)
app.include_router(voice_styles.router)

@app.on_event("startup")
async def startup_db_client():
    db.connect_to_database()

@app.on_event("shutdown")
async def shutdown_db_client():
    db.close_database_connection()

@app.get("/")
async def root():
    return {"message": "Welcome to TimeWell API"} 