#  Étape 1 : Image de base Python (Debian stable)
FROM python:3.12-slim-bookworm AS base

# Installer les dépendances systèmes nécessaires (libglib pour OpenCV headless)
RUN apt-get update && \
    apt-get install -y -o Acquire::Retries=10 -o Acquire::http::Timeout=120 --no-install-recommends \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

#  Étape 2 : Installer uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

#  Étape 3 : Configuration du projet 
WORKDIR /app

# Variables d'environnement pour uv (timeouts augmentés pour les gros paquets comme OpenCV)
ENV UV_HTTP_TIMEOUT=300
ENV UV_LINK_MODE=copy
ENV PYTHONUNBUFFERED=1

# Copier uniquement les fichiers de dépendances pour maximiser le cache Docker
COPY pyproject.toml uv.lock ./

# Synchroniser les dépendances sans installer le projet (le code n'est pas encore là)
# Utilisation d'un mount de cache pour accélérer les futurs builds
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copier le code source de l'application
COPY app/ app/

#  Étape 4 : Configuration finale
ENV TEMP_DIR=/tmp/dinediwatermark
ENV WORKERS=1
ENV MAX_FILE_SIZE_MB=50

# Créer le répertoire temporaire pour le traitement des fichiers
RUN mkdir -p /tmp/dinediwatermark && chmod 777 /tmp/dinediwatermark

# Port exposé
EXPOSE 8000

#  Étape 5 : Lancement
# On utilise 'uv run' qui gère automatiquement l'activation du venv
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
 