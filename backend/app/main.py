"""FastAPI application entry point."""

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from app.core.config import settings
from app.db.database import engine, Base
from app.utils.logger import log_to_db, logger

# ── Import all routers ──
from app.api.v1 import (
    auth,
    chapters,
    documents,
    chat,
    assessment,
    system,
    agents,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: create all tables
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")
    yield
    # Shutdown: nothing special to clean up
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# ── CORS middleware ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost",
        "http://127.0.0.1",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Logging middleware ──
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log request details to system_logs table."""
    start_time = time.time()
    ip_address = request.client.host if request.client else "unknown"
    request_path = request.url.path

    # Try to extract user_id from request state (set by auth dependency)
    user_id = None
    try:
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id
    except Exception:
        pass

    response = None
    try:
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        log_to_db(
            level="INFO" if response.status_code < 400 else "WARNING",
            module="system",
            action=f"{request.method} {request_path}",
            message=f"{request.method} {request_path} -> {response.status_code} ({duration_ms}ms)",
            user_id=user_id,
            ip_address=ip_address,
            request_path=request_path,
            duration_ms=duration_ms,
        )
    except Exception as exc:
        duration_ms = int((time.time() - start_time) * 1000)
        log_to_db(
            level="ERROR",
            module="system",
            action=f"{request.method} {request_path}",
            message=f"Unhandled error: {str(exc)}",
            user_id=user_id,
            ip_address=ip_address,
            request_path=request_path,
            duration_ms=duration_ms,
        )
        # Re-raise so FastAPI handles it normally
        raise exc

    return response


# ── Health check ──
@app.get("/api/v1/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# ── Register all API routers ──
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(chapters.router, prefix="/api/v1/chapters", tags=["Chapters"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(assessment.router, prefix="/api/v1/assessment", tags=["Assessment"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
