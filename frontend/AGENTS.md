# Repository Guidelines

## Project Structure & Module Organization

This `frontend` workspace is currently a clean project root. Keep future source files under `src/`, with reusable UI in `src/components/`, route or page code in `src/pages/` or `src/app/`, shared utilities in `src/lib/`, and static assets in `public/` or `src/assets/`. Place tests next to the code they cover as `*.test.*` or under `tests/` for integration flows.

## Build, Test, and Development Commands

No package manifest is present yet. Once the frontend framework is initialized, keep these commands in sync with `package.json`.

Expected commands for a Node-based frontend are:

- `npm install` or `pnpm install`: install dependencies.
- `npm run dev`: start the local development server.
- `npm run build`: create a production build.
- `npm test`: run the test suite.
- `npm run lint`: check formatting and static-analysis rules.

Use the package manager already committed to the repo, as indicated by `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, or `bun.lockb`.

## Coding Style & Naming Conventions

Prefer TypeScript when the project is scaffolded. Use 2-space indentation, single-purpose modules, and named exports for shared helpers and components. Name React-style components in `PascalCase` such as `ProjectCard.tsx`, hooks with a `use` prefix such as `useProjectData.ts`, and utility files in `camelCase` or `kebab-case` consistently within each directory.

Add Prettier and ESLint configuration with the framework scaffold, then run linting before opening a pull request.

## Testing Guidelines

Use the framework-standard tools once selected, such as Vitest or Jest for unit tests and Playwright for browser flows. Keep unit tests close to the implementation: `src/lib/formatDate.test.ts` or `src/components/Button.test.tsx`. Cover new logic, edge cases, and user-visible behavior. Add an end-to-end test for workflows spanning routing, forms, authentication, or network state.

## Commit & Pull Request Guidelines

This directory does not currently include Git history, so no local commit convention can be inferred. Use concise, imperative commit subjects such as `Add project dashboard shell` or `Fix upload validation state`.

Pull requests should include a short summary, testing performed, linked issue or task when available, and screenshots for visible UI changes. Call out configuration changes, new environment variables, and migration steps explicitly.

## Security & Configuration Tips

Do not commit secrets, API keys, or local `.env` files. Provide safe defaults in `.env.example` when configuration is required. Keep browser-exposed variables clearly prefixed according to the chosen framework, and verify that sensitive values remain server-only.
