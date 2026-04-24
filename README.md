# DineDiWaterMark

DineDiWaterMark est une application full-stack qui supprime les watermarks de documents NotebookLM et Gemini.

Le projet traite :
- PDF
- PPTX
- PNG/JPG

L'objectif est de garder la qualite visuelle et la mise en page tout en nettoyant automatiquement la zone du watermark.

## Fonctionnalites principales

- Upload de fichier unique ou batch
- Traitement asynchrone avec suivi de progression
- Apercu avant/apres pendant le traitement
- Telechargement du resultat final
- Modes de detection watermark :
  - `auto`
  - `notebook`
  - `gemini`

## Architecture

- `backend/` : API FastAPI + moteur de traitement image/PDF/PPTX
- `frontend/` : interface React + Vite + Tailwind
- `docker-compose.yml` : demarrage backend + frontend en conteneurs
- `.env.example` : variables d'environnement de base

## Prerequis

Option A (Docker) :
- Docker
- Docker Compose

Option B (local) :
- Python 3.12+
- Node.js 18+
- npm

## Demarrage rapide (Docker)

1. Copier les variables d'environnement :

```bash
cp .env.example .env
```

2. Lancer les services :

```bash
docker compose up --build
```

3. Acces :
- Frontend : http://localhost:8082
- Backend API : http://localhost:8000
- Swagger : http://localhost:8000/docs
- Healthcheck : http://localhost:8000/api/v1/health

## Demarrage local (sans Docker)

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Par defaut, le frontend appelle `http://localhost:8000/api/v1`.

## API (resume)

Base URL : `http://localhost:8000/api/v1`

Endpoints principaux :
- `POST /remove` : traitement d'un fichier
- `POST /batch` : traitement de plusieurs fichiers
- `POST /merge` : fusion PPTX
- `GET /status/{id}` : progression d'une tache
- `GET /download/{id}` : telechargement du resultat
- `GET /preview/{id}` : apercu avant/apres

Exemple `remove` :

```bash
curl -X POST "http://localhost:8000/api/v1/remove" \
  -F "file=@document.pdf" \
  -F "watermark_mode=auto"
```

## Variables d'environnement

Variables disponibles (voir aussi `.env.example`) :
- `ALLOWED_ORIGINS`
- `MAX_FILE_SIZE_MB`
- `CLEANUP_DELAY_SEC`
- `TEMP_DIR`
- `WORKERS`
- `RENDER_DPI`
- `INPAINT_RADIUS`
- `DEBUG_MODE`

ok 