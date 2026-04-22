from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import uuid

from app.core.database import engine, Base, AsyncSessionLocal
from app.core.redis_client import init_redis
from app.api import transactions, players, rules, alerts, dashboard, websocket
from app.api import auth
from app.api.websocket import broadcast_transaction
from app.services.rules_engine import seed_rules
from app.services.simulator import run_simulator


async def seed_admin():
    """Create default admin user on first startup if not exists."""
    from sqlalchemy import select
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if result.scalar():
            return  # already exists
        admin = User(
            id=str(uuid.uuid4()),
            username="admin",
            email="admin@antifraud.local",
            full_name="Platform Administrator",
            hashed_password=hash_password("admin123"),
            role=UserRole.admin,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print("[startup] Admin user created: admin / admin123")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await init_redis()
    await seed_rules()
    await seed_admin()
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

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(transactions.router)
app.include_router(players.router)
app.include_router(rules.router)
app.include_router(alerts.router)
app.include_router(websocket.router)
