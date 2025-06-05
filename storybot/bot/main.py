from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from .config import settings
from .handlers import story, auto, common        # ← reorder import list (optional)
from .services.scheduler import start_scheduler

log = logging.getLogger(__name__)


async def _on_startup() -> None:
    start_scheduler()
    log.info("Scheduler started inside startup hook")


async def _run() -> None:
    bot = Bot(
        token=settings.tg_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )

    dp = Dispatcher()

    # REGISTER THE ROUTERS IN THIS ORDER  ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓
    dp.include_router(story.router)   # /story (must be checked first)
    dp.include_router(auto.router)    # /auto_on, /auto_off, callbacks
    dp.include_router(common.router)  # /start, /help, fallback “unknown command”
    # ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑ END ORDER

    dp.startup.register(_on_startup)
    await dp.start_polling(bot)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(_run())


if __name__ == "__main__":
    main()
