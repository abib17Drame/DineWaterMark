"""
Point d'entrée FastAPI DineDiWaterMark API

Configure le serveur, le CORS, le logging et monte les routes.
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import ORIGINES_AUTORISEES, MODE_DEBUG
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
    docs_url="/docs",
    redoc_url="/redoc",
)

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
 