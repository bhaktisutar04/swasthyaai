from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from routes.auth import router as auth_router

# These routers will be added in later sprints:
from routes.consultation import router as consultation_router
from routes.nutrition import router as nutrition_router
from routes.finance import router as finance_router
from routes.history import router as history_router
from routes.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    init_db()
    yield
    # Shutdown logic
    pass

app = FastAPI(
    title="SwasthyaAI API",
    version="1.0",
    description="AI-powered health companion for Indian patients",
    lifespan=lifespan
)

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "https://bhaktisutar04.github.io",
    "https://bhaktisutar04.github.io/swasthyaai",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)

# Registering routers (Sprint 1)
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(consultation_router, prefix="/consultation", tags=["Consultation"])
app.include_router(nutrition_router, prefix="/nutrition", tags=["Nutrition"])
app.include_router(finance_router, prefix="/finance", tags=["Finance"])
app.include_router(history_router, prefix="/history", tags=["History"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])

@app.get("/health")
def health_check():
    return {
        "status": "ok", 
        "service": "SwasthyaAI", 
        "version": "1.0"
    }


