# Contributing to iGaming Anti-Fraud Platform

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Commit Convention](#commit-convention)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Reporting Issues](#reporting-issues)

---

## Getting Started

1. **Fork** the repository and clone your fork.
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. Make your changes, write tests, and open a Pull Request.

---

## Development Setup

### Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| Docker & Docker Compose | latest |
| PostgreSQL | 15 |
| Redis | 7 |

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Copy environment file
cp ../.env.example .env

# Start dependencies (Postgres + Redis)
docker compose up db redis -d

# Run the API
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Full Stack (Docker)

```bash
docker compose up --build
```

---

## Project Structure

```
igaming-antifraud-platform/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers (transactions, players, alerts...)
│   │   ├── core/         # DB engine, Redis client, config
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   └── services/     # Business logic (rules engine, risk scorer, ML)
│   └── tests/            # pytest test suite
├── frontend/
│   ├── src/
│   │   ├── api/          # Axios API clients
│   │   ├── components/   # React UI components
│   │   ├── hooks/        # Custom React hooks
│   │   └── types/        # TypeScript type definitions
│   └── ...
└── docker-compose.yml
```

---

## Coding Standards

### Python (Backend)

- Follow **PEP 8** and use type hints everywhere.
- Format with `black` and lint with `ruff`.
- All public functions must have docstrings.
- Async functions should be used for all I/O-bound operations.

```bash
pip install black ruff
black app tests
ruff check app tests
```

### TypeScript (Frontend)

- Use strict TypeScript — no `any` types without justification.
- Components: functional components with hooks only.
- Import types from `src/types/index.ts` — do not duplicate interfaces.
- Format with Prettier (`npm run format`).

### General

- Keep functions small and focused (single responsibility).
- Prefer explicit over implicit.
- Document any non-obvious business logic with comments.

---

## Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>
```

| Type | Usage |
|------|-------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Adding or updating tests |
| `refactor` | Code change without feature/bug |
| `chore` | Build process, tooling |
| `perf` | Performance improvement |

**Examples:**
```
feat(api): add /analytics/fraud-rate endpoint
fix(risk-scorer): handle division by zero for new players
docs: update CONTRIBUTING setup instructions
test(geo-service): add impossible travel edge cases
```

---

## Pull Request Process

1. Ensure your branch is up-to-date with `main`.
2. Run the full test suite locally — all tests must pass.
3. Fill in the PR description template:
   - **What** was changed and **why**
   - Link any related issues (e.g., `Closes #42`)
   - Include screenshots for UI changes
4. Request review from at least one maintainer.
5. Address review comments before merging.
6. Use **Squash and Merge** to keep history clean.

---

## Testing

### Backend

```bash
cd backend
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=term-missing
```

Tests are located in `backend/tests/`. Naming convention: `test_<module>.py`.

- **Unit tests**: Pure logic, mocked database (no DB required).
- **Integration tests**: Use `pytest-asyncio` with a test database.

### Frontend

```bash
cd frontend
npm run test
```

---

## Reporting Issues

When filing a bug report, please include:

- **Description** of the problem
- **Steps to reproduce**
- **Expected** vs **actual** behaviour
- Environment details (OS, Python/Node version, Docker version)
- Relevant logs or screenshots

For security vulnerabilities, please **do not** open a public issue. Contact the maintainers directly.

---

## Code of Conduct

Be respectful. Constructive criticism is welcome; personal attacks are not.
All contributions are subject to our standard open-source code of conduct.
