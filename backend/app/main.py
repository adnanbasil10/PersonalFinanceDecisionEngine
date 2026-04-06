"""
Personal Finance Decision Engine — FastAPI Application Entry Point.

Production-ready FastAPI app with:
- JWT authentication
- PostgreSQL/SQLite database
- ML-powered predictions
- Decision engine with explainability
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base, engine
from app.routes import auth, transactions, predictions, recommendations, explain


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown events."""
    # Startup: Create database tables
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.APP_ENV}")
    print(f"Database: {settings.effective_database_url[:50]}...")

    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified.")

    # Pre-load ML models into memory (if available)
    try:
        from app.ml.classifier import SpendingClassifier
        from app.ml.risk_predictor import OverspendRiskPredictor
        from app.ml.forecaster import SpendingForecaster

        SpendingClassifier.load()
        OverspendRiskPredictor.load()
        SpendingForecaster.load()
        print("ML models loaded successfully.")
    except Exception as e:
        print(f"ML models not loaded (run 'python -m app.ml.train' first): {e}")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "ML-powered personal finance decision engine. "
        "Predicts spending, detects risks, and recommends actionable decisions."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    """Welcome message for the API root."""
    return {
        "message": f"Welcome to the {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "active"
    }


# Health check
@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


# Register API routes
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(transactions.router, prefix=API_PREFIX)
app.include_router(predictions.router, prefix=API_PREFIX)
app.include_router(recommendations.router, prefix=API_PREFIX)
app.include_router(explain.router, prefix=API_PREFIX)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_DEBUG,
    )
