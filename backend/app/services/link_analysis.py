from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.player import Player
from app.models.device import EntityLink, DeviceSession
from app.models.transaction import Transaction

async def get_player_graph(player_id: str, db: AsyncSession) -> dict:
    """Build a graph of all players linked to a given player via shared attributes."""
    # Get all links for this player
    result = await db.execute(
        select(EntityLink).where(
            (EntityLink.player_id_a == player_id) |
            (EntityLink.player_id_b == player_id)
        )
    )
    links = result.scalars().all()

    # Get the target player
    player_result = await db.execute(select(Player).where(Player.id == player_id))
    focus_player = player_result.scalar()
    if not focus_player:
        return {"nodes": [], "edges": []}

    # Collect linked player ids
    linked_ids = set()
    for lnk in links:
        linked_ids.add(lnk.player_id_a)
        linked_ids.add(lnk.player_id_b)
    linked_ids.discard(player_id)

    # Get all linked players
    nodes = [{"id": focus_player.id, "label": focus_player.username, "risk_label": focus_player.risk_label, "focus": True}]
    if linked_ids:
        res2 = await db.execute(select(Player).where(Player.id.in_(linked_ids)))
        for p in res2.scalars().all():
            nodes.append({"id": p.id, "label": p.username, "risk_label": p.risk_label, "focus": False})

    edges = []
    for lnk in links:
        edges.append({
            "source": lnk.player_id_a,
            "target": lnk.player_id_b,
            "link_type": lnk.link_type,
            "link_value": lnk.link_value,
        })

    return {"nodes": nodes, "edges": edges}

async def rebuild_entity_links(player: Player, db: AsyncSession):
    """Find and create entity links based on shared IP/device."""
    # shared IP
    if player.last_ip:
        ip_res = await db.execute(
            select(Player).where(
                Player.last_ip == player.last_ip,
                Player.id != player.id
            )
        )
        for other in ip_res.scalars().all():
            existing = await db.execute(
                select(EntityLink).where(
                    EntityLink.player_id_a == player.id,
                    EntityLink.player_id_b == other.id,
                    EntityLink.link_type == "ip"
                )
            )
            if not existing.scalar():
                db.add(EntityLink(
                    player_id_a=player.id,
                    player_id_b=other.id,
                    link_type="ip",
                    link_value=player.last_ip,
                ))
    # shared device
    if player.device_fingerprint:
        dev_res = await db.execute(
            select(Player).where(
                Player.device_fingerprint == player.device_fingerprint,
                Player.id != player.id
            )
        )
        for other in dev_res.scalars().all():
            existing = await db.execute(
                select(EntityLink).where(
                    EntityLink.player_id_a == player.id,
                    EntityLink.player_id_b == other.id,
                    EntityLink.link_type == "device"
                )
            )
            if not existing.scalar():
                db.add(EntityLink(
                    player_id_a=player.id,
                    player_id_b=other.id,
                    link_type="device",
                    link_value=player.device_fingerprint,
                ))
    await db.commit()
