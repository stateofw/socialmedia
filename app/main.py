from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api import api_router
from app.api.routes import admin, signup, client_ui

# Templates
templates = Jinja2Templates(directory="app/templates")

# Add custom Jinja2 filters
def number_format(value):
    """Format number with commas for thousands."""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return value

templates.env.filters["number_format"] = number_format


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the application."""
    # Import models to ensure they're registered with Base
    from app import models  # noqa: F401

    # Startup: Initialize database
    await init_db()
    print("✅ Database initialized")
    yield
    # Shutdown: Cleanup
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Include admin UI routes
app.include_router(admin.router, prefix="/admin", tags=["admin-ui"])

# Include client UI routes
app.include_router(client_ui.router, prefix="/client", tags=["client-ui"])

# Include public signup routes
app.include_router(signup.router, prefix="/signup", tags=["signup"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Landing page."""
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENV,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
