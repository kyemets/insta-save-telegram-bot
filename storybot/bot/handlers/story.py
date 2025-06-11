"""
storybot.bot.handlers.story
───────────────────────────
Fetch and deliver Instagram stories on demand (/story or plain username)
and from APScheduler (auto-check).

Public
------
fetch_and_push_stories(user_id: int)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from aiogram import Router, F, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message

from ..config import settings
from ..dao.settings_dao import SettingsDAO
from ..dao.stats_dao import StatsDAO

from ..services.api_client import APIClient
from ..services.auth_token import AuthTokenManager
from ..services.browser import BrowserManager
from ..services.url_decoder import URLDecoder

log = logging.getLogger(__name__)
router = Router()



async def fetch_and_push_stories(user_id: int) -> None:
    """Background task executed by APScheduler."""
    profile = await SettingsDAO.get(user_id)
    if not profile.target_username:
        log.info("auto-job skipped: user %s has no target_username", user_id)
        return

    bot = Bot(
        token=settings.tg_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    status = await bot.send_message(
        user_id,
        f"🔄 Auto-check @{profile.target_username} …",
    )

    class _PseudoMsg:
        """Tiny wrapper so we can reuse _process_username logic."""
        chat = status.chat
        from_user = status.from_user

        async def answer(_, text: str, **kw):
            await bot.send_message(user_id, text, **kw)

    await _process_username(_PseudoMsg(), status, profile.target_username)




@router.message(Command("story"))
async def cmd_story(msg: Message) -> None:
    await msg.answer("✍️ Enter an Instagram username (without @):")


@router.message(~F.text.startswith("/"))
async def handle_username(msg: Message) -> None:
    username = _validate_username(msg.text)
    if not username:
        await msg.answer("⚠️ Please provide a valid username.")
        return

    profile = await SettingsDAO.get(msg.from_user.id)
    profile.target_username = username
    await SettingsDAO.upsert(profile)

    status = await msg.answer(f"🔎 Looking up @{username} …")
    success = await _process_username(msg, status, username)

    if success:
        from .auto import _interval_keyboard 
        await msg.answer(
            "⚙️ Choose an auto-check interval:",
            reply_markup=_interval_keyboard(),
        )



async def _process_username(
    requester: Message | Any,
    status: Message,
    username: str,
) -> bool:
    """Shared routine; returns *True* if at least one story was sent."""
    try:
        auth_token = AuthTokenManager.build_auth_token(username)

        await status.edit_text("🌐 Launching headless browser …")
        await BrowserManager().trigger_browser_async(username)

        await status.edit_text("⌛ Querying anonstories API …")
        data = await APIClient().wait_for_stories(auth_token)
        if not data:
            await status.edit_text(
                "❌ Nothing found (private or non-existent account)."
            )
            return False

        await _send_profile_info(requester, data["user_info"])

        stories = data["stories"]
        if not stories:
            await status.edit_text("ℹ️ The account currently has no active stories.")
            return False

        await status.edit_text(f"📲 Found {len(stories)} stories — sending …")
        for idx, story in enumerate(stories, 1):
            await _send_single_story(requester, story, idx, len(stories))
            if idx < len(stories):
                await asyncio.sleep(0.4)
        await SettingsDAO.add_search(
			user_id=requester.from_user.id,
			username=username,
			sent=len(stories),
		)
        

        await status.delete()
        return True

    except Exception as exc:  # noqa: BL
        log.exception("Failed to fetch %s: %s", username, exc)
        await status.edit_text("💥 An error occurred while fetching stories.")
        return False


async def _send_profile_info(msg: Message | Any, info: Dict[str, Any]) -> None:
    avatar = URLDecoder.decode_embed_url(info.get("profile_pic_url", ""))

    caption = (
        "👤 <b>Instagram profile</b>\n"
        f"• @{info['username']}\n"
        f"• Name: {info.get('full_name') or '—'}\n"
        f"• Posts: {info['posts']:,}\n"
        f"• Followers: {info['followers']:,}\n"
        f"• Following: {info['following']:,}"
    )

    try:
        if avatar.startswith(("http://", "https://")):
            await msg.answer_photo(avatar, caption=caption)
        else:
            await msg.answer(caption)
    except Exception as exc:  # noqa: BLE001
        log.warning("send_profile_info: %s", exc)
        await msg.answer(caption)


async def _send_single_story(
    msg: Message | Any,
    story: Dict[str, Any],
    idx: int,
    total: int,
) -> None:
    src = URLDecoder.decode_embed_url(story["source"])
    caption = f"📖 Story {idx}/{total}"

    try:
        if story["media_type"] == "image":
            await msg.answer_photo(src, caption=caption)
        else:
            await msg.answer_video(src, caption=caption)
    except Exception as exc:  # noqa: BLE001
        log.warning("Story %s/%s failed: %s", idx, total, exc)


def _validate_username(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    name = raw.strip().lstrip("@").lower()
    ok = 1 <= len(name) <= 30 and name.replace("_", "").replace(".", "").isalnum()
    return name if ok else None
