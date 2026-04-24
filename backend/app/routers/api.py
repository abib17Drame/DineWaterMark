"""
Routeur principal de l'API v1 — tous les endpoints REST.

Endpoints
- POST /remove          → Supprime le watermark d'un fichier unique
- POST /batch           → Traitement de plusieurs fichiers
- POST /merge           → Fusionne plusieurs PPTX en un seul
- GET  /status/{id}     → Statut d'une tâche asynchrone
- GET  /download/{id}   → Télécharge le fichier traité
- GET  /preview/{id}    → Aperçu avant/après de la première page
"""
import os
import uuid
import asyncio
import logging
import time
import base64

import cv2
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

from app.config import TAILLE_MAX_FICHIER_OCTETS, EXTENSIONS_AUTORISEES
from app.utils.file_utils import (
    valider_extension_fichier,
    valider_type_mime,
    valider_signature_fichier,
    detecter_type_fichier,
    obtenir_extension,
    obtenir_repertoire_temp,
    planifier_nettoyage,
)
from app.services.pdf_processeur import traiter_pdf, extraire_apercu_page
from app.services.pptx_processeur import traiter_pptx, fusionner_pptx
from app.services.image_processeur import traiter_image

logger = logging.getLogger(__name__)

routeur = APIRouter(tags=["Traitement"])

# Stockage en mémoire des tâches
# En production, utiliser Redis ou une base de données
taches: dict[str, dict] = {}

# Compteur global de fichiers traités (statistique publique)
compteur_fichiers_traites: int = 0
MODES_WATERMARK_AUTORISES: set[str] = {"auto", "notebook", "gemini"}


def _generer_id_tache() -> str:
    """Génère un identifiant unique pour une tâche."""
    return str(uuid.uuid4())[:8]


async def _traiter_fichier_tache(
    id_tache: str,
    chemin_entree: str,
    chemin_sortie: str,
    type_fichier: str,
    mode_debug: bool,
    mode_watermark: str,
) -> None:
    """
    Tâche de fond qui lance le traitement selon le type de fichier.
    Met à jour le statut dans le dictionnaire `taches`.
    """
    global compteur_fichiers_traites

    try:
        taches[id_tache]["status"] = "en_cours"
        taches[id_tache]["progression"] = 0

        def callback_progression(courant: int, total: int, b64_orig=None, b64_nette=None):
            taches[id_tache]["progression"] = int((courant / total) * 100)
            taches[id_tache]["message"] = f"Traitement de la page {courant}/{total}"
            if b64_orig and b64_nette:
                taches[id_tache]["preview_orig"] = b64_orig
                taches[id_tache]["preview_nette"] = b64_nette
                taches[id_tache]["page_courante"] = courant

        debut = time.time()

        if type_fichier == "pdf":
            resultat = await asyncio.to_thread(
                traiter_pdf,
                chemin_entree, chemin_sortie, mode_debug, callback_progression, mode_watermark
            )
        elif type_fichier == "pptx":
            resultat = await asyncio.to_thread(
                traiter_pptx,
                chemin_entree, chemin_sortie, mode_debug, callback_progression, mode_watermark
            )
        elif type_fichier == "image":
            resultat = await asyncio.to_thread(
                traiter_image,
                chemin_entree, chemin_sortie, mode_debug, mode_watermark
            )
        else:
            raise ValueError(f"Type de fichier non supporté : {type_fichier}")

        duree_ms = int((time.time() - debut) * 1000)

        taches[id_tache].update({
            "status": "termine",
            "progression": 100,
            "message": "Traitement terminé avec succès",
            "chemin_resultat": chemin_sortie,
            "watermark_detecte": resultat.get("watermark_detecte",
                                              resultat.get("pages_avec_watermark", 0) > 0),
            "temps_traitement_ms": duree_ms,
            "url_telechargement": f"/api/v1/download/{id_tache}",
            "resultat": resultat,
        })

        compteur_fichiers_traites += 1

        # Planifier le nettoyage des fichiers temporaires
        asyncio.create_task(planifier_nettoyage(chemin_entree))
        # Le fichier de sortie sera nettoyé après téléchargement

        logger.info("Tâche %s terminée avec succès en %dms", id_tache, duree_ms)

    except Exception as erreur:
        logger.error("Erreur tâche %s : %s", id_tache, erreur, exc_info=True)
        taches[id_tache].update({
            "status": "erreur",
            "message": str(erreur),
            "progression": 0,
        })
        # Nettoyer les fichiers en cas d'erreur
        asyncio.create_task(planifier_nettoyage(chemin_entree, delai=5))
        if os.path.exists(chemin_sortie):
            asyncio.create_task(planifier_nettoyage(chemin_sortie, delai=5))


# POST /remove
@routeur.post("/remove")
async def supprimer_watermark_fichier(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="Fichier à traiter (PDF, PPTX, PNG, JPG)"),
    debug: bool = Form(False, description="Activer le mode debug"),
    watermark_mode: str = Form("auto", description="Mode watermark: auto | notebook | gemini"),
):
    """
    Supprime le watermark NotebookLM d'un fichier unique.

    Formats supportés : PDF, PPTX, PNG, JPG.
    Le traitement est asynchrone — utilisez /status/{task_id} pour suivre.
    """
    # Validation
    if not valider_extension_fichier(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté. Extensions autorisées : {', '.join(EXTENSIONS_AUTORISEES)}",
        )

    # Lire le contenu pour vérifier la taille
    contenu = await file.read()
    taille_fichier = len(contenu)

    if taille_fichier > TAILLE_MAX_FICHIER_OCTETS:
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux ({taille_fichier // (1024*1024)}Mo). "
                   f"Maximum : {TAILLE_MAX_FICHIER_OCTETS // (1024*1024)}Mo",
        )

    if taille_fichier == 0:
        raise HTTPException(status_code=400, detail="Le fichier est vide")

    if not valider_type_mime(file.content_type):
        raise HTTPException(
            status_code=400,
            detail=f"Type MIME non supporté: {file.content_type}",
        )

    if not valider_signature_fichier(file.filename, contenu):
        raise HTTPException(
            status_code=400,
            detail="Signature de fichier invalide pour l'extension déclarée",
        )

    watermark_mode = watermark_mode.lower().strip()
    if watermark_mode not in MODES_WATERMARK_AUTORISES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Mode watermark invalide. Valeurs autorisées : "
                f"{', '.join(sorted(MODES_WATERMARK_AUTORISES))}"
            ),
        )

    # Préparation
    id_tache = _generer_id_tache()
    type_fichier = detecter_type_fichier(file.filename)
    extension = obtenir_extension(file.filename)
    repertoire_temp = obtenir_repertoire_temp()

    chemin_entree = str(repertoire_temp / f"{id_tache}_entree{extension}")
    chemin_sortie = str(repertoire_temp / f"{id_tache}_sortie{extension}")

    # Sauvegarder le fichier sur le disque
    with open(chemin_entree, "wb") as f:
        f.write(contenu)

    # Initialiser la tâche
    taches[id_tache] = {
        "id_tache": id_tache,
        "status": "en_attente",
        "progression": 0,
        "message": "En file d'attente...",
        "nom_fichier": file.filename,
        "type_fichier": type_fichier,
        "taille_octets": taille_fichier,
        "chemin_resultat": None,
        "watermark_detecte": None,
        "temps_traitement_ms": None,
        "watermark_mode": watermark_mode,
    }

    # Lancer le traitement en arrière-plan
    background_tasks.add_task(
        _traiter_fichier_tache,
        id_tache, chemin_entree, chemin_sortie, type_fichier, debug, watermark_mode,
    )

    return {
        "status": "succes",
        "id_tache": id_tache,
        "message": "Traitement en cours",
        "url_status": f"/api/v1/status/{id_tache}",
    }


# POST /batch
@routeur.post("/batch")
async def traitement_batch(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(..., description="Fichiers à traiter"),
    merge_pptx: bool = Form(False, description="Fusionner les PPTX avant traitement"),
    debug: bool = Form(False),
    watermark_mode: str = Form("auto", description="Mode watermark: auto | notebook | gemini"),
):
    """
    Traite plusieurs fichiers en une seule opération.
    Option : fusionner les PPTX avant traitement.
    """
    if not files:
        raise HTTPException(status_code=400, detail="Aucun fichier fourni")

    if len(files) > 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 fichiers par batch",
        )

    watermark_mode = watermark_mode.lower().strip()
    if watermark_mode not in MODES_WATERMARK_AUTORISES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Mode watermark invalide. Valeurs autorisées : "
                f"{', '.join(sorted(MODES_WATERMARK_AUTORISES))}"
            ),
        )

    ids_taches = []
    fichiers_rejetes = []

    for fichier in files:
        if not valider_extension_fichier(fichier.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Format non supporté pour {fichier.filename}",
            )

        if not valider_type_mime(fichier.content_type):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Type MIME non supporté pour {fichier.filename}: "
                    f"{fichier.content_type}"
                ),
            )

    # Si fusion PPTX demandée, on fusionne d'abord
    if merge_pptx:
        fichiers_pptx = [f for f in files if detecter_type_fichier(f.filename) == "pptx"]
        fichiers_autres = [f for f in files if detecter_type_fichier(f.filename) != "pptx"]

        if len(fichiers_pptx) > 1:
            # Sauvegarder les fichiers PPTX sur le disque
            id_fusion = _generer_id_tache()
            repertoire_temp = obtenir_repertoire_temp()
            chemins_pptx = []

            for i, f_pptx in enumerate(fichiers_pptx):
                contenu = await f_pptx.read()
                chemin_temp = str(repertoire_temp / f"{id_fusion}_merge_{i}.pptx")
                with open(chemin_temp, "wb") as f:
                    f.write(contenu)
                chemins_pptx.append(chemin_temp)

            # Fusionner
            chemin_fusionne = str(repertoire_temp / f"{id_fusion}_fusionne.pptx")
            fusionner_pptx(chemins_pptx, chemin_fusionne)

            # Traiter le fichier fusionné
            chemin_sortie_fusion = str(repertoire_temp / f"{id_fusion}_sortie.pptx")
            taches[id_fusion] = {
                "id_tache": id_fusion,
                "status": "en_attente",
                "progression": 0,
                "message": "Fusion + traitement en cours...",
                "nom_fichier": "merged.pptx",
                "type_fichier": "pptx",
                "chemin_resultat": None,
            }
            background_tasks.add_task(
                _traiter_fichier_tache,
                id_fusion, chemin_fusionne, chemin_sortie_fusion, "pptx", debug, watermark_mode,
            )
            ids_taches.append(id_fusion)

            # Nettoyage des fichiers temporaires de fusion
            for c in chemins_pptx:
                asyncio.create_task(planifier_nettoyage(c))

            files = fichiers_autres  # On ne traite que les non-PPTX en solo

    # Traiter chaque fichier restant individuellement
    for fichier in files:
        contenu = await fichier.read()
        taille = len(contenu)

        if not valider_signature_fichier(fichier.filename, contenu):
            fichiers_rejetes.append({
                "nom_fichier": fichier.filename,
                "raison": "Signature de fichier invalide",
            })
            continue

        if taille > TAILLE_MAX_FICHIER_OCTETS:
            fichiers_rejetes.append({
                "nom_fichier": fichier.filename,
                "raison": (
                    f"Fichier trop volumineux ({taille // (1024*1024)}Mo), "
                    f"max {TAILLE_MAX_FICHIER_OCTETS // (1024*1024)}Mo"
                ),
            })
            continue

        if taille == 0:
            fichiers_rejetes.append({
                "nom_fichier": fichier.filename,
                "raison": "Fichier vide",
            })
            continue

        id_tache = _generer_id_tache()
        type_fichier = detecter_type_fichier(fichier.filename)
        extension = obtenir_extension(fichier.filename)
        repertoire_temp = obtenir_repertoire_temp()

        chemin_entree = str(repertoire_temp / f"{id_tache}_entree{extension}")
        chemin_sortie = str(repertoire_temp / f"{id_tache}_sortie{extension}")

        with open(chemin_entree, "wb") as f:
            f.write(contenu)

        taches[id_tache] = {
            "id_tache": id_tache,
            "status": "en_attente",
            "progression": 0,
            "message": "En file d'attente...",
            "nom_fichier": fichier.filename,
            "type_fichier": type_fichier,
            "taille_octets": taille,
            "chemin_resultat": None,
            "watermark_mode": watermark_mode,
        }

        background_tasks.add_task(
            _traiter_fichier_tache,
            id_tache, chemin_entree, chemin_sortie, type_fichier, debug, watermark_mode,
        )
        ids_taches.append(id_tache)

    if not ids_taches:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Aucun fichier valide à traiter dans le batch",
                "fichiers_rejetes": fichiers_rejetes,
            },
        )

    return {
        "status": "succes",
        "nombre_fichiers": len(ids_taches),
        "ids_taches": ids_taches,
        "fichiers_rejetes": fichiers_rejetes,
        "message": f"{len(ids_taches)} fichier(s) en cours de traitement",
    }


# POST /merge
@routeur.post("/merge")
async def fusionner_fichiers_pptx(
    files: list[UploadFile] = File(..., description="Fichiers PPTX à fusionner"),
):
    """Fusionne plusieurs fichiers PPTX en un seul (sans supprimer le watermark)."""
    if len(files) < 2:
        raise HTTPException(
            status_code=400, detail="Au moins 2 fichiers PPTX requis pour la fusion"
        )

    for fichier in files:
        if detecter_type_fichier(fichier.filename) != "pptx":
            raise HTTPException(
                status_code=400,
                detail=f"Seuls les fichiers PPTX sont acceptés pour la fusion. "
                       f"Fichier invalide : {fichier.filename}",
            )

    id_tache = _generer_id_tache()
    repertoire_temp = obtenir_repertoire_temp()
    chemins_entree = []

    for i, fichier in enumerate(files):
        if not valider_type_mime(fichier.content_type):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Type MIME non supporté pour {fichier.filename}: "
                    f"{fichier.content_type}"
                ),
            )

        contenu = await fichier.read()
        if not valider_signature_fichier(fichier.filename, contenu):
            raise HTTPException(
                status_code=400,
                detail=f"Signature de fichier invalide pour {fichier.filename}",
            )

        chemin_temp = str(repertoire_temp / f"{id_tache}_merge_{i}.pptx")
        with open(chemin_temp, "wb") as f:
            f.write(contenu)
        chemins_entree.append(chemin_temp)

    chemin_sortie = str(repertoire_temp / f"{id_tache}_fusionne.pptx")
    resultat = fusionner_pptx(chemins_entree, chemin_sortie)

    # Nettoyage des fichiers source
    for c in chemins_entree:
        asyncio.create_task(planifier_nettoyage(c))

    taches[id_tache] = {
        "id_tache": id_tache,
        "status": "termine",
        "progression": 100,
        "message": "Fusion terminée",
        "chemin_resultat": chemin_sortie,
        "resultat": resultat,
    }

    return {
        "status": "succes",
        "id_tache": id_tache,
        "url_telechargement": f"/api/v1/download/{id_tache}",
        **resultat,
    }


# GET /status/{id_tache}
@routeur.get("/status/{id_tache}")
async def obtenir_statut(id_tache: str):
    """Retourne le statut actuel d'une tâche de traitement."""
    tache = taches.get(id_tache)
    if not tache:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")

    # Ne pas exposer les chemins internes dans la réponse
    reponse = {k: v for k, v in tache.items() if k != "chemin_resultat"}
    return reponse


# GET /download/{id_tache}
@routeur.get("/download/{id_tache}")
async def telecharger_fichier(id_tache: str):
    """Télécharge le fichier traité (nettoyé)."""
    tache = taches.get(id_tache)
    if not tache:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")

    if tache["status"] != "termine":
        raise HTTPException(
            status_code=400,
            detail=f"Le traitement n'est pas terminé (statut: {tache['status']})",
        )

    chemin_resultat = tache.get("chemin_resultat")
    if not chemin_resultat or not os.path.exists(chemin_resultat):
        raise HTTPException(status_code=404, detail="Fichier résultat non trouvé")

    nom_original = tache.get('nom_fichier', os.path.basename(chemin_resultat))
    # Nettoyer le nom de fichier pour éviter les bugs de header HTTP avec les espaces et caractères spéciaux
    nom_propre = "".join(c if c.isalnum() or c in ".-_" else "_" for c in nom_original)
    nom_fichier_sortie = f"nettoye_{nom_propre}"

    # Planifier le nettoyage du fichier après téléchargement
    asyncio.create_task(planifier_nettoyage(chemin_resultat, delai=60))

    return FileResponse(
        path=chemin_resultat,
        filename=nom_fichier_sortie,
        media_type="application/octet-stream",
        content_disposition_type="attachment",
        headers={"Access-Control-Expose-Headers": "Content-Disposition"}
    )


# GET /preview/{id_tache}
@routeur.get("/preview/{id_tache}")
async def apercu_avant_apres(id_tache: str):
    """
    Retourne un aperçu avant/après de la première page (base64).
    Utile pour le frontend.
    """
    tache = taches.get(id_tache)
    if not tache:
        raise HTTPException(status_code=404, detail="Tâche non trouvée")

    if tache["status"] != "termine":
        raise HTTPException(
            status_code=400, detail="Le traitement n'est pas encore terminé"
        )

    # Pour les PDF, extraire un aperçu de la première page
    chemin_resultat = tache.get("chemin_resultat")
    if not chemin_resultat or not os.path.exists(chemin_resultat):
        raise HTTPException(status_code=404, detail="Fichier résultat non trouvé")

    type_fichier = tache.get("type_fichier", "")

    if type_fichier == "pdf":
        apercu_apres = extraire_apercu_page(chemin_resultat, 0, dpi=150)
    elif type_fichier == "image":
        apercu_apres = cv2.imread(chemin_resultat)
    else:
        raise HTTPException(
            status_code=400,
            detail="Aperçu non disponible pour ce type de fichier",
        )

    if apercu_apres is None:
        raise HTTPException(status_code=500, detail="Erreur lors de la génération de l'aperçu")

    # Encoder en base64 pour le transport JSON
    _, tampon = cv2.imencode(".jpg", apercu_apres, [cv2.IMWRITE_JPEG_QUALITY, 85])
    apercu_b64 = base64.b64encode(tampon).decode("utf-8")

    return {
        "id_tache": id_tache,
        "apercu_apres": f"data:image/jpeg;base64,{apercu_b64}",
    }


# GET /stats
@routeur.get("/stats", tags=["Statistiques"])
async def obtenir_statistiques():
    """Retourne les statistiques publiques."""
    return {
        "fichiers_traites": compteur_fichiers_traites,
        "taches_en_cours": sum(
            1 for t in taches.values() if t["status"] in ("en_cours", "en_attente")
        ),
        "taches_terminees": sum(
            1 for t in taches.values() if t["status"] == "termine"
        ),
    }
 