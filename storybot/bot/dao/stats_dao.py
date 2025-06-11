"""
Append-only statistics DAO.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel, Field

from .settings_dao import _get_client        
import logging

log = logging.getLogger(__name__)




def _get_collection() -> AsyncIOMotorCollection:
    """Lazy access to the stats collection."""
    coll = _get_client().get_default_database().stats
    if not hasattr(coll, "_index_created"):
        coll.create_index(
            [("user_id", 1), ("date", 1), ("target_username", 1)]
        )
        coll.create_index("ts")
        setattr(coll, "_index_created", True)
        log.debug("stats indexes created")
    return coll



class StatsRecord(BaseModel):
    user_id: int
    target_username: str
    date: str = Field(default_factory=lambda: date.today().isoformat())
    ts: datetime = Field(default_factory=datetime.utcnow)
    fetched: int = 1
    sent: int = 0



class StatsDAO:
    """Append-only event logger."""

    @classmethod
    async def add(cls, user_id: int, username: str, sent: int) -> None:
        rec: Dict[str, Any] = StatsRecord(
            user_id=user_id,
            target_username=username.lower(),
            sent=sent,
        ).model_dump()
        await _get_collection().insert_one(rec)
