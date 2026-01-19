# ==============================================================================
# EXAM SCHEDULING PLATFORM - MAIN APPLICATION
# ==============================================================================
# This is the entry point of our FastAPI application.
# It sets up the app, middleware, and connects all the routers.
# ==============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.database import engine, Base

# Import routers
from app.routers import auth, departments, formations, professors, exams, scheduling, dashboard

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    This replaces the deprecated @app.on_event decorators.
    Code before 'yield' runs on startup, code after runs on shutdown.
    """
    # Startup: Create database tables if they don't exist
    # In production, you'd use Alembic migrations instead
    print("🚀 Starting Exam Scheduling Platform...")
    
    # Create tables on startup (Enabled for SQLite dev)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database connection established")
    print(f"📚 API Documentation: http://localhost:8000{settings.api_v1_prefix}/docs")
    
    yield  # Application runs here
    
    # Shutdown: Clean up resources
    print("👋 Shutting down...")
    await engine.dispose()
    print("✅ Database connections closed")


# Create the FastAPI application instance
app = FastAPI(
    title=settings.project_name,
    description="""
    ## 🎓 University Exam Scheduling Platform
    
    This API provides endpoints for managing university exam schedules, including:
    
    - **Departments & Formations**: Manage academic structure
    - **Students & Professors**: User management
    - **Modules & Enrollments**: Course management
    - **Exam Rooms**: Physical space management
    - **Exam Scheduling**: Automatic schedule generation
    - **Conflict Detection**: Find and resolve scheduling conflicts
    - **Statistics & KPIs**: Dashboard data and analytics
    
    ### Key Features:
    - 🤖 Automatic schedule optimization
    - ⚠️ Real-time conflict detection
    - 📊 Comprehensive statistics
    - 🔐 Role-based access control
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
)

# ==============================================================================
# MIDDLEWARE CONFIGURATION
# ==============================================================================

# CORS (Cross-Origin Resource Sharing)
# This allows our React frontend to make requests to the API from a different port/domain
app.add_middleware(
    CORSMiddleware,
    # List of origins allowed to make requests
    allow_origins=settings.cors_origins_list,
    # Allow cookies and authentication headers
    allow_credentials=True,
    # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    # Allow all headers
    allow_headers=["*"],
)


# ==============================================================================
# ROUTER REGISTRATION
# ==============================================================================
# Each router handles a specific domain of the application.
# The prefix ensures all routes start with /api/v1

app.include_router(
    auth.router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["Authentication"]
)

app.include_router(
    departments.router,
    prefix=f"{settings.api_v1_prefix}/departments",
    tags=["Departments"]
)

app.include_router(
    formations.router,
    prefix=f"{settings.api_v1_prefix}/formations",
    tags=["Formations"]
)

app.include_router(
    exams.router,
    prefix=f"{settings.api_v1_prefix}/exams",
    tags=["Exams"]
)

app.include_router(
    scheduling.router,
    prefix=f"{settings.api_v1_prefix}/scheduling",
    tags=["Scheduling"]
)

app.include_router(
    dashboard.router,
    prefix=f"{settings.api_v1_prefix}/dashboard",
    tags=["Dashboard"]
)

app.include_router(
    professors.router,
    prefix=f"{settings.api_v1_prefix}/professors",
    tags=["Professors"]
)


# ==============================================================================
# ROOT ENDPOINTS
# ==============================================================================

@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint - useful for health checks.
    
    Returns basic information about the API.
    """
    return {
        "message": "Welcome to the Exam Scheduling Platform API",
        "version": "1.0.0",
        "docs": f"{settings.api_v1_prefix}/docs",
        "status": "healthy"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring systems.
    
    This can be used by load balancers, Kubernetes, or monitoring tools
    to verify the application is running correctly.
    """
    return {
        "status": "healthy",
        "database": "connected",
        "api_version": "1.0.0"
    }


# ==============================================================================
# RUNNING THE APPLICATION
# ==============================================================================
# This block only runs when the file is executed directly (not when imported)

if __name__ == "__main__":
    import uvicorn
    
    # Run the application with hot reload for development
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,  # Enable hot reload only in debug mode
        log_level="info"
    )
