import asyncio
import base64
import json
import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urlparse

import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.exceptions import TelegramAPIError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from tg_token import TOKEN

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


API_ENDPOINT = 'https://anonstories.com/api/v1/story'
SHARED_SECRET = "LTE6Om11cmllbGdhbGxlOjpySlAydEJSS2Y2a3RiUnFQVUJ0UkU5a2xnQldiN2Q-"
SETTINGS_PATH = Path('user_settings.json')
MAX_RETRIES = 10
POLLING_DELAY = 3
BROWSER_TIMEOUT = 30
API_TIMEOUT = 30


@dataclass
class UserSettings:
    """user settings data class"""
    auto_enabled: bool = False
    interval: int = 3
    last_check: Optional[str] = None
    target_username: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSettings':
        """Create UserSettings from dictionary."""
        return cls(
            auto_enabled=data.get('auto_enabled', False),
            interval=data.get('interval', 3),
            last_check=data.get('last_check'),
            target_username=data.get('target_username')
        )


@dataclass
class StoryData:
    """story data structure"""
    media_type: str
    source: str
    timestamp: Optional[str] = None


@dataclass
class UserInfo:
    """user info data structure"""
    username: str
    full_name: Optional[str]
    profile_pic_url: str
    posts: int
    followers: int
    following: int
    is_private: bool


class SettingsManager:
    """manages user settings with proper error handling"""
    
    def __init__(self, settings_path: Path):
        self.settings_path = settings_path
        self._ensure_settings_file()
    
    def _ensure_settings_file(self) -> None:
        """Ensure settings file exists."""
        if not self.settings_path.exists():
            self.settings_path.write_text('{}')
    
    def get_all_settings(self) -> Dict[str, Dict]:
        """get all user settings"""
        try:
            return json.loads(self.settings_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error reading settings: {e}")
            return {}
    
    def get_user_settings(self, user_id: int) -> UserSettings:
        """get settings for specific user"""
        all_settings = self.get_all_settings()
        user_data = all_settings.get(str(user_id), {})
        return UserSettings.from_dict(user_data)
    
    def update_user_setting(self, user_id: int, **kwargs) -> None:
        """update user settings"""
        all_settings = self.get_all_settings()
        user_id_str = str(user_id)
        
        if user_id_str not in all_settings:
            all_settings[user_id_str] = {}
        
        all_settings[user_id_str].update(kwargs)
        
        try:
            self.settings_path.write_text(json.dumps(all_settings, indent=2))
        except Exception as e:
            logger.error(f"Error saving settings: {e}")


class AuthTokenManager:
    """manages authentication token generation"""
    
    @staticmethod
    def build_auth_token(username: str) -> str:
        """build authentication token for username"""
        if not username or not username.strip():
            raise ValueError("Username cannot be empty")
        
        username = username.strip().lower()
        raw = f"-1::{username}::{SHARED_SECRET}"
        b64 = base64.b64encode(raw.encode()).decode()
        token = b64.replace('+', '.').replace('/', '_').replace('=', '-')
        
        logger.info(f"Generated auth token for {username}")
        return token


class URLDecoder:
    """handles URL decoding operations"""
    
    @staticmethod
    def decode_embed_url(embed_url: str) -> str:
        """decode embedded URL"""
        if not embed_url:
            return ""
        
        try:
            parsed = urlparse(embed_url)
            if parsed.scheme in ('http', 'https'):
                return embed_url
            
            b64_part = embed_url.split("/")[-1]
            b64_part = b64_part.replace('-', '=').replace('_', '/').replace('.', '+')
            
            missing_padding = len(b64_part) % 4
            if missing_padding:
                b64_part += '=' * (4 - missing_padding)
            
            decoded = base64.b64decode(b64_part).decode('utf-8')
            
            if decoded.startswith(('http://', 'https://')):
                return decoded
            
        except Exception as e:
            logger.warning(f"URL decoding error for {embed_url}: {e}")
        
        return embed_url


class BrowserManager:
    """manages browser operations with proper resource cleanup"""
    
    def __init__(self):
        self.options = self._get_chrome_options()
    
    def _get_chrome_options(self) -> Options:
        """get Chrome options for headless browsing"""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        return options
    
    async def trigger_browser_async(self, username: str) -> None:
        """trigger browser in async context"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._trigger_browser_sync, username)
    
    def _trigger_browser_sync(self, username: str) -> None:
        """synchronous browser trigger"""
        logger.info(f"Launching browser for @{username}")
        
        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=self.options)
            
            try:
                url = f"https://anonstories.com/view/{username}"
                driver.get(url)
                
                WebDriverWait(driver, BROWSER_TIMEOUT).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                logger.info(f"Page loaded successfully: {url}")
                
            finally:
                driver.quit()
                
        except Exception as e:
            logger.error(f"Browser error for {username}: {e}")
            raise


class APIClient:
    """handles API communication with proper error handling and retries"""
    
    def __init__(self):
        self.session_timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
    
    @asynccontextmanager
    async def _get_session(self):
        """get aiohttp session with proper configuration"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession(
            headers=headers, 
            timeout=self.session_timeout
        ) as session:
            yield session
    
    async def fetch_story_data(self, auth_token: str) -> Dict[str, Any]:
        """fetch story data from API"""
        try:
            async with self._get_session() as session:
                data = {"auth": auth_token}
                
                async with session.post(API_ENDPOINT, data=data) as response:
                    logger.info(f"API response status: {response.status}")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API error ({response.status}): {error_text[:300]}")
                        return {}
                    
                    result = await response.json()
                    logger.info(f"API returned data with keys: {list(result.keys())}")
                    return result
                    
        except asyncio.TimeoutError:
            logger.error("API request timed out")
            return {}
        except Exception as e:
            logger.error(f"API request error: {e}")
            return {}
    
    async def wait_for_stories(self, auth_token: str, max_retries: int = MAX_RETRIES) -> Optional[Dict[str, Any]]:
        """wait for stories with exponential backoff"""
        for attempt in range(max_retries):
            delay = min(POLLING_DELAY * (2 ** (attempt // 3)), 30)  # Exponential backoff with cap
            
            logger.info(f"Polling API... attempt {attempt + 1}/{max_retries} (delay: {delay}s)")
            await asyncio.sleep(delay)
            
            data = await self.fetch_story_data(auth_token)
            
            if data.get("user_info") and data.get("stories"):
                logger.info("✅ Stories loaded successfully")
                return data
            elif data.get("user_info") and not data.get("stories"):
                logger.info("User found but no stories available")
                return data
        
        logger.warning("❌ Timed out waiting for stories")
        return None


class StoryBot:    
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.dp = Dispatcher(self.bot)
        self.dp.middleware.setup(LoggingMiddleware())
        
        self.settings_manager = SettingsManager(SETTINGS_PATH)
        self.browser_manager = BrowserManager()
        self.api_client = APIClient()
        self.url_decoder = URLDecoder()
        
        self._setup_handlers()
    
    def _setup_handlers(self) -> None:
        self.dp.register_message_handler(self.cmd_start, commands=['start'])
        self.dp.register_message_handler(self.cmd_story, commands=['story'])
        self.dp.register_message_handler(self.cmd_help, commands=['help'])
        self.dp.register_message_handler(self.handle_auto_controls, commands=['auto_on', 'auto_off', 'status'])
        self.dp.register_callback_query_handler(self.set_interval, lambda c: c.data.startswith("interval:"))
        self.dp.register_message_handler(self.handle_username, lambda msg: not msg.text.startswith("/"))
    
    async def cmd_start(self, message: types.Message) -> None:
        """Handle /start command"""
        welcome_text = (
            "👋 *Welcome to Instagram Stories Bot!*\n\n"
            "🔍 Send me an Instagram username to view their stories anonymously.\n"
            "⚙️ Use /help to see all available commands.\n\n"
            "Just type a username to get started!"
        )
        await message.answer(welcome_text, parse_mode="Markdown")
    
    async def cmd_story(self, message: types.Message) -> None:
        """handle /story command"""
        await message.answer("✍️ Enter the Instagram username (without @):")
    
    async def cmd_help(self, message: types.Message) -> None:
        """handle /help command"""
        help_text = (
            "📖 *Available Commands:*\n\n"
            "🔍 `/story` - Request stories for a username\n"
            "⚙️ `/auto_on` - Enable automatic story checking\n"
            "🚫 `/auto_off` - Disable automatic story checking\n"
            "📊 `/status` - Check your current settings\n"
            "❓ `/help` - Show this help message\n\n"
            "💡 *Tips:*\n"
            "• Just send a username without any command\n"
            "• Usernames should not include the @ symbol\n"
            "• Private accounts cannot be accessed"
        )
        await message.answer(help_text, parse_mode="Markdown")
    
    async def handle_auto_controls(self, message: types.Message) -> None:
        """handle auto control commands"""
        user_id = message.from_user.id
        command = message.text.split()[0]
        
        if command == "/auto_on":
            self.settings_manager.update_user_setting(user_id, auto_enabled=True)
            await message.answer("✅ Auto story checking is now *enabled*.", parse_mode="Markdown")
        
        elif command == "/auto_off":
            self.settings_manager.update_user_setting(user_id, auto_enabled=False)
            await message.answer("🚫 Auto story checking is now *disabled*.", parse_mode="Markdown")
        
        elif command == "/status":
            settings = self.settings_manager.get_user_settings(user_id)
            status = "ON ✅" if settings.auto_enabled else "OFF ❌"
            target = settings.target_username or "None"
            
            status_text = (
                f"⚙️ *Your Settings:*\n"
                f"🔄 Auto checking: *{status}*\n"
                f"⏱ Interval: *{settings.interval}h*\n"
                f"👤 Target: *{target}*"
            )
            await message.answer(status_text, parse_mode="Markdown")
    
    async def set_interval(self, call: types.CallbackQuery) -> None:
        """handle interval setting callback"""
        try:
            interval = int(call.data.split(":")[1])
            self.settings_manager.update_user_setting(call.from_user.id, interval=interval)
            await call.answer(f"✅ Interval set to {interval}h")
            
            await call.message.edit_text(
                f"⚙️ Auto-check interval set to *{interval} hours*.",
                parse_mode="Markdown"
            )
        except (ValueError, IndexError) as e:
            logger.error(f"Error setting interval: {e}")
            await call.answer("❌ Error setting interval")
    
    async def handle_username(self, message: types.Message) -> None:
        """handle username input"""
        username = self._validate_username(message.text)
        if not username:
            await message.answer("⚠️ Please provide a valid Instagram username.")
            return
        
        self.settings_manager.update_user_setting(
            message.from_user.id, 
            target_username=username
        )
        
        await self._process_username(message, username)
    
    def _validate_username(self, text: str) -> Optional[str]:
        """validate and clean username"""
        if not text or not text.strip():
            return None
        
        username = text.strip().replace("@", "").lower()
        
        if not username.replace("_", "").replace(".", "").isalnum():
            return None
        
        if len(username) < 1 or len(username) > 30:
            return None
        
        return username
    
    async def _process_username(self, message: types.Message, username: str) -> None:
        """process username and fetch stories"""
        status_message = await message.answer(f"🔎 Looking up @{username}...")
        
        try:
            auth_token = AuthTokenManager.build_auth_token(username)
            
            await status_message.edit_text("🌐 Launching browser...")
            await self.browser_manager.trigger_browser_async(username)
            
      
            await status_message.edit_text("⌛ Fetching story data...")
            data = await self.api_client.wait_for_stories(auth_token)
            
            if not data:
                await status_message.edit_text("❌ No data found. User might be private or non-existent.")
                return
            
            await self._send_stories(message, data, status_message)
            
        except Exception as e:
            logger.error(f"Error processing username {username}: {e}")
            await status_message.edit_text(f"❌ Error occurred: {str(e)[:100]}")
    
    async def _send_stories(self, message: types.Message, data: Dict, status_message: types.Message) -> None:
        """send stories to user"""
        user_info = data.get("user_info", {})
        stories = data.get("stories", [])
        
        if user_info.get("is_private"):
            await status_message.edit_text("🔒 This account is private and cannot be accessed.")
            return
        
        await self._send_profile_info(message, user_info)
        
        if not stories:
            await status_message.edit_text("ℹ️ No stories available for this user.")
            return
        
        await status_message.edit_text(f"📲 Found *{len(stories)}* stories. Sending...", parse_mode="Markdown")
        
        sent_count = 0
        for idx, story in enumerate(stories, 1):
            try:
                await self._send_single_story(message, story, idx, len(stories))
                sent_count += 1
                
                if idx < len(stories):
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Error sending story {idx}: {e}")
        
        if sent_count > 0:
            await self._show_interval_selection(message)
        
        await status_message.delete()
    
    async def _send_profile_info(self, message: types.Message, user_info: Dict) -> None:
        """send profile information"""
        profile_pic = self.url_decoder.decode_embed_url(user_info.get("profile_pic_url", ""))
        
        summary = (
            f"👤 *Instagram Profile*\n"
            f"• Username: @{user_info.get('username', 'N/A')}\n"
            f"• Name: {user_info.get('full_name') or '—'}\n"
            f"• Posts: {user_info.get('posts', 0):,}\n"
            f"• Followers: {user_info.get('followers', 0):,}\n"
            f"• Following: {user_info.get('following', 0):,}"
        )
        
        try:
            if profile_pic and profile_pic.startswith(('http://', 'https://')):
                await self.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=profile_pic,
                    caption=summary,
                    parse_mode="Markdown"
                )
            else:
                await message.answer(summary, parse_mode="Markdown")
        except TelegramAPIError as e:
            logger.warning(f"Failed to send profile picture: {e}")
            await message.answer(summary, parse_mode="Markdown")
    
    async def _send_single_story(self, message: types.Message, story: Dict, idx: int, total: int) -> None:
        """send a single story"""
        media_type = story.get("media_type")
        source = self.url_decoder.decode_embed_url(story.get("source", ""))
        caption = f"📖 Story {idx}/{total}"
        
        if not source or not source.startswith(('http://', 'https://')):
            logger.warning(f"Invalid source URL for story {idx}: {source}")
            return
        
        try:
            if media_type == "image":
                await self.bot.send_photo(
                    chat_id=message.chat.id,
                    photo=source,
                    caption=caption
                )
            elif media_type == "video":
                await self.bot.send_video(
                    chat_id=message.chat.id,
                    video=source,
                    caption=caption
                )
            else:
                logger.warning(f"Unknown media type: {media_type}")
        
        except TelegramAPIError as e:
            logger.error(f"Telegram API error sending story {idx}: {e}")
            raise
    
    async def _show_interval_selection(self, message: types.Message) -> None:
        """show interval selection buttons"""
        keyboard = types.InlineKeyboardMarkup(row_width=3)
        buttons = [
            types.InlineKeyboardButton("1h", callback_data="interval:1"),
            types.InlineKeyboardButton("3h", callback_data="interval:3"),
            types.InlineKeyboardButton("6h", callback_data="interval:6"),
            types.InlineKeyboardButton("8h", callback_data="interval:8"),
            types.InlineKeyboardButton("12h", callback_data="interval:12")
        ]
        keyboard.add(*buttons)
        
        await message.answer(
            "⚙️ Choose auto-check interval for this user:",
            reply_markup=keyboard
        )
    
    def run(self) -> None:
        """start the bot"""
        logger.info("🚀 Bot starting...")
        try:
            executor.start_polling(self.dp, skip_updates=True)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise


def main():
    """main entry point"""
    if not TOKEN:
        logger.error("TOKEN not found. Please check tg_token.py")
        return
    
    bot = StoryBot(TOKEN)
    bot.run()


if __name__ == "__main__":
    main()
