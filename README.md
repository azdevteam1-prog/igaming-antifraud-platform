# 🛡️ iGaming Anti-Fraud Platform

Real-time anti-fraud platform for iGaming operators.

## Features
- 🔴 Live Deposits & Withdrawals monitoring
- ⚙️ Rules Studio (create/edit/test/publish rules)
- 📊 Risk Scoring with explainability
- 🕸️ Multi-Account Graph (link analysis)
- 👤 Player Profile with full history
- 🚨 Cases & Alerts management

## Stack
- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: React + TypeScript + Vite + AG Grid + Cytoscape.js
- **Realtime**: WebSocket + SSE
- **Infra**: Docker Compose

## Quick Start
```bash
docker-compose up --build
```
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure
```
igaming-antifraud-platform/
├── backend/          # FastAPI app
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── core/     # Config, DB, Redis
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── services/ # Business logic
│   │   │   ├── simulator.py
│   │   │   ├── rules_engine.py
│   │   │   ├── risk_scorer.py
│   │   │   └── link_analysis.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/         # React app
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── api/
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```
