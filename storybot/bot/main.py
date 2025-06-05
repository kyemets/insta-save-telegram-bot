from __future__ import annotations

import asyncio
import logging
import threading

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from storybot.healthcheck import start_health_server
from .config import settings
from .handlers import story, auto, common
from .services.scheduler import start_scheduler

log = logging.getLogger(__name__)


async def _on_startup() -> None:
    start_scheduler()
    log.info("Scheduler started inside startup hook")


async def _run() -> None:
    # Запускаем health-check сервер в отдельном потоке
    threading.Thread(target=start_health_server, daemon=True).start()

    # Запускаем Telegram-бота
    bot = Bot(
        token=settings.tg_token,
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    dp = Dispatcher()

    # Порядок регистрации критичен
    dp.include_router(story.router)
    dp.include_router(auto.router)
    dp.include_router(common.router)

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
