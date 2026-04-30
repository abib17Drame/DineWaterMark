"""
Point d'entrée FastAPI DineDiWaterMark API

Configure le serveur, le CORS, le logging et monte les routes.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import ORIGINES_AUTORISEES, ALLOWED_HOSTS, ENABLE_DOCS, MODE_DEBUG
from app.routers import api

# Logging
logging.basicConfig(
    level=logging.DEBUG if MODE_DEBUG else logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("dinedi")

# Application FastAPI
app = FastAPI(
    title="DineDiWaterMark API",
    description=(
        "API de suppression de watermarks NotebookLM "
        "pour fichiers PDF, PPTX et images (PNG/JPG)."
    ),
    version="1.0.0",
    docs_url="/docs" if ENABLE_DOCS else None,
    redoc_url="/redoc" if ENABLE_DOCS else None,
    openapi_url="/openapi.json" if ENABLE_DOCS else None,
)

if ALLOWED_HOSTS and "*" not in ALLOWED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

# Middleware CORS
origines = ORIGINES_AUTORISEES or ["*"]
credentials_autorises = "*" not in origines

app.add_middleware(
    CORSMiddleware,
    allow_origins=origines,
    allow_credentials=credentials_autorises,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ajouter_entetes_securite(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Permissions-Policy",
        "camera=(), microphone=(), geolocation=()",
    )
    return response

# Routes
app.include_router(api.routeur, prefix="/api/v1")


# Health check
@app.get("/api/v1/health", tags=["Santé"])
async def verification_sante():
    """Vérifie que le service est opérationnel."""
    return {"status": "ok", "service": "DineDiWaterMark", "version": "1.0.0"}


@app.on_event("startup")
async def au_demarrage():
    logger.info("🚀 DineDiWaterMark API démarrée")


@app.on_event("shutdown")
async def a_larret():
    logger.info("🛑 DineDiWaterMark API arrêtée")
 