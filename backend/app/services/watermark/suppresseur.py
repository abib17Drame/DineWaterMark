"""
Suppression du watermark par inpainting OpenCV.

Strategie : on ne touche QUE les pixels du watermark dans la zone
etroite du coin inferieur droit.
Deux algorithmes :
- INPAINT_TELEA  : reconstruction naturelle (gradients + textures)
- Colonne par colonne : interpolation lineaire (fonds simples)
"""
import cv2
import numpy as np
import logging

from app.config import RAYON_INPAINTING
from app.services.watermark.detecteur import (
    detecter_watermark,
    detecter_watermark_selon_mode,
)
from app.services.watermark.gemini_math import supprimer_watermark_gemini_math

logger = logging.getLogger(__name__)


def creer_masque_watermark(
    image: np.ndarray,
    info_watermark: dict,
) -> np.ndarray:
    """
    Cree un masque binaire PRECIS de la zone du watermark.

    On isole uniquement les pixels sombres (texte/logo du watermark)
    dans la zone detectee, sans deborder sur le contenu autour.
    """
    hauteur_img, largeur_img = image.shape[:2]
    masque = np.zeros((hauteur_img, largeur_img), dtype=np.uint8)

    x = info_watermark["x"]
    y = info_watermark["y"]
    w = info_watermark["largeur"]
    h = info_watermark["hauteur"]

    # Extraire la zone du watermark
    zone = image[y:y+h, x:x+w]
    if zone.size == 0:
        return masque

    # Convertir en gris
    gris = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)

    # Le watermark NotebookLM est noir/gris fonce.
    _, masque_local = cv2.threshold(
        gris, 180, 255, cv2.THRESH_BINARY_INV
    )

    # DILATATION FORTE : C'est la cle pour que ca ne soit pas juste "floute".
    # Il faut que le masque deborde legerement au-dela des lettres grises 
    # pour que l'inpainting OpenCV les efface completement.
    noyau = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    masque_local = cv2.morphologyEx(masque_local, cv2.MORPH_CLOSE, noyau, iterations=2)
    masque_local = cv2.dilate(masque_local, noyau, iterations=3)

    # Placer le masque local dans le masque global
    masque[y:y+h, x:x+w] = masque_local

    return masque


def supprimer_watermark(
    image: np.ndarray,
    mode_debug: bool = False,
    rayon: int = None,
    mode_watermark: str = "auto",
) -> tuple[np.ndarray, dict]:
    """
    Pipeline complet : detection -> masque -> inpainting.

    Retourne (image_nettoyee, infos_traitement).
    """
    # Rayon par defaut configurable via l'environnement.
    rayon_inpaint = rayon or RAYON_INPAINTING

    mode_selection = (mode_watermark or "auto").lower().strip()

    # Detection
    info_watermark = detecter_watermark_selon_mode(
        image, mode_selection=mode_selection, mode_debug=mode_debug
    )

    if info_watermark is None:
        logger.info("Aucun watermark trouve -- image retournee intacte")
        return image.copy(), {
            "watermark_detecte": False,
            "message": "Aucun watermark detecte",
        }

    # Pour Gemini, preferer l'inversion mathematique (plus propre que l'inpainting).
    if info_watermark.get("source") == "gemini":
        try:
            image_math, infos_math = supprimer_watermark_gemini_math(image)

            # Deuxième passe: certains documents contiennent aussi le texte NotebookLM.
            # On retire ce résidu après l'inversion Gemini si détecté.
            if mode_selection != "gemini":
                info_residuel = detecter_watermark(image_math, mode_debug)
                if info_residuel is not None:
                    masque_residuel = creer_masque_watermark(image_math, info_residuel)
                    pixels_residuels = int(np.count_nonzero(masque_residuel))
                    if pixels_residuels > 0:
                        image_math = cv2.inpaint(
                            image_math, masque_residuel, rayon_inpaint, cv2.INPAINT_TELEA
                        )
                        infos_math["notebook_residuel_corrige"] = True
                        infos_math["pixels_residuels_corriges"] = pixels_residuels

            if mode_debug and "debug" in info_watermark:
                infos_math["debug_detection"] = info_watermark["debug"]
            return image_math, infos_math
        except Exception as erreur:
            logger.warning("Fallback inpainting Gemini (math indisponible): %s", erreur)

    # Creation du masque
    masque = creer_masque_watermark(image, info_watermark)

    # Verifier que le masque contient des pixels actifs
    pixels_actifs = np.count_nonzero(masque)
    if pixels_actifs == 0:
        # Fallback : masque rectangulaire simple sur la zone exacte
        logger.warning("Masque vide apres analyse -- rectangle simple")
        x = info_watermark["x"]
        y = info_watermark["y"]
        w = info_watermark["largeur"]
        h = info_watermark["hauteur"]
        masque[y:y+h, x:x+w] = 255

    rayon_effectif = rayon_inpaint

    # Inpainting
    image_nettoyee = cv2.inpaint(
        image, masque, rayon_effectif, cv2.INPAINT_TELEA
    )

    infos = {
        "watermark_detecte": True,
        "watermark_source": info_watermark.get("source", "notebooklm"),
        "position": {
            "x": info_watermark["x"],
            "y": info_watermark["y"],
            "largeur": info_watermark["largeur"],
            "hauteur": info_watermark["hauteur"],
        },
        "confiance": info_watermark.get("confiance", 0),
        "pixels_corriges": int(pixels_actifs),
        "rayon_inpainting": rayon_effectif,
    }

    if mode_debug and "debug" in info_watermark:
        infos["debug"] = info_watermark["debug"]

    logger.info(
        "Watermark supprime -- %d pixels corriges (rayon=%d)",
        pixels_actifs, rayon_inpaint,
    )

    return image_nettoyee, infos


def supprimer_watermark_colonne_par_colonne(
    image: np.ndarray,
    info_watermark: dict,
) -> np.ndarray:
    """
    Algorithme alternatif : reconstruction colonne par colonne.
    Interpole entre les pixels au-dessus et en-dessous du watermark.
    Efficace pour les fonds unis ou degrades verticaux.
    """
    resultat = image.copy()
    x = info_watermark["x"]
    y = info_watermark["y"]
    w = info_watermark["largeur"]
    h = info_watermark["hauteur"]

    hauteur_img = image.shape[0]

    for col in range(x, min(x + w, image.shape[1])):
        y_haut = max(0, y - 1)
        y_bas = min(hauteur_img - 1, y + h)

        pixel_haut = image[y_haut, col].astype(np.float32)
        pixel_bas = image[y_bas, col].astype(np.float32)

        for ligne in range(y, min(y + h, hauteur_img)):
            ratio = (ligne - y) / max(h, 1)
            pixel_interpole = pixel_haut * (1 - ratio) + pixel_bas * ratio
            resultat[ligne, col] = pixel_interpole.astype(np.uint8)

    return resultat
 