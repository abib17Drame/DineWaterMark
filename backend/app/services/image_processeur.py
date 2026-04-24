"""
Traitement d'images (PNG, JPG) — détection et suppression du watermark.

Pipeline :
1. Charger l'image en mémoire (OpenCV)
2. Détecter le watermark (zone fixe + analyse de contraste)
3. Reconstruire l'arrière-plan via inpainting
4. Exporter dans le même format que l'original
"""
import os
import logging
import time

import cv2
import numpy as np

from app.services.watermark.suppresseur import supprimer_watermark

logger = logging.getLogger(__name__)


def traiter_image(
    chemin_entree: str,
    chemin_sortie: str,
    mode_debug: bool = False,
    mode_watermark: str = "auto",
) -> dict:
    """
    Traite une image : supprime le watermark et la sauvegarde.

    Préserve :
    - La résolution originale
    - Le format original (PNG reste PNG, JPG reste JPG)
    - Les gradients et textures de fond

    Args:
        chemin_entree: Chemin vers l'image d'entrée
        chemin_sortie: Chemin vers l'image de sortie
        mode_debug: Activer les infos de debug

    Returns:
        Dictionnaire de statistiques
    """
    debut = time.time()

    # Chargement de l'image
    image = cv2.imread(chemin_entree, cv2.IMREAD_UNCHANGED)

    if image is None:
        raise ValueError(f"Impossible de charger l'image : {chemin_entree}")

    hauteur, largeur = image.shape[:2]
    a_canal_alpha = len(image.shape) == 3 and image.shape[2] == 4

    logger.info(
        "Image chargée : %s (%dx%d, alpha=%s)",
        os.path.basename(chemin_entree), largeur, hauteur, a_canal_alpha,
    )

    # Gérer le canal alpha séparément
    canal_alpha = None
    if a_canal_alpha:
        # Séparer le canal alpha avant traitement
        canal_alpha = image[:, :, 3]
        image_bgr = image[:, :, :3]
    else:
        image_bgr = image

    # Suppression du watermark
    image_nettoyee, infos_traitement = supprimer_watermark(
        image_bgr, mode_debug=mode_debug, mode_watermark=mode_watermark
    )

    # Recombiner le canal alpha si nécessaire
    if canal_alpha is not None:
        image_finale = cv2.merge([
            image_nettoyee[:, :, 0],
            image_nettoyee[:, :, 1],
            image_nettoyee[:, :, 2],
            canal_alpha,
        ])
    else:
        image_finale = image_nettoyee

    # Sauvegarder dans le même format
    extension = os.path.splitext(chemin_sortie)[1].lower()

    parametres_encodage = []
    if extension in (".jpg", ".jpeg"):
        # Qualité maximale pour JPEG (pas de dégradation)
        parametres_encodage = [cv2.IMWRITE_JPEG_QUALITY, 100]
    elif extension == ".png":
        # Compression PNG sans perte
        parametres_encodage = [cv2.IMWRITE_PNG_COMPRESSION, 1]

    succes = cv2.imwrite(chemin_sortie, image_finale, parametres_encodage)

    if not succes:
        raise RuntimeError(f"Échec de la sauvegarde de l'image : {chemin_sortie}")

    duree_ms = int((time.time() - debut) * 1000)

    resultat = {
        "status": "succes",
        "type_fichier": "image",
        "format": extension.lstrip("."),
        "dimensions": {"largeur": largeur, "hauteur": hauteur},
        "canal_alpha_preserve": a_canal_alpha,
        "temps_traitement_ms": duree_ms,
        **infos_traitement,
    }

    logger.info(
        "Image traitée avec succès en %dms — watermark=%s",
        duree_ms, "OUI" if infos_traitement.get("watermark_detecte") else "NON",
    )

    return resultat
 