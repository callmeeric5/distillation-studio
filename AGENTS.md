# Distillation Studio Architecture Notes

Distillation Studio is a portfolio for showing Eric Windsor's small projects. It should present each project clearly without rewriting the project as a separate frontend-only demo.

## Project Ownership

- Keep each project's core logic under `backend/<project>`.
- It is acceptable to refactor, simplify, or adapt backend project code so it works well on this website.
- Do not duplicate a project's core algorithms, game rules, agent logic, or execution model in React/TypeScript when the backend project already owns that behavior.
- The frontend may render visuals, collect input, and display status, but the project-specific behavior should stay in the backend project library.

## API Boundary

- `api/` is the shared FastAPI gateway for all projects.
- FastAPI routers should be thin adapters: validate requests, call the backend project library, serialize responses, and handle persistence when needed.
- Add one router per project and register it in the shared API registry.
- Keep one shared API container unless a future project has a clearly different runtime, security boundary, or scaling need.

## Frontend Boundary

- The frontend should focus on routing, layout, controls, visualization, and user feedback.
- For interactive projects, TypeScript may handle browser input and drawing, but it should not become the authoritative source for backend-owned rules.
- When adding a new project page, prefer a typed API client plus a focused studio component.

## Deployment

- Keep deployment simple: one frontend/Nginx container, one shared FastAPI API container, and shared infrastructure containers such as Postgres when needed.
- Avoid per-project Dockerfiles unless a project requires a separate runtime or isolation model.
