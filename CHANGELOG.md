# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- `backend/app/services/ml_detector.py` — ML-style anomaly detection using z-score normalisation, velocity burst detection, time-of-day signals, and round-amount heuristics.
- `backend/app/services/geo_service.py` — Geographic risk service with FATF country tiers, impossible travel detection (Haversine), and VPN/Tor/proxy/datacenter IP risk assessment.
- `backend/app/api/analytics.py` — Analytics REST endpoints: fraud rate, top risky players, alerts by rule, volume by transaction type, risk distribution, and KPI summary.
- `backend/app/models/session.py` — `PlayerSession` ORM model tracking login sessions with full device fingerprint fields (canvas hash, WebGL hash, screen resolution), IP geolocation, and computed risk signals.
- `backend/tests/test_ml_detector.py` — pytest unit tests covering z-score, velocity burst, time-of-day, round-amount, and composite anomaly scoring.
- `backend/tests/test_geo_service.py` — pytest unit tests for country risk tiers, Haversine distance, impossible travel, IP risk, and composite geo scoring.
- `frontend/src/types/index.ts` — Centralised TypeScript type definitions for all domain entities (Player, Transaction, Rule, Alert, Device, Session, Analytics, WebSocket events, Graph nodes/edges).
- `CONTRIBUTING.md` — Developer guide with setup instructions, coding standards, Conventional Commits convention, PR process, and issue reporting guidelines.

---

## [1.0.0] — 2026-04-22

### Added

#### Backend
- FastAPI application with async lifespan context (DB init, Redis init, rule seeding, simulator task).
- PostgreSQL integration via SQLAlchemy async engine with alembic-ready `Base`.
- Redis client with async support for caching and pub/sub.
- **Models**: `Transaction`, `Player`, `Device`, `Rule`, `Alert`.
- **API routers**:
  - `GET/POST /transactions` — transaction management.
  - `GET /players` — player list with risk score sorting.
  - `GET/PUT /rules` — fraud rule CRUD.
  - `GET/PUT /alerts` — alert management and status updates.
  - `GET /dashboard` — real-time dashboard stats.
  - `WS /ws` — WebSocket endpoint for live transaction broadcast.
- **Services**:
  - `rules_engine.py` — Default rule set (velocity, amount thresholds, fast cashout, sanctions, PEP, multi-account, bonus abuse).
  - `risk_scorer.py` — Weighted composite risk score from rule hits and player history signals.
  - `link_analysis.py` — Multi-account graph analysis using shared device/IP/email fingerprints.
  - `simulator.py` — Background transaction simulator for demo/testing.
- **Core**:
  - `config.py` — Pydantic settings from environment variables.
  - `database.py` — Async SQLAlchemy engine and session factory.
  - `redis_client.py` — Async Redis connection pool.
- `Dockerfile` — Multi-stage Python backend image.
- `requirements.txt` — Pinned dependencies.

#### Frontend
- Vite + React 18 + TypeScript application.
- Tailwind CSS for styling.
- WebSocket hook for live transaction feed.
- Dashboard, Transactions, Players, Rules, and Alerts pages.
- `package.json` with all dependencies pinned.
- `vite.config.ts`, `tsconfig.json`, `tailwind.config.js`, `postcss.config.js`.

#### Infrastructure
- `docker-compose.yml` — Orchestrates PostgreSQL 15, Redis 7, Backend (port 8000), and Frontend (port 3000).
- `.env.example` — Environment variable template.
- `.gitignore` — Standard Python + Node ignore patterns.
- `README.md` — Project overview, feature list, and quick-start guide.

---

## [0.1.0] — 2026-04-22 (Initial commit)

### Added
- Initial project scaffold: README, `.env.example`, `.gitignore`, `docker-compose.yml`.

---

[Unreleased]: https://github.com/azdevteam1-prog/igaming-antifraud-platform/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/azdevteam1-prog/igaming-antifraud-platform/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/azdevteam1-prog/igaming-antifraud-platform/releases/tag/v0.1.0
