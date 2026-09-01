import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from app.core.config import settings
from app.core.middleware import RateLimitMiddleware
from app.db.mongo import db_manager
from app.api.routes.router import api_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB Atlas (fails gracefully)
    db_manager.connect()
    yield
    # Shutdown: Close MongoDB client connection
    db_manager.close()


app = FastAPI(
    title="Smart Attendance API",
    description="Backend API for AI-Based Smart Attendance & Student Analytics System",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT == "development" else None,
)

# 1. Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware)

# 2. Dynamic Configurable CORS Middleware
cors_origins = settings.get_cors_origins_list()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 3. Global Exception Handler (Prevents stack trace / secret leakage)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    
    # In production, do not expose internal exception details
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact the administrator."},
    )

# Register main API router under /api
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "Smart Attendance API is active",
        "health_check": "/api/health",
        "environment": settings.ENVIRONMENT,
    }
