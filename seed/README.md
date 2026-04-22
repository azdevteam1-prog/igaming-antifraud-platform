# Seed Data

This folder contains test data for the iGaming Anti-Fraud Platform.

## What it seeds

| Item | Count | Details |
|------|-------|---------|
| Admin user | 1 | `admin` / `admin123` |
| Standalone players | 30 | Random countries, statuses, risk scores |
| Cluster 0 — shared device | 4 | Same `device_fingerprint`, risk +30 |
| Cluster 1 — shared IP | 4 | Same `last_ip`, risk +25 |
| Cluster 2 — shared device + IP | 4 | Both identical, risk +50 (most suspicious) |
| Transactions | ~200 | 2-8 per player, mixed deposits/withdrawals |

## How to run

### Option A — via Docker (recommended)

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait ~15s for DB + backend to be ready, then run the seeder
docker-compose exec backend python /seed/seed_data.py
```

> The seed script auto-detects `DATABASE_URL` from the container environment.

### Option B — locally

```bash
pip install asyncpg sqlalchemy faker passlib[bcrypt]

DATABASE_URL=postgresql+asyncpg://fraud:fraud123@localhost:5432/frauddb \
  python seed/seed_data.py
```

## After seeding

| URL | Purpose |
|-----|---------|
| http://localhost:5173 | React frontend (login: admin / admin123) |
| http://localhost:8000/docs | FastAPI Swagger docs |
| http://localhost:8000/redoc | ReDoc |

## Verifying the Account Graph

1. Login at http://localhost:5173
2. Navigate to **Players**
3. Click **View Profile** on any player from Cluster 0, 1 or 2  
   (they will have higher risk scores: 35-100)
4. Click the **Account Graph** tab in the profile modal
5. You should see 3-4 connected nodes with purple (shared device) or blue (shared IP) edges

## Re-running

The script is idempotent for the admin user (skips if exists).  
Players are always freshly inserted — run once or clear the `players` table first:

```sql
-- In psql or any DB client:
TRUNCATE players, transactions CASCADE;
```
