# Distillation Studio

Distillation Studio is a portfolio app with a Vite/React frontend, one shared FastAPI API, and project libraries under `backend/`.

## Structure

- `frontend/`: React UI, project catalog, project pages, and typed API clients.
- `api/`: FastAPI entrypoint and thin project adapters.
- `backend/`: project implementation libraries and binaries used by the API.
- `docker-compose.yml`: production Compose file for the Oracle server.
- `docker-compose.local.yml`: local Compose file for smoke testing containers.

## Adding A Backend Project

1. Add the project implementation under `backend/<project_name>`.
2. Keep project logic in `backend/`; API code should only validate, call the project, and serialize responses.
3. Add focused tests beside the project when the implementation has reusable logic.
4. If the project needs compiled artifacts, build them in the API Dockerfile builder stage and copy only runtime artifacts into the final image.

## Adding An API Router

1. Create `api/projects/<project_name>/router.py`, `schemas.py`, and `service.py`.
2. Register the router once in `api/projects/registry.py`.
3. Use stable prefixes under `/api/projects/<project-slug>`.
4. Keep public response shapes explicit in schemas or typed service helpers.

## Adding A Frontend Project Page

1. Add metadata in `frontend/src/data/projects.ts`.
2. Add a typed API client in `frontend/src/api/` if the page talks to FastAPI.
3. Add a project studio component when the project is runnable or interactive.
4. Route slugs are read from project metadata and must keep existing public URLs stable.

## Deployment

Production uses two containers:

- `api`: FastAPI on the internal Compose network, port `8000`.
- `frontend`: Nginx serving the Vite build and proxying `/api/` to `api:8000`.

The Oracle server deploy directory is `/home/ubuntu/distillation-studio`. Cloudflare Origin Certificate files should be placed at:

- `/home/ubuntu/distillation-studio/certs/origin.pem`
- `/home/ubuntu/distillation-studio/certs/origin.key`

GitHub Actions builds ARM64 images, pushes them to GHCR, uploads `docker-compose.yml`, writes `.env` with `IMAGE_TAG`, then runs `docker compose pull` and `docker compose up -d --remove-orphans`.
