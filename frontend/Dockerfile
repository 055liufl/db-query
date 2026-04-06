# Build from repo root (see docker-compose) so ../site exists for @site/tokens (vite alias -> /site).
FROM node:20-alpine

WORKDIR /app

# Lockfile keeps Vitest/devDeps in sync with CI (npm ci).
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
COPY site/ /site

EXPOSE 3000

CMD ["npm", "run", "dev"]
