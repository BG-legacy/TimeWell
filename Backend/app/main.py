from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import db
from app.routers import auth, users

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

@app.on_event("startup")
async def startup_db_client():
    db.connect_to_database()

@app.on_event("shutdown")
async def shutdown_db_client():
    db.close_database_connection()

@app.get("/")
async def root():
    return {"message": "Welcome to TimeWell API"} 