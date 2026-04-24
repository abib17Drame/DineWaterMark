"""
Détection du watermark NotebookLM par analyse de contraste local
et différence de flou (OpenCV).

Le watermark NotebookLM est un petit logo + texte "NotebookLM" situé
dans le coin inférieur droit de chaque page/slide.
"""
import cv2
import numpy as np
import logging

from app.config import ZONE_WATERMARK, MARGE_DETECTION, MODE_DEBUG

logger = logging.getLogger(__name__)


def detecter_watermark(image: np.ndarray, mode_debug: bool = False) -> dict | None:
    """
    Détecte la présence et la position du watermark NotebookLM dans une image.

    Stratégie :
    1. Extraire la zone candidate (coin inférieur droit ~20% x 7%)
    2. Convertir en niveaux de gris
    3. Appliquer un seuillage adaptatif pour isoler les éléments sombres/texte
    4. Trouver les contours et vérifier si le motif correspond à un watermark

    Args:
        image: Image BGR (format OpenCV)
        mode_debug: Si True, retourne les coordonnées détaillées

    Returns:
        Dictionnaire avec les coordonnées du watermark ou None si non détecté
    """
    hauteur, largeur = image.shape[:2]

    # Étape 1 : Définir la zone candidate
    x_debut = int(largeur * ZONE_WATERMARK["x_debut_pct"])
    y_debut = int(hauteur * ZONE_WATERMARK["y_debut_pct"])
    x_fin = int(largeur * ZONE_WATERMARK["x_fin_pct"])
    y_fin = int(hauteur * ZONE_WATERMARK["y_fin_pct"])

    zone_candidate = image[y_debut:y_fin, x_debut:x_fin]

    if zone_candidate.size == 0:
        logger.warning("Zone candidate vide — dimensions image trop petites")
        return None

    # Étape 2 : Convertir en niveaux de gris
    gris = cv2.cvtColor(zone_candidate, cv2.COLOR_BGR2GRAY)

    # Étape 3 : Analyse par différence de flou
    # Un watermark se distingue par un contraste local net
    flou_leger = cv2.GaussianBlur(gris, (3, 3), 0)
    flou_fort = cv2.GaussianBlur(gris, (21, 21), 0)
    difference_flou = cv2.absdiff(flou_leger, flou_fort)

    # Étape 4 : Seuillage pour isoler le watermark
    _, masque_binaire = cv2.threshold(
        difference_flou, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Étape 5 : Trouver les contours dans le masque
    contours, _ = cv2.findContours(
        masque_binaire, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        logger.info("Aucun watermark détecté dans la zone candidate")
        return None

    # Fusionner tous les contours pour obtenir le bounding box global
    tous_les_points = np.concatenate(contours)
    x_local, y_local, w_local, h_local = cv2.boundingRect(tous_les_points)

    # Vérifier que la zone détectée a une taille raisonnable pour un watermark
    surface_zone = w_local * h_local
    surface_candidate = zone_candidate.shape[0] * zone_candidate.shape[1]
    ratio_surface = surface_zone / surface_candidate if surface_candidate > 0 else 0

    # Le watermark NotebookLM occupe typiquement entre 5% et 80% de la zone candidate
    if ratio_surface < 0.03 or ratio_surface > 0.95:
        logger.info(
            "Zone détectée hors proportions attendues (ratio=%.2f)", ratio_surface
        )
        return None

    # Convertir en coordonnées globales (image complète)
    x_global = x_debut + x_local - MARGE_DETECTION
    y_global = y_debut + y_local - MARGE_DETECTION
    w_global = w_local + 2 * MARGE_DETECTION
    h_global = h_local + 2 * MARGE_DETECTION

    # S'assurer qu'on ne dépasse pas les bords de l'image
    x_global = max(0, x_global)
    y_global = max(0, y_global)
    w_global = min(w_global, largeur - x_global)
    h_global = min(h_global, hauteur - y_global)

    resultat = {
        "detecte": True,
        "x": x_global,
        "y": y_global,
        "largeur": w_global,
        "hauteur": h_global,
        "confiance": round(ratio_surface, 3),
    }

    if mode_debug or MODE_DEBUG:
        resultat["debug"] = {
            "zone_candidate": {
                "x_debut": x_debut,
                "y_debut": y_debut,
                "x_fin": x_fin,
                "y_fin": y_fin,
            },
            "nombre_contours": len(contours),
            "ratio_surface": round(ratio_surface, 4),
            "masque_pixels_actifs": int(np.count_nonzero(masque_binaire)),
        }

    logger.info(
        "Watermark détecté à (%d, %d) taille %dx%d (confiance=%.3f)",
        x_global, y_global, w_global, h_global, ratio_surface,
    )

    return resultat


def detecter_watermark_avance(image: np.ndarray, mode_debug: bool = False) -> dict | None:
    """
    Détection avancée combinant plusieurs méthodes :
    1. Analyse de contraste local (méthode principale)
    2. Template matching si un modèle du watermark est disponible
    3. Analyse morphologique pour affiner le masque

    Retombe sur la méthode simple si la détection avancée échoue.
    """
    # Détection standard NotebookLM en priorité.
    # Sur les exports NotebookLM (PDF/PPTX), le cas majoritaire est le watermark texte.
    resultat = detecter_watermark(image, mode_debug)

    if resultat is not None:
        resultat["source"] = "notebooklm"
        return resultat

    # Fallback Gemini ensuite.
    # Évite de classer à tort un watermark NotebookLM comme "gemini".
    resultat_gemini = detecter_watermark_gemini(image, mode_debug)
    if resultat_gemini is not None:
        return resultat_gemini

    # Méthode alternative : analyse morphologique étendue
    # Étendre la zone de recherche en cas de watermark décalé
    hauteur, largeur = image.shape[:2]

    zones_alternatives = [
        # Bas-centre
        {"x_debut_pct": 0.30, "y_debut_pct": 0.92, "x_fin_pct": 0.70, "y_fin_pct": 1.00},
        # Bas-gauche
        {"x_debut_pct": 0.00, "y_debut_pct": 0.93, "x_fin_pct": 0.20, "y_fin_pct": 1.00},
        # Bas complet
        {"x_debut_pct": 0.00, "y_debut_pct": 0.90, "x_fin_pct": 1.00, "y_fin_pct": 1.00},
    ]

    for zone in zones_alternatives:
        x_debut = int(largeur * zone["x_debut_pct"])
        y_debut = int(hauteur * zone["y_debut_pct"])
        x_fin = int(largeur * zone["x_fin_pct"])
        y_fin = int(hauteur * zone["y_fin_pct"])

        zone_candidate = image[y_debut:y_fin, x_debut:x_fin]
        if zone_candidate.size == 0:
            continue

        gris = cv2.cvtColor(zone_candidate, cv2.COLOR_BGR2GRAY)

        # Utiliser un seuillage adaptatif
        masque = cv2.adaptiveThreshold(
            gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Opérations morphologiques pour nettoyer le bruit
        noyau = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        masque = cv2.morphologyEx(masque, cv2.MORPH_CLOSE, noyau, iterations=2)
        masque = cv2.morphologyEx(masque, cv2.MORPH_OPEN, noyau, iterations=1)

        contours, _ = cv2.findContours(
            masque, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Filtrer les contours trop petits
        contours_valides = [c for c in contours if cv2.contourArea(c) > 50]

        if not contours_valides:
            continue

        tous_les_points = np.concatenate(contours_valides)
        x_local, y_local, w_local, h_local = cv2.boundingRect(tous_les_points)

        x_global = x_debut + x_local - MARGE_DETECTION
        y_global = y_debut + y_local - MARGE_DETECTION
        w_global = w_local + 2 * MARGE_DETECTION
        h_global = h_local + 2 * MARGE_DETECTION

        x_global = max(0, x_global)
        y_global = max(0, y_global)
        w_global = min(w_global, largeur - x_global)
        h_global = min(h_global, hauteur - y_global)

        logger.info(
            "Watermark détecté (méthode alternative) à (%d, %d) taille %dx%d",
            x_global, y_global, w_global, h_global,
        )

        return {
            "detecte": True,
            "x": x_global,
            "y": y_global,
            "largeur": w_global,
            "hauteur": h_global,
            "confiance": 0.6,
            "methode": "alternative",
        }

    logger.info("Aucun watermark détecté avec les méthodes alternatives")
    return None


def detecter_watermark_selon_mode(
    image: np.ndarray,
    mode_selection: str = "auto",
    mode_debug: bool = False,
) -> dict | None:
    """
    Détection avec sélection explicite de la source watermark.

    mode_selection:
    - auto: détection avancée combinée
    - notebook: détection NotebookLM uniquement
    - gemini: détection Gemini uniquement
    """
    mode = (mode_selection or "auto").lower().strip()

    if mode == "notebook":
        resultat = detecter_watermark(image, mode_debug)
        if resultat is not None:
            resultat["source"] = "notebooklm"
        return resultat

    if mode == "gemini":
        return detecter_watermark_gemini(image, mode_debug)

    return detecter_watermark_avance(image, mode_debug)


def detecter_watermark_gemini(image: np.ndarray, mode_debug: bool = False) -> dict | None:
    """
    Détection heuristique du watermark visible Gemini (logo + texte),
    principalement situé dans le coin inférieur droit.
    """
    hauteur, largeur = image.shape[:2]

    # Zone plus haute et plus compacte : le logo Gemini est généralement
    # proche du coin bas droit mais au-dessus du bord inférieur.
    x_debut = int(largeur * 0.80)
    y_debut = int(hauteur * 0.82)
    x_fin = int(largeur * 0.995)
    y_fin = int(hauteur * 0.98)

    zone = image[y_debut:y_fin, x_debut:x_fin]
    if zone.size == 0:
        return None

    gris = cv2.cvtColor(zone, cv2.COLOR_BGR2GRAY)

    # Le logo est clair/semi-transparent: seuillage lumineux dynamique.
    seuil = max(145, int(np.percentile(gris, 88)))
    _, masque = cv2.threshold(gris, seuil, 255, cv2.THRESH_BINARY)

    noyau = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    masque = cv2.morphologyEx(masque, cv2.MORPH_OPEN, noyau, iterations=1)
    masque = cv2.morphologyEx(masque, cv2.MORPH_CLOSE, noyau, iterations=2)

    contours, _ = cv2.findContours(masque, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    surface_image = hauteur * largeur
    meilleur = None
    meilleur_score = -1.0

    for contour in contours:
        x_local, y_local, w_local, h_local = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)

        if area < max(120, surface_image * 0.00003) or area > surface_image * 0.01:
            continue
        if w_local < 18 or h_local < 18:
            continue

        rect_area = max(w_local * h_local, 1)
        fill_ratio = area / rect_area
        aspect = w_local / max(h_local, 1)

        # L'étoile Gemini est presque carrée et non totalement pleine.
        if fill_ratio < 0.20 or fill_ratio > 0.92:
            continue
        if aspect < 0.45 or aspect > 1.8:
            continue

        score = area * (1.0 - abs(1.0 - aspect)) * (1.0 - abs(0.45 - fill_ratio))
        if score > meilleur_score:
            meilleur_score = score
            meilleur = (x_local, y_local, w_local, h_local, area, fill_ratio)

    if meilleur is None:
        return None

    x_local, y_local, w_local, h_local, area, fill_ratio = meilleur

    # Ajuster la bbox selon la forme détectée:
    # - logo seul (presque carré) -> zone serrée
    # - logo + texte (forme horizontale) -> zone plus large
    aspect_local = w_local / max(h_local, 1)
    if 0.65 <= aspect_local <= 1.55:
        marge_x = int(0.18 * w_local)
        marge_y = int(0.18 * h_local)
        largeur_box = int(w_local * 1.35)
        hauteur_box = int(h_local * 1.35)
    else:
        marge_x = int(0.35 * w_local)
        marge_y = int(0.20 * h_local)
        largeur_box = int(w_local * 1.8)
        hauteur_box = int(h_local * 2.2)

    x_global = max(0, x_debut + x_local - marge_x - MARGE_DETECTION)
    y_global = max(0, y_debut + y_local - marge_y - MARGE_DETECTION)
    w_global = min(largeur_box + 2 * MARGE_DETECTION, largeur - x_global)
    h_global = min(hauteur_box + 2 * MARGE_DETECTION, hauteur - y_global)

    confiance = float(min(0.95, 0.55 + min(area / 3500.0, 0.35)))

    resultat = {
        "detecte": True,
        "x": x_global,
        "y": y_global,
        "largeur": w_global,
        "hauteur": h_global,
        "confiance": round(confiance, 3),
        "source": "gemini",
    }

    if mode_debug or MODE_DEBUG:
        resultat["debug"] = {
            "zone_candidate": {
                "x_debut": x_debut,
                "y_debut": y_debut,
                "x_fin": x_fin,
                "y_fin": y_fin,
            },
            "seuil": seuil,
            "area": round(float(area), 2),
            "fill_ratio": round(float(fill_ratio), 4),
            "nombre_contours": len(contours),
            "masque_pixels_actifs": int(np.count_nonzero(masque)),
        }

    logger.info(
        "Watermark Gemini détecté à (%d, %d) taille %dx%d (confiance=%.3f)",
        x_global, y_global, w_global, h_global, resultat["confiance"],
    )

    return resultat
 