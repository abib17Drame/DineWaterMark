# Étape 1 : Construction (Node.js)
FROM node:20-alpine AS builder

WORKDIR /app

# Installer les dépendances
COPY package*.json ./
RUN npm ci

# Copier le code
COPY . .

# Construire l'application Vite (Vite lira automatiquement le fichier .env copié)

# Construire l'application Vite
RUN npm run build

# Étape 2 : Serveur Web (Nginx)
FROM nginx:alpine

# Copier le bundle généré par Vite
COPY --from=builder /app/dist /usr/share/nginx/html

# Ajouter une configuration Nginx minimaliste pour supporter le routage Single Page App (SPA)
RUN echo "server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files \$uri \$uri/ /index.html; \
    } \
}" > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
 