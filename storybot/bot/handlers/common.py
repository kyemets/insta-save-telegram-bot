"""
storybot.bot.handlers.common
────────────────────────────
Generic /start and /help commands plus a fallback “unknown command” handler.
"""

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def cmd_start(msg: Message) -> None:
    await msg.answer(
        "👋 Hi!\nSend /story to fetch Instagram stories "
        "or type a username directly."
    )


@router.message(Command("help"))
async def cmd_help(msg: Message) -> None:
    await msg.answer(
        "📖 <b>Available commands</b>\n"
        "/story – request stories for a user\n"
        "/auto_on – enable periodic checks\n"
        "/auto_off – disable periodic checks\n"
        "/help – this message",
        parse_mode="HTML",
    )


# Fallback: any other slash-command that was not matched above
@router.message(F.text.startswith("/"))
async def unknown_command(msg: Message) -> None:
    await msg.answer("❓ Unknown command. Use /help for the list.")
