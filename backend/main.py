"""
Network Troubleshooting Assistant — FastAPI Application

Main entry point. Registers all routers, configures CORS,
and initializes the database on startup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db

# Import routers
from routers.auth import router as auth_router
from routers.analysis import router as analysis_router
from routers.scenarios import router as scenarios_router
from routers.reports import router as reports_router
from routers.dashboard import router as dashboard_router
from routers.admin import router as admin_router


# ── Lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    init_db()
    yield


# ── App creation ──────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Deterministic troubleshooting workbench for Cisco Packet Tracer labs with "
                "CLI capture analysis, evidence coverage, and prioritized fix planning.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router registration ──────────────────────────────────────

app.include_router(auth_router)
app.include_router(analysis_router)
app.include_router(scenarios_router)
app.include_router(reports_router)
app.include_router(dashboard_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "status": "running",
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


# ── Run directly ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=settings.DEBUG)
