"""
storybot.bot.dao.settings_dao
─────────────────────────────
MongoDB access layer for user-specific auto-check settings.
"""

from __future__ import annotations        

import logging
from datetime import datetime
from typing import Any, Dict

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pydantic import BaseModel, Field

from ..config import settings

log = logging.getLogger(__name__)


_motor: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient:
    """Singleton Motor client bound to the current running event-loop."""
    global _motor  # noqa: PLW0603
    if _motor is None:
        _motor = AsyncIOMotorClient(settings.mongo_dsn, uuidRepresentation="standard")
        log.info("Mongo client initialised for %s", _motor.address)
    return _motor


def _get_collection() -> AsyncIOMotorCollection:
    """Return the settings collection inside the DB named in the DSN."""
    db = _get_client().get_default_database() 
    coll = db.settings


    if not hasattr(coll, "_index_created"):
        coll.create_index("target_username", sparse=True)
        setattr(coll, "_index_created", True)

    return coll




class SettingsModel(BaseModel):
    """Document schema for the `settings` collection."""

    user_id: int = Field(..., alias="_id")  
    auto_enabled: bool = False
    interval: int = 3                   
    target_username: str | None = None

    model_config = {
        "populate_by_name": True, 
        "from_attributes": True,
    }




class SettingsDAO:
    """Async helpers for CRUD on `settings`."""

    @classmethod
    async def get(cls, user_id: int) -> SettingsModel:
        doc: Dict[str, Any] | None = await _get_collection().find_one({"_id": user_id})
        if doc is None:  
            doc = {"_id": user_id}
        return SettingsModel.model_validate(doc)

    @classmethod
    async def upsert(cls, model: SettingsModel) -> None:
        coll = _get_collection()
        payload: Dict[str, Any] = model.model_dump(by_alias=True, exclude_none=True)

        log.info("UPSERT ► %s", payload)          
        result = await coll.update_one(
            {"_id": model.user_id},
            {"$set": payload},
            upsert=True,
        )
        log.info(                            
            "UPSERT ◄ matched=%s  modified=%s  upserted_id=%s",
            result.matched_count,
            result.modified_count,
            result.upserted_id,
        )

    @classmethod
    async def add_search(cls, user_id: int, username: str, sent: int) -> None:
        """Append a search event (keeps full history)."""
        record = {
            "username": username.lower(),
            "ts": datetime.utcnow(),
            "sent": sent,
        }
        await _get_collection().update_one(
            {"_id": user_id},
            {"$push": {"searches": record}},
            upsert=True,
        )
