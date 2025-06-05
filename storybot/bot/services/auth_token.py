"""
storybot.bot.services.auth_token
────────────────────────────────
Builds the auth token required by anonstories.com.

The algorithm reproduces the JavaScript logic seen on their site:
    raw  = f"-1::{username_lowered}::{SHARED_SECRET}"
    b64  = base64-encode(raw)
    safe = b64.replace('+', '.').replace('/', '_').replace('=', '-')
"""

import base64
import logging

SHARED_SECRET = (
    "LTE6Om11cmllbGdhbGxlOjpySlAydEJSS2Y2a3RiUnFQVUJ0UkU5a2xnQldiN2Q-"
)

log = logging.getLogger(__name__)


class AuthTokenManager:
    """Single static helper used by story handler & background tasks."""

    @staticmethod
    def build_auth_token(username: str) -> str:
        """
        Convert *username* into anonstories’ auth string.

        Raises
        ------
        ValueError
            If username is empty / only whitespace.
        """
        if not username or not username.strip():
            raise ValueError("username must not be empty")

        uname = username.strip().lower()
        raw = f"-1::{uname}::{SHARED_SECRET}"
        b64 = base64.b64encode(raw.encode()).decode()

        # url-safe replacements
        token = b64.replace("+", ".").replace("/", "_").replace("=", "-")
        log.debug("auth token generated for %s", uname)
        return token
