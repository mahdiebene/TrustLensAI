"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.health import router as health_router
from app.api.analyze import router as analyze_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown events."""
    # Startup
    settings = get_settings()
    print(f"[TrustLens] Starting in {settings.APP_ENV} mode")
    print(f"[TrustLens] Pollinations API: {settings.POLLINATIONS_BASE_URL}")
    yield
    # Shutdown
    print("[TrustLens] Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="TrustLens API",
    description="AI-Powered Trust Scoring Platform for Bengali Social Media",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting — single shared instance
# Import the limiter from analyze.py so it's the same instance
from app.api.analyze import limiter  # noqa: E402

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://trustlens.vercel.app",
        "http://localhost:3000",
        settings.APP_URL,
    ],
    # Allow the Chrome extension (chrome-extension://<id>) and any *.vercel.app
    # preview deployment to call the API.
    allow_origin_regex=r"^(chrome-extension://.*|https://.*\.vercel\.app)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(analyze_router, prefix="/api", tags=["analyze"])
