# Repository Guidelines

## Project Structure & Module Organization
- Root files only: `example.svg` (sample diagram asset) and `plan.md` (project notes).
- No `src/`, `tests/`, or build config directories are present yet. Add them when introducing code or tooling.

## Build, Test, and Development Commands
- No build or test commands are defined in this repository at the moment.
- If you add tooling, document it here (e.g., `npm run build` for asset generation, `npm test` for automated checks).

## Coding Style & Naming Conventions
- Use 2-space indentation for any future JavaScript/TypeScript or JSON files unless a formatter is introduced.
- Prefer lowercase, hyphenated file names for assets (example: `diagram-flow.svg`).
- Keep assets in a dedicated folder if more than a few are added (example: `assets/`).

## Testing Guidelines
- No testing framework is configured yet.
- If tests are introduced, keep them in a `tests/` or `__tests__/` directory and name files with a clear suffix (example: `diagram-render.test.js`).
- Document how to run tests once a framework is chosen.

## Commit & Pull Request Guidelines
- Git history is not available in this workspace, so no commit convention can be derived.
- Use concise, imperative commit messages (example: `Add SVG export script`).
- For pull requests, include a short summary, linked issue (if any), and before/after screenshots for visual changes.

## Configuration & Assets Tips
- Treat `example.svg` as a reference asset; avoid overwriting it.
- When adding new assets, include a brief note in `plan.md` describing the purpose and expected usage.
