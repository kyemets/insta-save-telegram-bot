"""
storybot.bot.services.browser
─────────────────────────────
Launches a headless Chrome session so that anonstories prepares JSON for us.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import undetected_chromedriver as uc

_BROWSERS_SEMAPHORE = asyncio.Semaphore(3)
BROWSER_TIMEOUT = 30  # seconds

log = logging.getLogger(__name__)


class BrowserManager:
    """Spawn short-lived headless Chrome sessions."""

    def __init__(self) -> None:
        self._options = uc.ChromeOptions()
        self._options.add_argument("--headless=new")
        self._options.add_argument("--disable-gpu")
        self._options.add_argument("--no-sandbox")
        self._options.add_argument("--disable-dev-shm-usage")
        self._options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        )
        
        chrome_binary = os.getenv("CHROME_BINARY")
        if chrome_binary:
            self._options.binary_location = chrome_binary

    async def trigger_browser_async(self, username: str) -> None:
        """Run _open_page in a thread-executor, limited by a semaphore."""
        loop = asyncio.get_running_loop()
        async with _BROWSERS_SEMAPHORE:
            await loop.run_in_executor(None, self._open_page, username)

    # internal -------------------------------------------------------------

    def _open_page(self, username: str) -> None:
        url = f"https://anonstories.com/view/{username}"
        log.debug("Headless Chrome → %s", url)

        driver = uc.Chrome(options=self._options)
        try:
            driver.set_page_load_timeout(BROWSER_TIMEOUT)
            driver.get(url)
            driver.find_element("tag name", "body")  # wait for <body>
            log.debug("Page loaded for %s", username)
        except Exception as exc:  # pylint: disable=broad-except
            log.warning("Browser error for %s: %s", username, exc)
        finally:
            driver.quit()
