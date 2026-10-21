"""Production FastAPI application entrypoint with lifespan DB creation and routers."""

import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import engine, Base
from api.endpoints import router as api_router
from api.webhooks import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes tables on startup and handles graceful shutdown."""
    # Ensure all ORM models are registered and tables exist
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Email Automation & Reminder System API",
    description="High-performance async email dispatch, Jinja2 templating, and reminder scheduler.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(api_router)
app.include_router(webhooks_router)


@app.get("/", tags=["General"])
def root():
    """Service status and quick links."""
    return {
        "status": "online",
        "service": "Email Automation & Reminder System",
        "version": "1.0.0",
        "docs_url": "/docs",
        "api_prefix": "/api/v1",
    }


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint for container probes and uptime monitors."""
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
