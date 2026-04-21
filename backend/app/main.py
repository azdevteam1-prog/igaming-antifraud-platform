from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.core.database import engine, Base
from app.core.redis_client import init_redis
from app.api import transactions, players, rules, alerts, dashboard, websocket
from app.api.websocket import broadcast_transaction
from app.services.rules_engine import seed_rules
from app.services.simulator import run_simulator

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    await seed_rules()
    # Start simulator in background
    asyncio.create_task(run_simulator(broadcast_transaction))
    yield

app = FastAPI(
    title="iGaming Anti-Fraud Platform",
    description="Real-time fraud detection for iGaming operators",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(transactions.router)
app.include_router(players.router)
app.include_router(rules.router)
app.include_router(alerts.router)
app.include_router(websocket.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "igaming-antifraud-platform"}
