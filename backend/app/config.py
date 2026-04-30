"""
Configuration globale
"""
import os
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

# Limites
TAILLE_MAX_FICHIER_MO: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
TAILLE_MAX_FICHIER_OCTETS: int = TAILLE_MAX_FICHIER_MO * 1024 * 1024

# Dossier temporaire
REPERTOIRE_TEMP: Path = Path(os.getenv("TEMP_DIR", "/tmp/dinedi"))
REPERTOIRE_TEMP.mkdir(parents=True, exist_ok=True)

# Nettoyage
DELAI_NETTOYAGE_SEC: int = int(os.getenv("CLEANUP_DELAY_SEC", "30"))

# OpenCV
RAYON_INPAINTING: int = int(os.getenv("INPAINT_RADIUS", "3"))
RESOLUTION_DPI: int = int(os.getenv("RENDER_DPI", "300"))
MODE_DEBUG: bool = _env_bool("DEBUG_MODE", False)
ENABLE_DOCS: bool = _env_bool("ENABLE_DOCS", MODE_DEBUG)

# API
ORIGINES_AUTORISEES: list[str] = [
    origine.strip()
    for origine in os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if origine.strip()
]
ALLOWED_HOSTS: list[str] = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "*").split(",")
    if host.strip()
]
NOMBRE_WORKERS: int = int(os.getenv("WORKERS", "4"))
API_KEY: str | None = os.getenv("API_KEY")

# Fichiers permis
TYPES_MIME_AUTORISES: set[str] = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "image/png",
    "image/jpeg",
}
EXTENSIONS_AUTORISEES: set[str] = {".pdf", ".pptx", ".png", ".jpg", ".jpeg"}

# Zone du watermark (coin inferieur droit)
ZONE_WATERMARK = {
    "x_debut_pct": 0.88,
    "y_debut_pct": 0.97,
    "x_fin_pct": 1.00,
    "y_fin_pct": 1.00,
}

MARGE_DETECTION: int = int(os.getenv("MARGE_DETECTION", "2"))
 