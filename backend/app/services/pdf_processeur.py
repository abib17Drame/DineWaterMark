"""
Traitement PDF : rendu → détection → inpainting → reconstruction.

Pipeline :
1. Ouvrir le PDF avec PyMuPDF
2. Rendre chaque page en image haute résolution (300 DPI)
3. Détecter et supprimer le watermark sur chaque image
4. Reconstruire un PDF à partir des images patchées
"""
import os
import logging
import base64
import time
from pathlib import Path

import fitz  # PyMuPDF
import cv2
import numpy as np
import img2pdf
from PIL import Image

from app.config import RESOLUTION_DPI
from app.services.watermark.suppresseur import supprimer_watermark

logger = logging.getLogger(__name__)


def traiter_pdf(
    chemin_entree: str,
    chemin_sortie: str,
    mode_debug: bool = False,
    callback_progression: callable = None,
    mode_watermark: str = "auto",
) -> dict:
    """
    Traite un fichier PDF : supprime le watermark de chaque page.

    Args:
        chemin_entree: Chemin vers le PDF d'entrée
        chemin_sortie: Chemin vers le PDF de sortie (nettoyé)
        mode_debug: Activer les infos de debug
        callback_progression: Fonction(page_courante, total_pages) pour le suivi

    Returns:
        Dictionnaire avec les statistiques de traitement
    """
    debut = time.time()
    document = fitz.open(chemin_entree)
    nombre_pages = len(document)

    logger.info(
        "Début du traitement PDF : %s (%d pages)",
        os.path.basename(chemin_entree), nombre_pages,
    )

    images_nettoyees = []
    resultats_pages = []
    pages_avec_watermark = 0

    repertoire_temp = Path(chemin_sortie).parent / f"_temp_pages_{os.getpid()}"
    repertoire_temp.mkdir(parents=True, exist_ok=True)

    try:
        for numero_page in range(nombre_pages):
            page = document[numero_page]

            # Rendu haute résolution
            matrice = fitz.Matrix(RESOLUTION_DPI / 72, RESOLUTION_DPI / 72)
            pixmap = page.get_pixmap(matrix=matrice, alpha=False)

            # Convertir le pixmap PyMuPDF en array NumPy (BGR pour OpenCV)
            donnees = pixmap.samples
            image_np = np.frombuffer(donnees, dtype=np.uint8).reshape(
                pixmap.height, pixmap.width, 3
            )
            image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

            # Suppression du watermark
            image_nettoyee, infos_page = supprimer_watermark(
                image_bgr, mode_debug=mode_debug, mode_watermark=mode_watermark
            )

            if infos_page.get("watermark_detecte"):
                pages_avec_watermark += 1

            resultats_pages.append({
                "page": numero_page + 1,
                **infos_page,
            })

            # Sauvegarder l'image temporaire en PNG (lossless)
            image_rgb = cv2.cvtColor(image_nettoyee, cv2.COLOR_BGR2RGB)
            chemin_image_temp = str(repertoire_temp / f"page_{numero_page:04d}.png")

            img_pil = Image.fromarray(image_rgb)
            img_pil.save(chemin_image_temp, format="PNG")
            images_nettoyees.append(chemin_image_temp)

            # Callback de progression
            if callback_progression:
                # Créer une miniature très légère pour le frontend (300px large)
                try:
                    h, w = image_bgr.shape[:2]
                    ratio = 300 / w
                    dim = (300, int(h * ratio))
                    
                    small_orig = cv2.resize(image_bgr, dim, interpolation=cv2.INTER_AREA)
                    _, buf_orig = cv2.imencode('.jpg', small_orig, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    b64_orig = base64.b64encode(buf_orig).decode('utf-8')
                    
                    small_nette = cv2.resize(image_nettoyee, dim, interpolation=cv2.INTER_AREA)
                    _, buf_nette = cv2.imencode('.jpg', small_nette, [cv2.IMWRITE_JPEG_QUALITY, 50])
                    b64_nette = base64.b64encode(buf_nette).decode('utf-8')
                    
                    callback_progression(numero_page + 1, nombre_pages, b64_orig, b64_nette)
                except Exception as e:
                    logger.error(f"Erreur preview base64: {e}")
                    callback_progression(numero_page + 1, nombre_pages)

            logger.info(
                "Page %d/%d traitée (watermark=%s)",
                numero_page + 1, nombre_pages,
                "OUI" if infos_page.get("watermark_detecte") else "NON",
            )

        document.close()

        # Reconstruction du PDF à partir des images
        reconstruire_pdf_depuis_images(images_nettoyees, chemin_sortie)

        duree_ms = int((time.time() - debut) * 1000)

        resultat_global = {
            "status": "succes",
            "type_fichier": "pdf",
            "nombre_pages": nombre_pages,
            "pages_avec_watermark": pages_avec_watermark,
            "temps_traitement_ms": duree_ms,
            "details_pages": resultats_pages if mode_debug else None,
        }

        logger.info(
            "PDF traité avec succès en %dms — %d/%d pages avec watermark",
            duree_ms, pages_avec_watermark, nombre_pages,
        )

        return resultat_global

    finally:
        # Nettoyage des fichiers temporaires
        import shutil
        if repertoire_temp.exists():
            shutil.rmtree(repertoire_temp, ignore_errors=True)


def reconstruire_pdf_depuis_images(
    chemins_images: list[str],
    chemin_sortie: str,
) -> None:
    """
    Reconstruit un PDF à partir d'une liste d'images PNG (lossless via img2pdf).

    Préserve la résolution originale sans recompression.
    """
    with open(chemin_sortie, "wb") as fichier_pdf:
        fichier_pdf.write(img2pdf.convert(chemins_images))

    logger.info(
        "PDF reconstruit : %s (%d pages)",
        os.path.basename(chemin_sortie), len(chemins_images),
    )


def extraire_apercu_page(
    chemin_pdf: str,
    numero_page: int = 0,
    dpi: int = 150,
) -> np.ndarray:
    """
    Extrait une page spécifique du PDF en image (pour l'aperçu avant/après).

    Args:
        chemin_pdf: Chemin vers le PDF
        numero_page: Numéro de la page (0-indexé)
        dpi: Résolution de l'aperçu

    Returns:
        Image BGR (NumPy array)
    """
    document = fitz.open(chemin_pdf)
    page = document[numero_page]
    matrice = fitz.Matrix(dpi / 72, dpi / 72)
    pixmap = page.get_pixmap(matrix=matrice, alpha=False)

    donnees = pixmap.samples
    image_np = np.frombuffer(donnees, dtype=np.uint8).reshape(
        pixmap.height, pixmap.width, 3
    )
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    document.close()
    return image_bgr
  