"""
Utilitaires de gestion des fichiers — sauvegarde, validation, nettoyage.
"""
import os
import shutil
import asyncio
import logging
from pathlib import Path
from typing import BinaryIO

from app.config import (
    REPERTOIRE_TEMP,
    TAILLE_MAX_FICHIER_OCTETS,
    EXTENSIONS_AUTORISEES,
    TYPES_MIME_AUTORISES,
    DELAI_NETTOYAGE_SEC,
)

logger = logging.getLogger(__name__)


def obtenir_repertoire_temp() -> Path:
    """Retourne (et crée si besoin) le répertoire temporaire global."""
    REPERTOIRE_TEMP.mkdir(parents=True, exist_ok=True)
    return REPERTOIRE_TEMP


def sauvegarder_fichier_upload(source: BinaryIO, destination: str) -> None:
    """Copie un fichier uploadé sur le disque."""
    with open(destination, "wb") as f:
        shutil.copyfileobj(source, f)


def valider_extension_fichier(nom_fichier: str) -> bool:
    """Vérifie que l'extension du fichier est dans la liste autorisée."""
    extension = Path(nom_fichier).suffix.lower()
    return extension in EXTENSIONS_AUTORISEES


def valider_taille_fichier(taille: int) -> bool:
    """Vérifie que la taille du fichier est dans la limite autorisée."""
    return taille <= TAILLE_MAX_FICHIER_OCTETS


def detecter_type_fichier(nom_fichier: str) -> str:
    """Retourne un type simplifié : 'pdf', 'pptx', 'image' ou 'inconnu'."""
    extension = Path(nom_fichier).suffix.lower()
    if extension == ".pdf":
        return "pdf"
    elif extension == ".pptx":
        return "pptx"
    elif extension in (".png", ".jpg", ".jpeg"):
        return "image"
    return "inconnu"


def obtenir_extension(nom_fichier: str) -> str:
    """Retourne l'extension du fichier en minuscules."""
    return Path(nom_fichier).suffix.lower()


def valider_type_mime(mime_type: str | None) -> bool:
    """Vérifie que le type MIME est autorisé."""
    if not mime_type:
        return False
    return mime_type.lower() in TYPES_MIME_AUTORISES


def valider_signature_fichier(nom_fichier: str, contenu: bytes) -> bool:
    """Valide la signature binaire du fichier selon son extension."""
    extension = obtenir_extension(nom_fichier)

    if extension == ".pdf":
        return contenu.startswith(b"%PDF-")

    if extension == ".pptx":
        # Un PPTX est une archive ZIP OpenXML.
        return len(contenu) >= 4 and contenu[:2] == b"PK"

    if extension == ".png":
        return contenu.startswith(b"\x89PNG\r\n\x1a\n")

    if extension in (".jpg", ".jpeg"):
        return len(contenu) >= 3 and contenu[:3] == b"\xff\xd8\xff"

    return False


async def planifier_nettoyage(chemin: str, delai: int = DELAI_NETTOYAGE_SEC) -> None:
    """Supprime un fichier/dossier après *delai* secondes (fire-and-forget)."""
    await asyncio.sleep(delai)
    try:
        if os.path.isfile(chemin):
            os.remove(chemin)
            logger.info("Fichier temporaire nettoyé : %s", chemin)
        elif os.path.isdir(chemin):
            shutil.rmtree(chemin, ignore_errors=True)
            logger.info("Dossier temporaire nettoyé : %s", chemin)
    except Exception as erreur:
        logger.warning("Échec du nettoyage pour %s : %s", chemin, erreur)
