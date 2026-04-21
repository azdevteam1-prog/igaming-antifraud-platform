import asyncio
import random
import uuid
from datetime import datetime
from faker import Faker
from app.core.database import AsyncSessionLocal
from app.models.player import Player
from app.models.transaction import Transaction
from app.models.device import DeviceSession, EntityLink
from app.services.rules_engine import evaluate_rules
from app.services.risk_scorer import compute_risk_score
from sqlalchemy import select
import json

fake = Faker()

COUNTRIES = ["LV", "DE", "GB", "EE", "LT", "FI", "SE", "PL", "UA", "CY"]
PAYMENT_METHODS = ["card", "crypto", "bank", "ewallet", "prepaid"]
HIGH_RISK_COUNTRIES = ["CY", "UA"]

# Shared attributes pool for multi-account simulation
SHARED_IPS = [fake.ipv4() for _ in range(15)]
SHARED_DEVICES = [str(uuid.uuid4())[:8] for _ in range(15)]
SHARED_PAYMENTS = [str(uuid.uuid4())[:12] for _ in range(20)]

async def seed_players(n=50):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Player).limit(1))
        if result.scalar():
            return  # already seeded
        players = []
        for _ in range(n):
            is_risky = random.random() < 0.25
            country = random.choice(HIGH_RISK_COUNTRIES if is_risky else COUNTRIES)
            ip = random.choice(SHARED_IPS) if is_risky else fake.ipv4()
            device = random.choice(SHARED_DEVICES) if is_risky else str(uuid.uuid4())[:8]
            p = Player(
                id=str(uuid.uuid4()),
                username=fake.user_name() + str(random.randint(10, 999)),
                email=fake.email(),
                phone=fake.phone_number()[:20],
                country=country,
                kyc_verified=random.random() > 0.3,
                risk_score=round(random.uniform(0.6, 0.95) if is_risky else random.uniform(0.0, 0.4), 3),
                risk_label="High" if is_risky else "Low",
                pep_flag=random.random() < 0.04,
                sanctions_flag=random.random() < 0.01,
                registration_ip=ip,
                last_ip=ip,
                device_fingerprint=device,
                total_deposits=round(random.uniform(100, 20000), 2),
                total_withdrawals=round(random.uniform(50, 18000), 2),
            )
            players.append(p)
            db.add(p)
        await db.commit()
        # seed device sessions and links
        await seed_links(players)

async def seed_links(players):
    async with AsyncSessionLocal() as db:
        for p in players:
            ds = DeviceSession(
                id=str(uuid.uuid4()),
                player_id=p.id,
                fingerprint=p.device_fingerprint or str(uuid.uuid4())[:8],
                ip_address=p.last_ip or fake.ipv4(),
                country=p.country,
            )
            db.add(ds)
        await db.commit()

async def generate_transaction():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Player).order_by(Player.id))
        players = result.scalars().all()
        if not players:
            return None
        player = random.choice(players)
        tx_type = random.choices(["deposit", "withdrawal"], weights=[60, 40])[0]
        amount = round(random.uniform(10, 5000), 2)
        payment_method = random.choice(PAYMENT_METHODS)
        ip = random.choice(SHARED_IPS) if player.risk_label in ["High", "Critical"] else fake.ipv4()
        device = player.device_fingerprint or str(uuid.uuid4())[:8]
        geo_mismatch = ip != player.registration_ip and random.random() < 0.3

        tx = Transaction(
            id=str(uuid.uuid4()),
            player_id=player.id,
            tx_type=tx_type,
            amount=amount,
            payment_method=payment_method,
            payment_token=random.choice(SHARED_PAYMENTS) if player.risk_label in ["High", "Critical"] else str(uuid.uuid4())[:12],
            status="pending",
            ip_address=ip,
            country=player.country,
            device_fingerprint=device,
            geo_mismatch_flag=geo_mismatch,
        )

        # evaluate rules
        hits = await evaluate_rules(tx, player, db)
        tx.rule_hits = json.dumps(hits)

        # compute risk
        score, label = await compute_risk_score(tx, player, hits)
        tx.risk_score = score
        tx.risk_label = label

        # decide status
        if score > 0.8:
            tx.status = "flagged"
        elif score > 0.6:
            tx.status = "review"
        elif score > 0.9:
            tx.status = "hold"
        else:
            tx.status = "approved"

        db.add(tx)

        # update player totals
        if tx_type == "deposit":
            player.total_deposits = (player.total_deposits or 0) + amount
        else:
            player.total_withdrawals = (player.total_withdrawals or 0) + amount
        player.last_ip = ip

        await db.commit()
        await db.refresh(tx)
        return tx

async def run_simulator(broadcast_fn):
    await seed_players(50)
    while True:
        tx = await generate_transaction()
        if tx:
            await broadcast_fn(tx)
        await asyncio.sleep(random.uniform(0.8, 2.5))
