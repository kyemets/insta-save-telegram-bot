"""
storybot.bot.services.url_decoder
─────────────────────────────────
Convert anonstories “embed” URLs (base64-url-safe strings) into real
http/https links that Telegram can deliver.  If the input is already a
regular link, it is returned untouched.
"""

from __future__ import annotations

import base64
import logging
from urllib.parse import urlparse

log = logging.getLogger(__name__)


class URLDecoder:
    """Static helper used by the story handler when sending media."""

    @staticmethod
    def decode_embed_url(url: str | None) -> str:
        """
        Parameters
        ----------
        url : str | None
            Value coming from anonstories JSON.

        Returns
        -------
        str
            Clean media URL or the original string if decoding fails.
        """
        if not url:
            return ""

        # Already a normal link?  Just return it.
        if urlparse(url).scheme in ("http", "https"):
            return url

        try:
            # Last path segment looks like a base64-url-safe token.
            token = url.rsplit("/", 1)[-1]
            token = token.replace("-", "=").replace("_", "/").replace(".", "+")
            if len(token) % 4:
                token += "=" * (4 - len(token) % 4)

            decoded = base64.b64decode(token).decode()
            if decoded.startswith(("http://", "https://")):
                return decoded
        except Exception as exc:  # pylint: disable=broad-except
            log.debug("URL decoding failed for %s: %s", url, exc)

        # Fallback: return whatever we got.
        return url
