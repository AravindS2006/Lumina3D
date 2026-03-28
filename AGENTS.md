# AGENTS.md

Operating guide for autonomous coding agents working in `Lumina3D`.

## Project Context

- Repository: `Lumina3D`
- Primary branch: `main`
- Product goal:
  - Frontend: React + Tailwind with a glassmorphism UI system
  - Backend: FastAPI (Colab deployment path with pyngrok)
  - AI engines: Hunyuan3D-2mv (mesh) and Hunyuan3D-2.1 (PBR textures)
  - Runtime strategy: sequential VRAM management between heavy stages

## Current Repository State (Verified)

- Tracked files at `HEAD`: `.gitattributes`
- Working tree also contains this `AGENTS.md`
- No frontend/backend source code yet
- No detected manifests yet (`package.json`, `pyproject.toml`, `requirements*.txt`, etc.)
- No configured build/lint/test scripts at this moment

## Cursor and Copilot Policy Files

Agents must check and obey these files before making changes:

- `.cursor/rules/`
- `.cursorrules`
- `.github/copilot-instructions.md`

Status during this analysis:

- `.cursor/rules/` not present
- `.cursorrules` not present
- `.github/copilot-instructions.md` not present

If any of these files appear later, treat them as higher-priority instructions.

## Command Discovery Protocol

Do not guess commands. Infer from real project config only.

1. Inspect manifests and scripts first.
2. Use repo-native commands only.
3. Prefer deterministic command variants in CI-friendly mode.
4. When multiple tools exist, use the one already wired in scripts.

## Commands (Current + Planned)

### Current Commands You Can Run Now

- `git status --short --branch`
- `git log --oneline -n 20`
- `git ls-tree --name-only -r HEAD`

### Frontend Commands (Use Once Frontend Exists)

If React + Tailwind is scaffolded with npm scripts, standardize on:

- Build: `npm run build`
- Lint: `npm run lint`
- Format check (if configured): `npm run format:check`
- Unit tests (all): `npm run test -- --runInBand` or `vitest run`
- Single test file (Vitest): `vitest run src/path/file.test.ts`
- Single test by name (Vitest): `vitest run -t "test case name"`
- Single test file (Jest): `npm test -- src/path/file.test.ts`
- Single test by name (Jest): `npm test -- -t "test case name"`

### Backend Commands (Use Once FastAPI Exists)

If Python backend is scaffolded, standardize on:

- Dev server: `uvicorn app.main:app --reload`
- Lint (ruff): `ruff check .`
- Format (ruff/black): `ruff format .` or `black .`
- Type check (if present): `mypy .`
- Tests (all): `pytest`
- Single test file: `pytest tests/test_api.py`
- Single test case: `pytest tests/test_api.py::test_endpoint_behavior`
- Single parametrized case: `pytest tests/test_api.py::test_name[param]`

### AI Pipeline Validation Commands (When Added)

- Prefer script entrypoints over ad-hoc notebooks.
- Add stage-level smoke tests for:
  - video ingest/preprocess
  - Hunyuan3D-2mv mesh generation
  - Hunyuan3D-2.1 texture generation
  - mesh + texture integration/export
- For VRAM-sensitive flows, validate sequential execution explicitly.

## Engineering Workflow Rules

1. Read current repo state before editing.
2. Keep changes minimal and scoped to the request.
3. Avoid unrelated refactors.
4. Preserve user changes you did not create.
5. Verify touched scope with the narrowest useful command.
6. Document assumptions when tooling is missing.

## Code Style Guidelines

### Imports and Dependencies

- Keep imports explicit, minimal, and sorted.
- Remove unused imports in edited files.
- Group imports as: standard library, third-party, local.
- Prefer stable absolute imports when project conventions support them.
- Do not add dependencies without clear need and rationale.
- Avoid circular dependencies; refactor boundaries instead.

### Formatting and File Hygiene

- Use configured formatters/linters when available.
- Keep line length readable (target <= 100 chars unless required).
- Favor trailing commas in multiline structures.
- Avoid formatting-only churn in unrelated files.
- Keep files focused; split oversized modules by responsibility.

### Types and Interfaces

- Prefer explicit types at module boundaries.
- Avoid `any`/untyped payloads unless unavoidable.
- Validate external inputs at API boundaries.
- Model nullability/optionality explicitly.
- Use small, composable interfaces over large catch-all types.
- For Python, add type hints for public functions and data models.

### Naming Conventions

- Use domain-oriented names, not implementation trivia.
- Types/classes/components: `PascalCase`
- Functions/variables: `camelCase` (JS/TS), `snake_case` (Python)
- Constants/env vars: `UPPER_SNAKE_CASE`
- File names:
  - Frontend components: `PascalCase.tsx` (if established)
  - Other frontend modules: `kebab-case` or existing convention
  - Python modules: `snake_case.py`

### Error Handling and Reliability

- Fail fast on invalid states and bad input.
- Never swallow exceptions silently.
- Return/raise actionable errors with context identifiers.
- Do not leak secrets/tokens in logs or errors.
- Use typed/domain errors where practical.
- Add retries/timeouts only where failure modes justify them.

### API and Data Contracts

- Treat external contracts as stable unless intentionally versioned.
- Keep schema validation close to IO boundaries.
- Document breaking changes and migration expectations.
- Keep serialization/deserialization rules explicit and tested.

### Testing Standards

- Add/update tests with every behavior change.
- Cover happy path, edge cases, and failure modes.
- Prefer deterministic tests (control clock/random/network).
- Keep fixtures small and local.
- Add regression tests for bug fixes.
- For GPU-intensive stages, include lightweight smoke tests and mocked fallbacks.

## Definition of Done

A task is complete only when all are true:

- Implementation matches the request.
- Relevant checks pass (or missing tooling is explicitly documented).
- Docs/config are updated for behavioral changes.
- Diff is focused and free of unrelated edits.
- Risks, TODOs, or follow-ups are called out clearly.

## Maintenance Notes for This File

When the first real stack files are added, immediately replace placeholders with exact commands from repo scripts/config and keep single-test examples current for the active test runners.
