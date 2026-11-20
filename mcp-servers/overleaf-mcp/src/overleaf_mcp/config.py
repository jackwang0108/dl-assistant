"""Explicit instance, proxy and local storage configuration."""

import os
from pathlib import Path

from .models import OverleafError, origin


class Config:
    def __init__(self, home=None, base_url=None, proxy=None, cdn_origins=None):
        self.base_url = (
            base_url or os.getenv("OVERLEAF_BASE_URL", "https://www.overleaf.com")
        ).rstrip("/")
        self.origin = origin(self.base_url)
        self.home = (
            Path(home or os.getenv("OVERLEAF_MCP_HOME", Path.home() / ".local/share/overleaf-mcp"))
            .expanduser()
            .resolve()
        )
        self.credentials_path = Path(
            os.getenv("OVERLEAF_CREDENTIALS_PATH", self.home / "auth-v2.json")
        ).expanduser()
        self.proxy = proxy or os.getenv("OVERLEAF_PROXY_URL") or None
        self.compile_timeout = float(os.getenv("OVERLEAF_COMPILE_TIMEOUT", "180"))
        if not 1 <= self.compile_timeout <= 600:
            raise OverleafError("INVALID_CONFIG", "Compile timeout must be 1–600 seconds")
        defaults = "https://compiles.overleaf.com,https://compiles.overleafusercontent.com"
        values = (
            cdn_origins
            if cdn_origins is not None
            else os.getenv("OVERLEAF_CDN_ORIGINS", defaults).split(",")
        )
        self.cdn_origins = {origin(value.strip()) for value in values if value.strip()}
        self.cdn_origins.add(self.origin)
