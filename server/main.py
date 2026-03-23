# -*- coding: utf-8 -*-
"""
AHDUNYI Terminal PRO - Backend API Server with multi-environment support

Author : AHDUNYI
Version: 9.1.0
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.api.auth import router as auth_router
from server.api.logs import router as logs_router
from server.api.permissions import router as permissions_router
from server.api.tasks import router as tasks_router
from server.api.team import router as team_router
from server.api.users import router as users_router
from server.api.violation import router as violation_router
from server.api.dynamic_roles import router as dynamic_roles_router
from server.core.config import config
from server.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    print(f"🚀 Starting {config.app_name} Backend...")
    print(f"📊 Environment: {config.environment.upper()}")
    print(f"🔧 Debug Mode: {config.debug}")
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables ready")
    
    yield
    
    # Shutdown
    print(f"👋 Shutting down {config.app_name} Backend...")


app = FastAPI(
    title=config.app_name,
    version=config.app_version,
    description=f"Backend API for {config.app_name} - {config.environment.upper()} Environment",
    lifespan=lifespan,
    docs_url="/docs" if config.enable_docs else None,
    redoc_url="/redoc" if config.enable_redoc else None,
)

# CORS middleware
if config.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to specific origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include routers
app.include_router(auth_router)
app.include_router(permissions_router)
app.include_router(users_router)
app.include_router(tasks_router)
app.include_router(team_router)
app.include_router(logs_router)
app.include_router(violation_router)
app.include_router(dynamic_roles_router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": config.app_name,
        "version": config.app_version,
        "environment": config.environment,
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.reload,
    )
